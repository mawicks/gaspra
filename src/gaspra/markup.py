from contextlib import contextmanager
from copy import deepcopy
from rich.console import Console

from gaspra.types import Change


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

STRIKEOUT_SCREEN_MARKUP = deepcopy(SCREEN_MARKUP)
STRIKEOUT_SCREEN_MARKUP["fragment"]["from"]["prefix"] = "[bright_red strike]"
STRIKEOUT_SCREEN_MARKUP["line"]["from"]["prefix"] = "[red strike]"

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
    escape = markup.get("escape", lambda _: _)
    header_markup = markup.get("header", {})
    prefix = header_markup.get("prefix", "")
    suffix = header_markup.get("suffix", "")
    if header:
        print(f"\n{prefix}{escape(header)}{suffix}")


def markup_changes(
    print, fragment_sequence, __name0__, __name1__, markup={}, header: str | None = None
):
    escape = markup.get("escape", lambda _: _)

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


def print_line(print, line, name, line_markup):
    prefix = line_markup["prefix"](name)
    suffix = line_markup["suffix"](name)
    print(f"{prefix}{line}{suffix}")


def markup_fragment(fragment, fragment_markup):
    prefix = fragment_markup["prefix"]
    suffix = fragment_markup["suffix"]
    return f"{prefix}{fragment}{suffix}"


def line_oriented_markup_changes(
    print, fragment_sequence, name0, name1, markup={}, header: str | None = None
):
    show_header(print, header, markup)
    escape = markup.get("escape", lambda _: _)
    line_markup = markup.get("line", {})
    fragment_markup = markup.get("fragment", {})

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
            print,
            partial_line_into,
            name0,
            line_markup["into"],
        )
        print(markup["separator"])
        print_line(
            print,
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
            if len(lines) > 1:  # Have a newline
                if in_conflict:
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
                else:
                    print(escape("\n".join(lines[:-1])) + "\n")
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
        if partial_line_into[-1:] != "\n" or partial_line_from[-1:] != "\n":
            tail = "\n"
        else:
            tail = ""
        finish_conflict(partial_line_into, partial_line_from, name0, name1, tail)
    else:
        print(escape(partial_line_from))
        if partial_line_from:
            print("\n")


@contextmanager
def file_writer(filename):
    file = open(filename, "wt", encoding="utf-8")
    writer = file.write
    yield writer
    file.close()


@contextmanager
def console_writer():
    console = Console(force_terminal=True, highlight=False)

    def print(s):
        console.print(s, end="")

    yield print
    return


def print_conflict(print, version, token_dict, escape, name, markup):
    prefix = markup["prefix"](name)
    suffix = markup["suffix"](name)
    if prefix is not None:
        print(prefix)
    for token in version:
        print(escape(token_dict[token]))
    if suffix is not None:
        print(suffix)


def token_oriented_markup_changes(
    print,
    fragment_sequence,
    token_dict,
    name0,
    name1,
    markup={},
    header: str | None = None,
):
    escape = markup["escape"]

    if header:
        show_header(print, header, markup)

    for item in fragment_sequence:
        if isinstance(item, Change):
            print_conflict(print, item.a, token_dict, escape, name0, markup["into"])
            print(markup["separator"])
            print_conflict(print, item.b, token_dict, escape, name1, markup["from"])
        else:
            for token in item:
                print(token_dict[token])
