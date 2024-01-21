import argparse
import os
import copy
import sys

from gaspra.markup import console_writer, file_writer
from gaspra.markup import (
    GIT_MARKUP_LEVEL0,
    COLORED_LEVEL0,
    PLAIN_LEVEL1,
    COLORED_LEVEL1,
    strikeout_level0,
    strikeout_level1,
    markup_changes,
)

from gaspra.merge import merge_token_sequence
from gaspra.diff_to_lines import to_line_diff
from gaspra.changesets import diff_token_sequences
from gaspra.tokenizers import (
    decode_changes,
    diff,
    CharTokenizer,
    LineTokenizer,
    SymbolTokenizer,
)
from gaspra.types import DiffIterable
import gaspra.torture_test as torture_test


def add_common_arguments(parser):
    parser.add_argument(
        "-o",
        "--output",
        help="Output file",
        default=None,
    )
    token_group = parser.add_mutually_exclusive_group()

    token_group.add_argument(
        "-c",
        "--characters",
        action="store_true",
        help="Process input as stream of characters",
    )
    token_group.add_argument(
        "-w",
        "--words",
        action="store_true",
        help="Process input as stream of words or symbols",
    )
    token_group.add_argument(
        "-l",
        "--lines",
        action="store_true",
        help="Process input stream of lines",
    )

    parser.add_argument(
        "-L",
        "--show-lines",
        action="store_true",
        help="Show line-oriented diffs, regardless of tokenization of input stream.",
    )

    parser.add_argument(
        "-g",
        "--git-compatible",
        action="store_true",
        help="Use git-compatible merge conflict markers (no color)",
    )

    parser.add_argument(
        "-s",
        "--strikeout",
        action="store_true",
        help="Use a strikeout font for deletions (only on diffs))",
    )


def get_merge_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("parent")
    parser.add_argument("from_branch_head")
    parser.add_argument("into_branch_head")

    add_common_arguments(parser)

    parser.add_argument(
        "-d", "--diff", action="store_true", help="Show diffs along with merge result"
    )

    args = parser.parse_args()
    return args


def get_diff_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("original")
    parser.add_argument("modified")

    add_common_arguments(parser)
    args = parser.parse_args()
    return args


def get_torture_test_arguments():
    parser = argparse.ArgumentParser(usage=torture_test.get_usage())
    parser.add_argument("test_case")
    add_common_arguments(parser)

    parser.add_argument(
        "-d", "--diff", action="store_true", help="Show diffs along with merge result"
    )

    args = parser.parse_args()
    return args


def get_markup_function(arguments, escape, allow_strikeout=True):
    markup = get_markup_style(arguments, allow_strikeout)

    def markup_function(
        writer,
        changeset: DiffIterable,
        branch0: str,
        branch1: str,
        header: str | None = "",
    ):
        markup_changes(
            writer,
            changeset,
            markup0=markup["level0"],
            markup1=markup["level1"],
            name_into=os.path.basename(branch0),
            name_from=os.path.basename(branch1),
            header=os.path.basename(header) if header else None,
            escape=escape,
        )

    return markup_function


def get_markup_style(arguments, allow_strikeout=True):
    if arguments.git_compatible:
        level0 = GIT_MARKUP_LEVEL0
    else:
        level0 = COLORED_LEVEL0
    if arguments.output:
        level1 = PLAIN_LEVEL1
    else:
        level1 = COLORED_LEVEL1

    markup = {"level0": level0, "level1": level1}

    if arguments.strikeout and allow_strikeout:
        markup["level0"]["from"] = strikeout_level0
        markup["level1"]["from"] = strikeout_level1

    return copy.deepcopy(markup)


def get_writer(arguments):
    if arguments.output is None:
        return console_writer()

    else:
        return file_writer(arguments.output)


def merge_cli():
    arguments = get_merge_arguments()
    parent_name = arguments.parent
    current_name = arguments.into_branch_head
    other_name = arguments.from_branch_head

    _merge(parent_name, current_name, other_name, arguments)


def torture_cli():
    arguments = get_torture_test_arguments()

    test_case = arguments.test_case

    parent_name, current_name, other_name = torture_test.get_filenames(test_case)

    _merge(parent_name, current_name, other_name, arguments)


def _merge(parent_name, current_name, other_name, arguments):
    parent, current, other = get_text(parent_name, current_name, other_name)

    tokenizer = make_tokenizer(arguments)

    parent = tokenizer.encode(parent)
    current = tokenizer.encode(current)
    other = tokenizer.encode(other)

    with get_writer(arguments) as writer_and_escape:
        writer, escape = writer_and_escape
        if arguments.diff:
            diff_markup = get_markup_function(arguments, escape, allow_strikeout=True)

            current_changes = decode_changes(
                diff_token_sequences(parent, current), tokenizer
            )
            other_changes = decode_changes(
                diff_token_sequences(parent, other), tokenizer
            )

            def markup_one(changes, branch_name):
                diff_markup(
                    writer,
                    changes,
                    branch_name,
                    parent_name,
                    header=branch_name,
                )

            if arguments.show_lines or arguments.git_compatible:
                current_changes = to_line_diff(current_changes)
                other_changes = to_line_diff(other_changes)

            markup_one(current_changes, current_name)
            markup_one(other_changes, other_name)

        merged = decode_changes(merge_token_sequence(parent, current, other), tokenizer)

        if arguments.show_lines or arguments.git_compatible:
            merged = to_line_diff(merged)

        merge_markup = get_markup_function(arguments, escape, allow_strikeout=False)

        merge_markup(
            writer,
            merged,
            current_name,
            other_name,
            header="Merged" if arguments.diff else None,
        )


def make_tokenizer(arguments):
    if arguments.words:
        return SymbolTokenizer()
    if arguments.lines:
        return LineTokenizer()
    return CharTokenizer()


def diff_cli():
    arguments = get_diff_arguments()

    original_name = arguments.original
    modified_name = arguments.modified

    original, modified = get_text(original_name, modified_name)

    tokenizer = make_tokenizer(arguments)

    with get_writer(arguments) as writer:
        writer, escape = writer

        display_function = get_markup_function(arguments, escape, allow_strikeout=True)

        changes = diff(original, modified, tokenizer)

        if arguments.show_lines or arguments.git_compatible:
            changes = to_line_diff(changes)

        display_function(
            writer,
            changes,
            escape(modified_name),
            escape(original_name),
        )


def get_text(*filenames: str) -> tuple[str, ...]:
    data = []
    for filename in filenames:
        try:
            with open(filename, "rt", encoding="utf-8") as f:
                data.append(f.read())

        except UnicodeDecodeError:
            with open(filename, "rt", encoding="iso-8859-1") as f:
                data.append(f.read())

    return tuple(data)


def get_bytes(*filenames: str) -> tuple[bytes, ...]:
    data = []
    for filename in filenames:
        with open(filename, "rb") as f:
            data.append(f.read())
    return tuple(data)


if __name__ == "__main__":
    sys.argv = [
        __file__,
        "-dg",
        "test-files/x",
        "test-files/y",
        "test-files/z",
    ]
    merge_cli()
