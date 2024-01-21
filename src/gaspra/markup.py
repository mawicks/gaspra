from collections.abc import Hashable, Iterable, Sequence
from contextlib import contextmanager
import io

from rich.console import Console

from gaspra.types import Change


def rich_escape(s):
    return s.replace("[", r"\[")


COLORED_LEVEL0 = {
    "into": {"prefix": lambda _: "[green4]", "suffix": lambda _: "[/]"},
    "from": {"prefix": lambda _: "[dark_red]", "suffix": lambda _: "[/]"},
    "separator": "",
    "header": {"prefix": "<<<[bright_blue]", "suffix": "[/]>>>\n"},
}

GIT_MARKUP_LEVEL0 = {
    "into": {"prefix": lambda s: f"<<<<<<< {s}\n", "suffix": lambda _: ""},
    "from": {"prefix": lambda _: "", "suffix": lambda s: f">>>>>>> {s}\n"},
    "separator": "=======\n",
}

PLAIN_LEVEL1 = {
    "into": {"prefix": lambda _: "", "suffix": lambda _: ""},
    "from": {"prefix": lambda _: "", "suffix": lambda _: ""},
    "separator": "",
    "header": {"prefix": "<<<", "suffix": ">>>\n"},
}


COLORED_LEVEL1 = {
    "into": {"prefix": lambda _: "[light_green]", "suffix": lambda _: "[/]"},
    "from": {"prefix": lambda _: "[pink1]", "suffix": lambda _: "[/]"},
    "separator": "",
}


STRIKEOUT_LEVEL0 = lambda _: "[dark_red strike]"
STRIKEOUT_LEVEL1 = lambda _: "[pink1 strike]"


def show_header(print, header, markup={}):
    header_markup = markup.get("header", {})
    prefix = header_markup.get("prefix", "")
    suffix = header_markup.get("suffix", "")
    if header:
        print(f"\n{prefix}{header}{suffix}")


@contextmanager
def file_writer(filename):
    file = open(filename, "wt", encoding="utf-8")

    yield file.write, lambda _: _
    file.close()


@contextmanager
def console_writer():
    console = Console(force_terminal=None, highlight=False)

    def print(s):
        console.print(s, end="")

    yield print, rich_escape
    return


def markup_stream(
    print,
    stream,
    markup0,
    markup1=None,
    name_into=None,
    name_from=None,
    escape=lambda _: _,
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
                        item.a,
                        markup_into,
                        name_into,
                        markup1,
                        escape,
                    )
                )

            print(markup0["separator"])

            if item.b:
                print(
                    markup_change_item(
                        item.b,
                        markup_from,
                        name_from,
                        markup1,
                        escape,
                    )
                )


def markup_change_item(item, branch_markup, branch_name, markup, escape):
    # Accumulate everything into a buffer mainly because of `rich`.  It
    # requires that the prefix and suffix be printed with the same rich
    # call.  That means we accumulate all of the contents between the
    # prefix and suffix and then send the accumulated result to rich.

    output_buffer = io.StringIO()
    write = output_buffer.write
    write(branch_markup["prefix"](branch_name))
    if isinstance(item, str):
        write(escape(item))
    else:
        markup_stream(write, item, markup, escape=escape)
    write(branch_markup["suffix"](branch_name))
    return output_buffer.getvalue()


def markup_changes(
    print,
    stream,
    markup0={},
    markup1={},
    name_into=None,
    name_from=None,
    header: str | None = None,
    escape=lambda _: _,
):
    if header:
        show_header(print, header, markup0)

    markup_stream(print, stream, markup0, markup1, name_into, name_from, escape)
