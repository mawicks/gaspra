from collections.abc import Hashable, Iterable, Sequence
from contextlib import contextmanager
from copy import deepcopy
import io
from typing import cast

from rich.console import Console

from gaspra.types import Change
from gaspra.tokenizers import Tokenizer


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

TOKEN_GIT_MARKUP = {
    "into": {"prefix": lambda s: f"<<<<<<< {s}\n", "suffix": lambda _: ""},
    "from": {"prefix": lambda _: "", "suffix": lambda s: f">>>>>>> {s}\n"},
    "escape": lambda _: _,
    "separator": "=======\n",
    "header": {"prefix": "<<<", "suffix": ">>>"},
}

TOKEN_SCREEN_MARKUP = {
    "into": {"prefix": lambda _: "[bright_green]", "suffix": lambda _: "[/]"},
    "from": {"prefix": lambda _: "[bright_red]", "suffix": lambda _: "[/]"},
    "escape": rich_escape,
    "separator": "",
    "header": {"prefix": "<<<", "suffix": ">>>"},
}


def show_header(print, header, markup={}):
    escape = markup.get("escape", lambda _: _)
    header_markup = markup.get("header", {})
    prefix = header_markup.get("prefix", "")
    suffix = header_markup.get("suffix", "")
    if header:
        print(f"\n{prefix}{escape(header)}{suffix}")


def markup_changes(
    print,
    fragment_sequence: Iterable[Sequence[Hashable] | tuple[Sequence[Hashable]]],
    __name0__,
    __name1__,
    tokenizer: Tokenizer,
    markup={},
    header: str | None = None,
    **__kwargs__,
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


def _markup_and_add_fragment(partial_line, fragment, fragment_markup):
    if fragment:
        prefix = fragment_markup["prefix"]
        suffix = fragment_markup["suffix"]
        return partial_line + f"{prefix}{fragment}{suffix}"
    else:
        return partial_line


def markup_and_add_fragment(
    partial_line_into: str,
    partial_line_from: str,
    fragment: tuple[Iterable[Hashable], Iterable[Hashable]],
    tokenizer: Tokenizer[str],
    fragment_markup,
):
    partial_line_into = _markup_and_add_fragment(
        partial_line_into, tokenizer.decode(fragment[0]), fragment_markup["into"]
    )
    partial_line_from = _markup_and_add_fragment(
        partial_line_from, tokenizer.decode(fragment[1]), fragment_markup["from"]
    )
    return partial_line_into, partial_line_from


def update_partials(partial_line_into, partial_line_from, input_fragment):
    if (partial_line_into and partial_line_into[-1] != "\n") or (
        partial_line_from and partial_line_from[-1] != "\n"
    ):
        partial_line_into = partial_line_into + input_fragment
        partial_line_from = partial_line_from + input_fragment
        input_fragment = ""
    return partial_line_into, partial_line_from, input_fragment


def conflict_finisher(print, markup, name0, name1):
    line_markup = markup.get("line", {})
    escape = markup.get("escape", lambda _: _)

    def finish_conflict(partial_line_into, partial_line_from, input_fragment):
        input_fragment = escape(input_fragment)
        partial_line_into, partial_line_from, input_fragment = update_partials(
            partial_line_into, partial_line_from, input_fragment
        )

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

    return finish_conflict


def line_oriented_markup_changes(
    print,
    fragment_sequence: Iterable[Sequence[Hashable]],
    name0,
    name1,
    tokenizer: Tokenizer[str],
    markup={},
    header: str | None = None,
    **__kwargs__,
):
    show_header(print, header, markup)
    escape = markup.get("escape", lambda _: _)
    fragment_markup = markup.get("fragment", {})

    finish_conflict = conflict_finisher(print, markup, name0, name1)

    in_conflict = False
    partial_line_into = partial_line_from = ""
    for fragment in fragment_sequence:
        if isinstance(fragment, str):
            lines = tokenizer.decode(fragment).split("\n")
            if len(lines) > 1:  # Have a newline
                if in_conflict:
                    finish_conflict(
                        partial_line_into,
                        partial_line_from,
                        lines[0] + "\n",
                    )
                    print(escape(join(lines[1:-1])))
                else:
                    print(escape(join(lines[:-1])))
                in_conflict = False
                partial_line_into = partial_line_from = lines[-1]
            else:
                partial_line_into += lines[0]
                partial_line_from += lines[0]

        if isinstance(fragment, tuple):
            fragment = cast(tuple[Iterable[Hashable], Iterable[Hashable]], fragment)
            in_conflict = True
            partial_line_into, partial_line_from = markup_and_add_fragment(
                partial_line_into,
                partial_line_from,
                fragment,
                tokenizer,
                fragment_markup,
            )
    if in_conflict:
        if partial_line_into[-1:] != "\n" or partial_line_from[-1:] != "\n":
            tail = "\n"
        else:
            tail = ""
        finish_conflict(partial_line_into, partial_line_from, tail)
    elif partial_line_from:
        # If not in a conflict, partial_line_into should be
        # exactly the same as partial_line_from.
        print(escape(partial_line_from) + "\n")


def join(lines):
    if len(lines) > 0:
        return "\n".join(line for line in lines) + "\n"
    else:
        return ""


@contextmanager
def file_writer(filename):
    file = open(filename, "wt", encoding="utf-8")

    yield file.write
    file.close()


@contextmanager
def console_writer():
    console = Console(force_terminal=True, highlight=False)

    def print(s):
        console.print(s, end="")

    yield print
    return


def print_conflict(print, version, tokenizer: Tokenizer, escape, name, markup):
    prefix = markup["prefix"](name)
    suffix = markup["suffix"](name)
    # Collect output in a buffer so that prefix and suffix
    # tags appear in the same call to print().
    # That is important for the rich Console writer.
    buffer = io.StringIO()
    if prefix is not None:
        buffer.write(prefix)
    buffer.write(escape(tokenizer.decode(version)))
    if suffix is not None:
        buffer.write(suffix)
    print(buffer.getvalue())


def token_oriented_markup_changes(
    print,
    fragment_sequence,
    name0,
    name1,
    tokenizer: Tokenizer,
    markup={},
    header: str | None = None,
):
    escape = markup["escape"]

    if header:
        show_header(print, header, markup)

    for item in fragment_sequence:
        if isinstance(item, Change):
            print_conflict(print, item.a, tokenizer, escape, name0, markup["into"])
            print(markup["separator"])
            print_conflict(print, item.b, tokenizer, escape, name1, markup["from"])
        else:
            print(tokenizer.decode(item))
