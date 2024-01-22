import pytest
import io
from itertools import chain

from gaspra.markup import (
    markup_changes,
)
from gaspra.types import Change


TEST_DIFF_MARKUP = {
    "level0": {
        "into": {
            "prefix": lambda s: f"< {s}\n",
            "suffix": lambda _: "[i]",
        },
        "from": {
            "prefix": lambda _: "[f]",
            "suffix": lambda s: f"> {s}\n",
        },
        "separator": "=\n",
        "header": {"prefix": "{", "suffix": "}"},
    },
    "level1": {
        "into": {"prefix": lambda _: "<", "suffix": lambda _: ">"},
        "from": {"prefix": lambda _: "[", "suffix": lambda _: "]"},
        "separator": "|",
    },
}


@pytest.mark.parametrize(
    "input_sequence,output",
    [
        # Empty file remains empty.
        (("",), ""),
        # Just an empty line
        (("\n",), "\n"),
        # Two empty lines
        (("\n\n",), "\n\n"),
        # One line
        (("a\n",), "a\n"),
        # One line followed by empty line
        (("a\n\n",), "a\n\n"),
        # Two lines
        (("a\nb\n",), "a\nb\n"),
        # A line with "a" or a line with "b" (no level1)
        (
            (Change("a\n", "b\n"),),
            "< x\na\n[i]=\n[f]b\n> y\n",
        ),
        (
            (
                "a\n",
                Change(
                    ("b", Change("c", ""), "\n"),
                    ("d", Change("", "e"), "\n"),
                ),
                "f\n",
            ),
            "a\n< x\nb<c>|\n[i]=\n[f]d|[e]\n> y\nf\n",
        ),
    ],
)
def test_markup_changes(input_sequence, output):
    output_buffer = io.StringIO()

    markup_changes(
        output_buffer.write,
        input_sequence,
        TEST_DIFF_MARKUP["level0"],
        TEST_DIFF_MARKUP["level1"],
        "x",
        "y",
    )

    assert output_buffer.getvalue() == output


@pytest.mark.parametrize(
    "input_sequence,output",
    [
        # Empty file remains empty.
        (("",), ""),
        (("a\n",), "A\n"),
        (
            (Change("a\n", "b\n"),),
            "< x\nA\n[i]=\n[f]B\n> y\n",
        ),
        (
            (
                "a\n",
                Change(
                    ("b", Change("c", ""), "\n"),
                    ("d", Change("", "e"), "\n"),
                ),
                "f\n",
            ),
            "A\n< x\nB<C>|\n[i]=\n[f]D|[E]\n> y\nF\n",
        ),
    ],
)
def test_markup_changes_applies_escape(input_sequence, output):
    output_buffer = io.StringIO()

    markup_changes(
        output_buffer.write,
        input_sequence,
        TEST_DIFF_MARKUP["level0"],
        TEST_DIFF_MARKUP["level1"],
        "x",
        "y",
        escape=str.upper,
    )

    assert output_buffer.getvalue() == output
