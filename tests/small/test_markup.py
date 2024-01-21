import pytest
import io
from itertools import chain

from gaspra.markup import (
    markup_changes,
)
from gaspra.types import Change
from gaspra.diff_to_lines import to_line_diff

TEST_MARKUP = {
    "fragment": {
        "into": {"prefix": "", "suffix": ""},
        "from": {"prefix": "", "suffix": ""},
    },
    "line": {
        "into": {"prefix": lambda s: f"< {s}\n", "suffix": lambda _: ""},
        "from": {"prefix": lambda _: "", "suffix": lambda s: f"> {s}\n"},
    },
    "separator": "=\n",
    "header": {"prefix": "|", "suffix": "|"},
}

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

TEST_TOKEN_MARKUP = {
    "into": {"prefix": lambda s: f"< {s}\n", "suffix": lambda _: None},
    "from": {"prefix": lambda _: None, "suffix": lambda s: f"> {s}\n"},
    "separator": "=\n",
    "header": {"prefix": "|", "suffix": "|"},
}


@pytest.fixture
def tokenizer():
    _token_map = tuple(chain(("",), "abcdefg"))

    # This is a hard-coded decoder with
    # 0 -> "\n"
    # 1 -> "a\n"
    # 2 -> "b\n", etc

    class _Tokenizer:
        def decode(self, content):
            return "".join((_token_map[token] + "\n") for token in content)

    return _Tokenizer()


@pytest.mark.parametrize(
    ["input_sequence", "output"],
    [
        # Empty file remains empty.
        (("",), ("",)),
        # Just an empty line
        (("\n",), ("\n",)),
        # Two empty lines
        (("\n\n",), ("\n\n",)),
        # One line
        (("a\n",), ("a\n",)),
        # One line followed by empty line
        (("a\n\n",), ("a\n\n",)),
        # Two lines
        (
            ("a\nb\n",),
            ("a\nb\n",),
        ),
        # A line with "a" or a line with "b"
        (
            (Change("a", "b"), "\n"),
            (
                Change(
                    (Change("a", ""), "\n"),
                    (Change("", "b"), "\n"),
                ),
            ),
        ),
        # Previous case with an extra newline.
        (
            (Change("a", "b"), "\n\n"),
            (
                Change(
                    (Change("a", ""), "\n\n"),
                    (Change("", "b"), "\n\n"),
                ),
            ),
        ),
        # A line with "ab" or a line with "ac"
        (
            ("a", Change("b", "c"), "\n"),
            (
                Change(
                    ("a", Change("b", ""), "\n"),
                    ("a", Change("", "c"), "\n"),
                ),
            ),
        ),
        # Line with "a" deleted in alternate followed by "b".
        (
            (Change("a\n", ""), "b\n"),
            (
                Change(
                    (Change("a\n", ""),),
                    (Change("", ""),),
                ),
                "b\n",
            ),
        ),
        # Same with reversed directions.
        (
            (Change("", "a\n"), "b\n"),
            (
                Change(
                    (Change("", ""),),
                    (Change("", "a\n"),),
                ),
                "b\n",
            ),
        ),
        # "a" line followed by "b" or "c" lines
        (
            ("a\n", Change("b", "c"), "\n"),
            (
                "a\n",
                Change(
                    (Change("b", ""), "\n"),
                    (Change("", "c"), "\n"),
                ),
            ),
        ),
        # Conflict in the middle of a line (abd | acd).
        (
            ("a", Change("b", "c"), "d\n"),
            (
                Change(
                    ("a", Change("b", ""), "d\n"),
                    ("a", Change("", "c"), "d\n"),
                ),
            ),
        ),
        # Two conflicts with one line between them. There was
        # a bug that needed two lines to trigger it:
        #
        (
            ("a\n", Change("b", "c"), "\nd\n", Change("e", "f"), "\n"),
            (
                "a\n",
                Change(
                    (Change("b", ""), "\n"),
                    (Change("", "c"), "\n"),
                ),
                "d\n",
                Change(
                    (Change("e", ""), "\n"),
                    (Change("", "f"), "\n"),
                ),
            ),
        ),
        # Two conflicts with two lines between them:
        #
        (
            ("a\n", Change("b", "c"), "\nd\ne\n", Change("f", "g"), "\n"),
            (
                "a\n",
                Change(
                    (Change("b", ""), "\n"),
                    (Change("", "c"), "\n"),
                ),
                "d\ne\n",
                Change(
                    (Change("f", ""), "\n"),
                    (Change("", "g"), "\n"),
                ),
            ),
        ),
        # Two conflicts with three lines between them:
        #
        (
            ("a\n", Change("b", "c"), "\nd\ne\nf\n", Change("g", "h"), "\n"),
            (
                "a\n",
                Change(
                    (Change("b", ""), "\n"),
                    (Change("", "c"), "\n"),
                ),
                "d\ne\nf\n",
                Change(
                    (Change("g", ""), "\n"),
                    (Change("", "h"), "\n"),
                ),
            ),
        ),
        #
        # Two conflicts in the same line
        (
            ("a", Change("b", "c"), "d", Change("e", "f"), "g\n"),
            (
                Change(
                    ("a", Change("b", ""), "d", Change("e", ""), "g\n"),
                    ("a", Change("", "c"), "d", Change("", "f"), "g\n"),
                ),
            ),
        ),
        # Newline in the middle of a conflict.
        (
            ("a", Change("b\nc", "d"), "\n"),
            (
                Change(
                    ("a", Change("b\nc", ""), "\n"),
                    ("a", Change("", "d"), "\n"),
                ),
            ),
        ),
        #
        # Malformed files without newlines.
        (
            ("a",),
            ("a\n",),
        ),
        (
            ("a", Change("c", "d")),
            (
                Change(
                    ("a", Change("c", ""), "\n"),
                    ("a", Change("", "d"), "\n"),
                ),
            ),
        ),
        (
            ("a", Change("c", "")),
            (
                Change(
                    ("a", Change("c", ""), "\n"),
                    ("a", Change("", ""), "\n"),
                ),
            ),
        ),
        (
            (Change("a", "b"),),
            (
                Change(
                    (Change("a", ""), "\n"),
                    (Change("", "b"), "\n"),
                ),
            ),
        ),
        # Two consecutive lines of changes should be consolidated.
        # "The newlines are considered  "common sequences"
        # by all tokenizers except the line tokenizer.
        (
            (Change("a", "b"), "\n", Change("c", "d"), "\n"),
            (
                Change(
                    (Change("a", ""), "\n", Change("c", ""), "\n"),
                    (Change("", "b"), "\n", Change("", "d"), "\n"),
                ),
            ),
        ),
    ],
)
def test_diff_to_lines(input_sequence, output):
    as_lines = tuple(_ for _ in to_line_diff(input_sequence))

    assert as_lines == output


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
