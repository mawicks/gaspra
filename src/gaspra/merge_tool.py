import argparse
import os

from rich.console import Console

from gaspra.merge import merge
from gaspra.changesets import escape, diff

PROGRAM_NAME = os.path.basename(__file__)


def rich_escape(s):
    return s.replace("[", r"\[")


SCREEN_MARKUP = {
    "fragment": {
        "into": {"prefix": "[bright_green]", "suffix": "[/]"},
        "from": {"prefix": "[bright_red]", "suffix": "[/]"},
    },
    "line": {
        "into": {"prefix": lambda _: "[green]", "suffix": lambda _: "[/]"},
        "from": {"prefix": lambda _: "[red]", "suffix": lambda _: "[/]"},
    },
    "escape": rich_escape,
    "separator": "",
    "header": {"prefix": "<<<[bright_blue]", "suffix": "[/]>>>\n"},
}

GIT_MARKUP = {
    "fragment": {
        "into": {"prefix": "", "suffix": ""},
        "from": {"prefix": "", "suffix": ""},
    },
    "line": {
        "into": {"prefix": lambda s: f"<<<<<<< {s}\n", "suffix": lambda _: ""},
        "from": {"prefix": lambda _: "", "suffix": lambda s: f">>>>>>> {s}\n"},
    },
    "escape": lambda _: _,
    "separator": "=======\n",
    "header": {"prefix": "<<<", "suffix": ">>>\n"},
}


def show_header(print, header, markup={}):
    header_markup = markup.get("header", {})
    prefix = header_markup.get("prefix", "")
    suffix = header_markup.get("suffix", "")
    if header:
        print(f"\n{prefix}{escape(header)}{suffix}")


def markup_changes(
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


def line_oriented_markup_changes(
    print, fragment_sequence, name0, name1, markup={}, header: str | None = None
):
    show_header(print, header, markup)
    escape = markup.get("escape", lambda _: _)
    line_markup = markup.get("line", {})
    fragment_markup = markup.get("fragment", {})

    def print_line(line, name, line_markup):
        prefix = line_markup["prefix"](name)
        suffix = line_markup["suffix"](name)
        print(f"{prefix}{line}{suffix}")

    def markup_fragment(fragment, fragment_markup):
        prefix = fragment_markup["prefix"]
        suffix = fragment_markup["suffix"]
        return f"{prefix}{fragment}{suffix}"

    def finish_conflict(
        partial_line_into, partial_line_from, name0, name1, input_fragment
    ):
        input_fragment = escape(input_fragment)
        if (partial_line_into and partial_line_into[-1] != "\n") or (
            partial_line_from and partial_line_from[-1] != "\n"
        ):
            partial_line_into = partial_line_into + input_fragment
            partial_line_from = partial_line_from + input_fragment
            input_fragment = ""

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
        print(input_fragment)

    in_conflict = False
    partial_line_into = partial_line_from = ""
    for fragment in fragment_sequence:
        if isinstance(fragment, str):
            lines = fragment.split("\n")
            if in_conflict:
                if len(lines) > 1:  # Have a newline
                    finish_conflict(
                        partial_line_into,
                        partial_line_from,
                        name0,
                        name1,
                        lines[0] + "\n",
                    )
                    in_conflict = False
                    print(
                        escape("\n".join(lines[1:-1])) + "\n" if len(lines) > 2 else ""
                    )
                    partial_line_into = lines[-1]
                    partial_line_from = lines[-1]
                else:
                    partial_line_into += lines[0]
                    partial_line_from += lines[0]

            else:
                if len(lines) > 1:  # Have a newline
                    print(escape("\n".join(lines[:-1])))
                    print("\n")
                    # If not in a conflict, partial_line_into should be
                    # exactly the same as partial_line_from.
                    partial_line_into = lines[-1]
                    partial_line_from = lines[-1]
                else:
                    partial_line_into += lines[0]
                    partial_line_from += lines[0]

        if isinstance(fragment, tuple):
            in_conflict = True
            if fragment[0]:
                partial_line_into = partial_line_into + markup_fragment(
                    fragment[0], fragment_markup["into"]
                )
            if fragment[1]:
                partial_line_from = partial_line_from + markup_fragment(
                    fragment[1], fragment_markup["from"]
                )
    if in_conflict:
        if partial_line_into[-1:] != "\n" or partial_line_from[-1] != "\n":
            tail = "\n"
        else:
            tail = ""
        finish_conflict(partial_line_into, partial_line_from, name0, name1, tail)
    else:
        print(escape(partial_line_from))
        if partial_line_from:
            print("\n")


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("parent")
    parser.add_argument("from_branch_head")
    parser.add_argument("into_branch_head")
    parser.add_argument(
        "-l",
        "--line-oriented",
        action="store_true",
        help="Use a line-oriented diff rather than a fragment-oriented diff",
    )
    parser.add_argument(
        "-d", "--diff", action="store_true", help="Show diffs along with merge result"
    )
    parser.add_argument(
        "-f",
        "--file-style",
        action="store_true",
        help='Mark up for file output (git-style with "-l", no color otherwise)',
    )
    args = parser.parse_args()
    return args


def get_display_function(arguments):
    if arguments.line_oriented:
        return line_oriented_markup_changes

    return markup_changes


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

    parent = arguments.parent
    into_branch = arguments.into_branch_head
    from_branch = arguments.from_branch_head

    def get_text(filename):
        with open(os.path.join(filename), "rt", encoding="utf-8") as f:
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
