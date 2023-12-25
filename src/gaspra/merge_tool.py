import argparse
import os

from rich.console import Console

from gaspra.merge import merge
from gaspra.changesets import escape, diff

TEST_CASE_DIRECTORY = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "test-cases",
    )
)

PROGRAM_NAME = os.path.basename(__file__)


def rich_escape(s):
    return s.replace("[", r"\[")


SCREEN_MARKUP = {
    "fragment": {
        "into": {
            "prefix": "[bright_green]",
            "suffix": "[/]",
        },
        "from": {
            "prefix": "[bright_red]",
            "suffix": "[/]",
        },
    },
    "line": {
        "into": {
            "prefix": lambda _: "[green]",
            "suffix": lambda _: "[/]",
        },
        "from": {
            "prefix": lambda _: "[red]",
            "suffix": lambda _: "[/]",
        },
    },
    "escape": rich_escape,
    "separator": "",
    "header": {
        "prefix": "<<<[bright_blue]",
        "suffix": "[/]>>>",
    },
}

GIT_MARKUP = {
    "fragment": {
        "into": {
            "prefix": "",
            "suffix": "",
        },
        "from": {
            "prefix": "",
            "suffix": "",
        },
    },
    "line": {
        "into": {
            "prefix": lambda s: f"<<<<<<< {s}\n",
            "suffix": lambda _: "",
        },
        "from": {
            "prefix": lambda _: "",
            "suffix": lambda s: f">>>>>>> {s}\n",
        },
    },
    "escape": lambda _: _,
    "separator": "=======\n",
    "header": {
        "prefix": "<<<",
        "suffix": ">>>",
    },
}


TEST_CASES = [
    "About.java",
    "ErrorMsg.java",
    "FlownetController.cpp",
    "Misc.java",
    "RearViewMirror.java",
    "ServerWin_2005.vcproj",  # This is the "real world" anchor moves example.
    "ServerWin_2005.vcproj.Reduced",
    "getCLIArgs.java",
    "chunks",
    "ReleaseNotes",
    "Bug_ReporterApp",
]

# 0 - Perfect.  No issues at all.
# 1 - Conflicts that are handled correctly.
# 2 - Conflicts that are handled correctly.
# 3 - Conflicts that are handled correctly.
# 4 - Technically correct, but SureMerge says they would have flagged it.
# 5 - Too long to tell. (This is the "real world" moves test.)
# 6 - Perfect (Shorter version of real world).
# 7 - Duplicated some code but it's arguably correct.
# 8 - Perfect but it had a weird split.
# 9 - Perfect, but it easily have gone otherwise.


EXCEPTIONS = {
    "chunks": ("chunks_1_0.c", "chunks_1_1.c", "chunks_1_2.c"),
    "ReleaseNotes": (
        "ReleaseNotes 9_4.html",
        "ReleaseNotes 9_4_1.html",
        "ReleaseNotes 9_4_2.html",
    ),
    "Bug_ReporterApp": (
        "Bug_ReporterApp_Parent.h",
        "Bug_ReporterApp_BranchA.h",
        "Bug_ReporterApp_BranchB.h",
    ),
}


def get_usage():
    return (
        f"{PROGRAM_NAME} test_case\nValid test cases are:\n\t"
        + "\n\t".join(TEST_CASES)
        + "\n"
    )


def show_header(print, header, markup={}):
    header_markup = markup.get("header", {})
    prefix = header_markup.get("prefix", "")
    suffix = header_markup.get("suffix", "")
    if header:
        print(f"\n{prefix}{escape(header)}{suffix}")


def show_changes(
    print, fragment_sequence, __name0__, __name1__, markup={}, header: str | None = None
):
    show_header(print, header, markup)

    fragment_markup = markup.get("fragment", {})

    def print_fragment(fragment, fragment_markup):
        prefix = fragment_markup["prefix"]
        suffix = fragment_markup["suffix"]
        print(f"{prefix}{escape(fragment)}{suffix}")

    for fragment in fragment_sequence:
        if isinstance(fragment, str):
            print(fragment)

        if isinstance(fragment, tuple):
            print_fragment(fragment[0], fragment_markup["into"])
            print_fragment(fragment[1], fragment_markup["from"])


