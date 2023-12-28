from collections.abc import Iterable
import argparse
import os

from gaspra.markup import console_writer, file_writer
from gaspra.markup import (
    GIT_MARKUP,
    SCREEN_MARKUP,
    STRIKEOUT_SCREEN_MARKUP,
    TOKEN_GIT_MARKUP,
    TOKEN_SCREEN_MARKUP,
    line_oriented_markup_changes,
    markup_changes,
    token_oriented_markup_changes,
)

from gaspra.merge import merge
from gaspra.changesets import diff
from gaspra.types import TokenSequence, ChangeIterable
import gaspra.torture_test as torture_test


def tokenize(
    *string_set: str,
) -> Iterable[TokenSequence]:
    tokenized = []
    token_dict = {}

    for s in string_set:
        lines = s.split("\n")
        # Ignore the empty string that gets generated
        # by an ending newline.

        if len(lines) > 0 and lines[-1] == "":
            lines = lines[:-1]

        for line in s.split("\n"):
            if line not in token_dict:
                token_dict[line] = len(token_dict)

        tokenized.append(tuple(token_dict[line] for line in lines))
    token_map = tuple(token_dict.keys())
    return tuple([token_map, *tokenized])


def add_common_arguments(parser):
    parser.add_argument(
        "-o",
        "--output",
        help="Output file",
        default=None,
    )
    parser.add_argument(
        "-l",
        "--line-oriented",
        action="store_true",
        help="Use a line-oriented diff for output rather than a fragment-oriented diff",
    )
    parser.add_argument(
        "-t",
        "--tokenize-lines",
        action="store_true",
        help="Process the input a line at a time rather than a character at a time (implies -l)",
    )
    parser.add_argument(
        "-f",
        "--file-style",
        action="store_true",
        help='Mark up for file output (git-style with "-l", no color otherwise)',
    )
    parser.add_argument(
        "-s",
        "--strikeout",
        action="store_true",
        help="Use a strikeout font for deletions on diffs.",
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


def get_markup_function(arguments, token_map=(), allow_strikeout=True):
    if arguments.tokenize_lines:
        wrapped_markup_function = token_oriented_markup_changes

    elif arguments.line_oriented:
        wrapped_markup_function = line_oriented_markup_changes
    else:
        wrapped_markup_function = markup_changes

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
            token_map=token_map,
        )

    return markup_function


def get_markup_style(arguments, allow_strikeout=True):
    if arguments.tokenize_lines:
        if arguments.file_style:
            return TOKEN_GIT_MARKUP
        return TOKEN_SCREEN_MARKUP
    if arguments.file_style:
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
    if arguments.tokenize_lines:
        token_map, parent, current, other = tokenize(parent, current, other)

    with get_writer(arguments) as writer:
        if arguments.diff:
            diff_markup = get_markup_function(
                arguments, token_map, allow_strikeout=True
            )
            current_changes = diff(parent, current)
            other_changes = diff(parent, other)

            def markup_one(changes, branch_name):
                diff_markup(
                    writer,
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
            merged,
            current_name,
            other_name,
            header="Merged" if arguments.diff else None,
        )


def diff_cli():
    arguments = get_diff_arguments()

    original_name = arguments.original
    modified_name = arguments.modified

    original, modified = get_text(original_name, modified_name)

    token_map = None
    if arguments.tokenize_lines:
        token_map, original, modified = tokenize(original, modified)

    changes = diff(original, modified)

    display_function = get_markup_function(arguments, token_map)

    with get_writer(arguments) as writer:
        display_function(
            writer,
            changes,
            modified_name,
            original_name,
        )


def get_text(*filenames: str):
    data = []
    for filename in filenames:
        try:
            with open(filename, "rt", encoding="utf-8") as f:
                data.append(f.read())

        except UnicodeDecodeError:
            with open(filename, "rt", encoding="iso-8859-1") as f:
                data.append(f.read())

    return tuple(data)


if __name__ == "__main__":
    torture_cli()
