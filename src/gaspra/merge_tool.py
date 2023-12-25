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
        "branch0": {
            "prefix": "[bright_green]",
            "suffix": "[/]",
        },
        "branch1": {
            "prefix": "[bright_red]",
            "suffix": "[/]",
        },
    },
    "line": {
        "branch0": {
            "prefix": lambda _: "[green]",
            "suffix": lambda _: "[/]",
        },
        "branch1": {
            "prefix": lambda _: "[red]",
            "suffix": lambda _: "[/]",
        },
    },
    "escape": rich_escape,
    "separator": "",
}

GIT_MARKUP = {
    "fragment": {
        "branch0": {
            "prefix": "",
            "suffix": "",
        },
        "branch1": {
            "prefix": "",
            "suffix": "",
        },
    },
    "line": {
        "branch0": {
            "prefix": lambda s: f"<<<<<<< {s}\n",
            "suffix": lambda _: "\n",
        },
        "branch1": {
            "prefix": lambda _: "",
            "suffix": lambda s: f"\n>>>>>>> {s}",
        },
    },
    "escape": lambda _: _,
    "separator": "=======\n",
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


def show_header(print, header):
    if header:
        print(f"\n[bright_blue]<<<{escape(header)}>>>[/]")


def show_changes(
    print, fragment_sequence, name0, name1, markup={}, header: str | None = None
):
    show_header(print, header)

    for fragment in fragment_sequence:
        if isinstance(fragment, str):
            print(fragment, end="")

        if isinstance(fragment, tuple):
            print(f"[green]{escape(fragment[0])}[/]", end="")
            print(f"[red]{escape(fragment[1])}[/]", end="")


def show_changes_line_oriented(
    print, fragment_sequence, name0, name1, markup={}, header: str | None = None
):
    show_header(print, header)
    escape = markup.get("escape", lambda _: _)
    line_markup = markup.get("line", {})
    fragment_markup = markup.get("fragment", {})

    def print_line(line, name, line_markup):
        prefix = line_markup["prefix"](name)
        suffix = line_markup["suffix"](name)
        print(f"{prefix}{line}{suffix}")

    def markup_fragment(fragment, fragment_markup):
        print(fragment_markup)
        prefix = fragment_markup["prefix"]
        suffix = fragment_markup["suffix"]
        return f"{prefix}{fragment}{suffix}"

    in_conflict = False
    partial_line_0 = partial_line_1 = ""
    any_line_0 = any_line_1 = False
    for fragment in fragment_sequence:
        if isinstance(fragment, str):
            lines = fragment.split("\n")
            if in_conflict:
                partial_line_0 = partial_line_0 + lines[0]
                partial_line_1 = partial_line_1 + lines[0]
                if len(lines) > 1:
                    print_line(
                        partial_line_0 if any_line_0 else " ",
                        name0,
                        line_markup["branch0"],
                    )
                    print(markup["separator"], end="")
                    print_line(
                        partial_line_1 if any_line_1 else " ",
                        name1,
                        line_markup["branch1"],
                    )
                    partial_line_0 = partial_line_1 = ""
                    any_line_0 = any_line_1 = in_conflict = False
                    print(escape("\n".join(lines[1:-1])))
                    partial_line_0 = lines[-1]
                    partial_line_1 = lines[-1]
            else:
                print(escape(partial_line_0))
                # If not in a conflict, partial_line_0 should be
                # exactly the same as partial_line_1.
                print(escape("\n".join(lines[:-1])))
                partial_line_0 = lines[-1]
                partial_line_1 = lines[-1]

        if isinstance(fragment, tuple):
            in_conflict = True
            if fragment[0]:
                partial_line_0 = partial_line_0 + markup_fragment(
                    fragment[0], fragment_markup["branch0"]
                )
                any_line_0 = True
            if fragment[1]:
                partial_line_1 = partial_line_1 + markup_fragment(
                    fragment[1], fragment_markup["branch1"]
                )
                any_line_1 = True


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
    args = parser.parse_args()
    return args


def get_display_function(arguments):
    if arguments.line_oriented:
        return show_changes_line_oriented

    return show_changes


if __name__ == "__main__":
    console = Console(force_terminal=True, highlight=False)

    arguments = get_arguments()
    display_function = get_display_function(arguments)
    markup = GIT_MARKUP
    markup = SCREEN_MARKUP

    parent, branch0, branch1 = get_file_versions(arguments.test_case)

    def get_text(filename):
        with open(
            os.path.join(TEST_CASE_DIRECTORY, filename), "rt", encoding="ISO-8859-1"
        ) as f:
            data = f.read()
            return data

    parent_text = get_text(parent)
    branch0_text = get_text(branch0)
    branch1_text = get_text(branch1)

    changes0 = diff(parent_text, branch0_text)
    changes1 = diff(parent_text, branch1_text)

    print_fn = console.print

    if arguments.diff:
        display_function(
            console.print, changes0, parent, branch0, markup=markup, header=branch0
        )
        display_function(
            console.print, changes1, parent, branch1, markup=markup, header=branch1
        )

    merged = merge(parent_text, branch0_text, branch1_text)
    display_function(
        console.print,
        merged,
        branch0,
        branch1,
        markup=markup,
        header="Merged" if arguments.diff else None,
    )