def show_changes_line_oriented(
    print, fragment_sequence, name0, name1, markup={}, header: str | None = None
):
    show_header(print, header, markup)
    escape = markup.get("escape", lambda _: _)
    line_markup = markup.get("line", {})
    fragment_markup = markup.get("fragment", {})

    def print_line(line, name, line_markup):
        prefix = line_markup["prefix"](name)
        suffix = line_markup["suffix"](name)
        print(f"{prefix}{line}\n{suffix}")

    def markup_fragment(fragment, fragment_markup):
        prefix = fragment_markup["prefix"]
        suffix = fragment_markup["suffix"]
        return f"{prefix}{fragment}{suffix}"

    in_conflict = False
    partial_line_into = partial_line_from = ""
    any_line_into = any_line_from = False
    for fragment in fragment_sequence:
        if isinstance(fragment, str):
            lines = fragment.split("\n")
            if in_conflict:
                partial_line_into = partial_line_into + lines[0]
                partial_line_from = partial_line_from + lines[0]
                if len(lines) > 1:
                    print_line(
                        partial_line_into,
                        name0,
                        line_markup["into"],
                    )
                    print(markup["separator"])
                    print_line(
                        partial_line_from,
                        name1,
                        line_markup["from"],
                    )
                    partial_line_into = partial_line_from = ""
                    any_line_into = any_line_from = in_conflict = False
                    print(escape("\n".join(lines[1:-1])))
                    print("\n")
                    partial_line_into = lines[-1]
                    partial_line_from = lines[-1]
            else:
                print(escape(partial_line_into))
                # If not in a conflict, partial_line_0 should be
                # exactly the same as partial_line_1.
                print(escape("\n".join(lines[:-1])))
                partial_line_into = lines[-1]
                partial_line_from = lines[-1]

        if isinstance(fragment, tuple):
            in_conflict = True
            if fragment[0]:
                partial_line_into = partial_line_into + markup_fragment(
                    fragment[0], fragment_markup["into"]
                )
                any_line_into = True
            if fragment[1]:
                partial_line_from = partial_line_from + markup_fragment(
                    fragment[1], fragment_markup["from"]
                )
                any_line_from = True


def get_file_versions(test_case: str):
    if test_case in EXCEPTIONS:
        return EXCEPTIONS[test_case]

    parent = f"{test_case}.parent"
    branch0 = f"{test_case}.1st"
    branch1 = f"{test_case}.2nd"
    return parent, branch0, branch1


def get_arguments():
    parser = argparse.ArgumentParser(usage=get_usage())
    parser.add_argument("test_case")
    parser.add_argument(
        "-l",
        "--line-oriented",
        action="store_true",
        help="Show lines changed rather than fragments changed",
    )
    parser.add_argument(
        "-d", "--diff", action="store_true", help="Show diffs along with merge"
    )
    parser.add_argument(
        "-f",
        "--file-style",
        action="store_true",
        help="Mark up for files (git-style, no color)",
    )
    args = parser.parse_args()
    return args


def get_display_function(arguments):
    if arguments.line_oriented:
        return show_changes_line_oriented

    return show_changes


def get_markup_style(arguments):
    if arguments.file_style:
        return GIT_MARKUP
    else:
        return SCREEN_MARKUP


if __name__ == "__main__":
    console = Console(force_terminal=True, highlight=False)

    def console_print_function(s):
        console.print(s, end="")

    print_function = console_print_function

    arguments = get_arguments()
    display_function = get_display_function(arguments)
    markup = get_markup_style(arguments)

    parent, into_branch, from_branch = get_file_versions(arguments.test_case)

    def get_text(filename):
        with open(
            os.path.join(TEST_CASE_DIRECTORY, filename), "rt", encoding="ISO-8859-1"
        ) as f:
            data = f.read()
            return data

    parent_text = get_text(parent)
    into_text = get_text(into_branch)
    from_text = get_text(from_branch)

    into_changes = diff(parent_text, into_text)
    from_changes = diff(parent_text, from_text)

    print_fn = console.print

    if arguments.diff:
        display_function(
            print_function,
            into_changes,
            into_branch,
            parent,
            markup=markup,
            header=into_branch,
        )
        display_function(
            print_function,
            from_changes,
            from_branch,
            parent,
            markup=markup,
            header=from_branch,
        )

    merged = merge(parent_text, into_text, from_text)
    display_function(
        print_function,
        merged,
        into_branch,
        from_branch,
        markup=markup,
        header="Merged" if arguments.diff else None,
    )
