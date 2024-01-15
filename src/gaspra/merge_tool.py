import argparse
import os

from gaspra.markup import console_writer, file_writer
from gaspra.markup import (
    GIT_MARKUP,
    SCREEN_MARKUP,
    STRIKEOUT_SCREEN_MARKUP,
    line_oriented_markup_changes,
    markup_changes,
)

from gaspra.merge import merge
from gaspra.changesets import diff
from gaspra.tokenizers import (
    decode_changes,
    line_encode_strings,
    CharTokenizer,
    LineTokenizer,
    SymbolTokenizer,
)
from gaspra.types import ChangeIterable
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
        "-g",
        "--git-compatible",
        action="store_true",
        help="Use git-compatible merge conflict markers (no color)",
    )

    parser.add_argument(
        "-L",
        "--show-lines",
        action="store_true",
        help="Show a line-oriented diff, regardless of tokenization of input stream.",
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
    parser.add_argument(
        "-s",
        "--strikeout",
        action="store_true",
        help="Use a strikeout font for deletions (only on diffs).",
    )

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


def get_markup_function(arguments, tokenizer, allow_strikeout=True):
    if arguments.show_lines or arguments.git_compatible:
        wrapped_markup_function = line_oriented_markup_changes
    else:
        wrapped_markup_function = markup_changes

    # Is there any use for this now?
    # wrapped_markup_function = token_oriented_markup_changes

    markup = get_markup_style(arguments, allow_strikeout)

    def markup_function(
        writer,
        changeset: ChangeIterable,
        branch0: str,
        branch1: str,
        header: str | None = "",
    ):
        wrapped_markup_function(
            writer,
            changeset,
            os.path.basename(branch0),
            os.path.basename(branch1),
            markup=markup,
            header=os.path.basename(header) if header else None,
        )

    return markup_function


def get_markup_style(arguments, allow_strikeout=True):
    if arguments.git_compatible:
        return GIT_MARKUP
    elif arguments.strikeout and allow_strikeout:
        return STRIKEOUT_SCREEN_MARKUP
    return SCREEN_MARKUP


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

    token_map = None
    if not arguments.characters:
        token_map, parent, current, other = line_encode_strings(parent, current, other)

    with get_writer(arguments) as writer:
        writer, escape = writer
        if arguments.diff:
            diff_markup = get_markup_function(
                arguments, token_map, allow_strikeout=True
            )
            current_changes = diff(parent, current)
            other_changes = diff(parent, other)

            def markup_one(changes, branch_name):
                diff_markup(
                    writer,
                    escape,
                    changes,
                    branch_name,
                    parent_name,
                    header=branch_name,
                )

            markup_one(current_changes, current_name)
            markup_one(other_changes, other_name)

        merged = merge(parent, current, other)
        merge_markup = get_markup_function(arguments, token_map, allow_strikeout=False)

        merge_markup(
            writer,
            escape,
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

    original = tokenizer.encode(original)
    modified = tokenizer.encode(modified)

    changes = diff(original, modified)

    display_function = get_markup_function(arguments, tokenizer)

    with get_writer(arguments) as writer:
        writer, escape = writer
        display_function(
            writer,
            decode_changes(tokenizer, changes, escape),
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
    diff_cli()
