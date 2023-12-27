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
        help="Use a line-oriented diff rather than a fragment-oriented diff",
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


def get_markup_function(arguments):
    if arguments.line_oriented:
        return line_oriented_markup_changes

    return markup_changes


def get_merge_markup_style(arguments):
    if arguments.file_style:
        return GIT_MARKUP
    else:
        return SCREEN_MARKUP


def get_diff_markup_style(arguments):
    if arguments.file_style:
        return GIT_MARKUP
    elif arguments.strikeout:
        return STRIKEOUT_SCREEN_MARKUP
    return SCREEN_MARKUP


def get_writer(arguments):
    if arguments.output is None:
        return console_writer()

    else:
        return file_writer(arguments.output)


def merge_cli():
    arguments = get_merge_arguments()
    display_function = get_markup_function(arguments)
    markup = get_merge_markup_style(arguments)
    diff_markup = get_diff_markup_style(arguments)

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

    with get_writer(arguments) as writer:
        if arguments.diff:
            display_function(
                writer,
                into_changes,
                into_branch,
                parent,
                markup=diff_markup,
                header=into_branch,
            )
            display_function(
                writer,
                from_changes,
                from_branch,
                parent,
                markup=diff_markup,
                header=from_branch,
            )

        merged = merge(parent_text, into_text, from_text)
        display_function(
            writer,
            merged,
            into_branch,
            from_branch,
            markup=markup,
            header="Merged" if arguments.diff else None,
        )


def diff_cli():
    arguments = get_diff_arguments()

    display_function = get_markup_function(arguments)
    markup = get_diff_markup_style(arguments)

    original = arguments.original
    modified = arguments.modified

    def get_text(filename):
        with open(os.path.join(filename), "rt", encoding="utf-8") as f:
            data = f.read()
            return data

    original_text = get_text(original)
    modified_text = get_text(modified)

    changes = diff(original_text, modified_text)

    with get_writer(arguments) as writer:
        display_function(
            writer,
            changes,
            modified,
            original,
            markup=markup,
        )


if __name__ == "__main__":
    diff_cli()
