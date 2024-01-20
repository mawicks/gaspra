from collections.abc import Hashable, Iterable, Sequence
from contextlib import contextmanager
from copy import deepcopy
import io

from rich.console import Console

from gaspra.types import Change


def rich_escape(s):
    return s.replace("[", r"\[")


SCREEN_MARKUP = {
    "level0": {
        "into": {"prefix": lambda _: "[green4]", "suffix": lambda _: "[/]"},
        "from": {"prefix": lambda _: "[dark_red]", "suffix": lambda _: "[/]"},
        "separator": "",
        "header": {"prefix": "<<<[bright_blue]", "suffix": "[/]>>>\n"},
    },
    "level1": {
        "into": {"prefix": lambda _: "[light_green]", "suffix": lambda _: "[/]"},
        "from": {"prefix": lambda _: "[pink1]", "suffix": lambda _: "[/]"},
        "separator": "",
    },
}

STRIKEOUT_SCREEN_MARKUP = deepcopy(SCREEN_MARKUP)
STRIKEOUT_SCREEN_MARKUP["level0"]["from"]["prefix"] = lambda _: "[red strike]"
STRIKEOUT_SCREEN_MARKUP["level1"]["from"]["prefix"] = lambda _: "[bright_red strike]"

GIT_MARKUP = {
    "level1": {
        "into": {"prefix": lambda _: "", "suffix": lambda _: ""},
        "from": {"prefix": lambda _: "", "suffix": lambda _: ""},
        "separator": "",
        "header": {"prefix": "<<<", "suffix": ">>>\n"},
    },
    "level0": {
        "into": {"prefix": lambda s: f"<<<<<<< {s}\n", "suffix": lambda _: ""},
        "from": {"prefix": lambda _: "", "suffix": lambda s: f">>>>>>> {s}\n"},
        "separator": "=======\n",
    },
}


def show_header(print, header, markup={}):
    header_markup = markup.get("header", {})
    prefix = header_markup.get("prefix", "")
    suffix = header_markup.get("suffix", "")
    if header:
        print(f"\n{prefix}{header}{suffix}")


def old_markup_changes(
    print,
    fragment_sequence: Iterable[Sequence[Hashable] | tuple[Sequence[Hashable]]],
    __name0__,
    __name1__,
    markup={},
    header: str | None = None,
    **__kwargs__,
):
    show_header(print, header, markup)

    fragment_markup = markup.get("fragment", {})

    def print_fragment(fragment, fragment_markup):
        prefix = fragment_markup["prefix"]
        suffix = fragment_markup["suffix"]
        print(f"{prefix}{fragment}{suffix}")

    for fragment in fragment_sequence:
        if isinstance(fragment, Change):
            print_fragment(fragment.a, fragment_markup["into"])
            print_fragment(fragment.b, fragment_markup["from"])

        else:
            print(fragment)


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
    fragment: Change,
    fragment_markup,
):
    partial_line_into = _markup_and_add_fragment(
        partial_line_into,
        fragment.a,
        fragment_markup["into"],
    )
    partial_line_from = _markup_and_add_fragment(
        partial_line_from,
        fragment.b,
        fragment_markup["from"],
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

    def finish_conflict(partial_line_into, partial_line_from, input_fragment):
        input_fragment = input_fragment
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
    markup={},
    header: str | None = None,
):
    show_header(print, header, markup)
    fragment_markup = markup.get("fragment", {})

    finish_conflict = conflict_finisher(print, markup, name0, name1)

    in_conflict = False
    partial_line_into = partial_line_from = ""
    for fragment in fragment_sequence:
        if isinstance(fragment, Change):
            in_conflict = True
            partial_line_into, partial_line_from = markup_and_add_fragment(
                partial_line_into,
                partial_line_from,
                fragment,
                fragment_markup,
            )
        elif isinstance(fragment, str):
            lines = fragment.split("\n")
            if len(lines) > 1:  # Have a newline
                if in_conflict:
                    finish_conflict(
                        partial_line_into,
                        partial_line_from,
                        lines[0] + "\n",
                    )
                    print(join_with_newline(lines[1:-1]))
                else:
                    print(join_with_newline(lines[:-1]))
                in_conflict = False
                partial_line_into = partial_line_from = lines[-1]
            else:
                partial_line_into += lines[0]
                partial_line_from += lines[0]

    if in_conflict:
        if partial_line_into[-1:] != "\n" or partial_line_from[-1:] != "\n":
            tail = "\n"
        else:
            tail = ""
        finish_conflict(partial_line_into, partial_line_from, tail)
    elif partial_line_from:
        # If not in a conflict, partial_line_into should be
        # exactly the same as partial_line_from.
        print(partial_line_from + "\n")


def join_with_newline(lines):
    if len(lines) > 0:
        return "\n".join(line for line in lines) + "\n"
    else:
        return ""


@contextmanager
def file_writer(filename):
    file = open(filename, "wt", encoding="utf-8")

    yield file.write, lambda _: _
    file.close()


@contextmanager
def console_writer():
    console = Console(force_terminal=True, highlight=False)

    def print(s):
        console.print(s, end="")

    yield print, rich_escape
    return


def print_conflict(print, version, name, markup):
    prefix = markup["prefix"](name)
    suffix = markup["suffix"](name)
    # Collect output in a buffer so that prefix and suffix
    # tags appear in the same call to print().
    # That is important for the rich Console writer.
    buffer = io.StringIO()
    if prefix is not None:
        buffer.write(prefix)
    buffer.write(version)
    if suffix is not None:
        buffer.write(suffix)
    print(buffer.getvalue())


def token_oriented_markup_changes(
    print,
    fragment_sequence,
    name0,
    name1,
    markup={},
    header: str | None = None,
):
    if header:
        show_header(print, header, markup)

    for item in fragment_sequence:
        if isinstance(item, Change):
            print_conflict(print, item.a, name0, markup["into"])
            print(markup["separator"])
            print_conflict(print, item.b, name1, markup["from"])
        else:
            print(item)


def markup_stream(
    print, stream, name_into, name_from, markup0, markup1=None, escape=lambda _: _
):
    markup_into = markup0["into"]
    markup_from = markup0["from"]

    for item in stream:
        if isinstance(item, str):
            print(escape(item))
            continue

        if isinstance(item, Change):
            if item.a:
                print(
                    markup_change_item(
                        item.a, markup_into, name_into, name_from, markup1, escape
                    )
                )

            print(markup0["separator"])

            if item.b:
                print(
                    markup_change_item(
                        item.b, markup_from, name_into, name_from, markup1, escape
                    )
                )


def markup_change_item(item, branch_markup, name_into, name_from, markup, escape):
    # Accumulate everything into a buffer mainly because of `rich`.  It
    # requires that the prefix and suffix be printed with the same rich
    # call.  That means we accumulate all of the contents between the
    # prefix and suffix and then send the accumulated result to rich.

    output_buffer = io.StringIO()
    write = output_buffer.write
    write(branch_markup["prefix"](name_into))
    if isinstance(item, str):
        write(escape(item))
    else:
        markup_stream(write, item, name_into, name_from, markup, escape=escape)
    write(branch_markup["suffix"](name_into))
    return output_buffer.getvalue()


def markup_changes(
    print,
    stream,
    name_into,
    name_from,
    markup0={},
    markup1={},
    header: str | None = None,
    escape=lambda _: _,
):
    if header:
        show_header(print, header, markup0)

    markup_stream(print, stream, name_into, name_from, markup0, markup1, escape)
