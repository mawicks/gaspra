import pytest
import io
from itertools import chain


from gaspra.markup import line_oriented_markup_changes, token_oriented_markup_changes
from gaspra.types import Change
from gaspra.tokenizers import NullTokenizer

TEST_MARKUP = {
    "fragment": {
        "into": {"prefix": "", "suffix": ""},
        "from": {"prefix": "", "suffix": ""},
    },
    "line": {
        "into": {"prefix": lambda s: f"< {s}\n", "suffix": lambda _: ""},
        "from": {"prefix": lambda _: "", "suffix": lambda s: f"> {s}\n"},
    },
    "escape": lambda _: _,
    "separator": "=\n",
    "header": {"prefix": "|", "suffix": "|"},
}

TEST_TOKEN_MARKUP = {
    "into": {"prefix": lambda s: f"< {s}\n", "suffix": lambda _: None},
    "from": {"prefix": lambda _: None, "suffix": lambda s: f"> {s}\n"},
    "escape": lambda _: _,
    "separator": "=\n",
    "header": {"prefix": "|", "suffix": "|"},
}


@pytest.mark.parametrize(
    ["input_sequence", "output"],
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
        # A line with "a" or a line with "b"
        ((("a", "b"), "\n"), "< x\na\n=\nb\n> y\n"),
        # Same thing written diferently
        ((("a\n", "b\n"),), "< x\na\n=\nb\n> y\n"),
        # Previous case with an extra newline.
        ((("a\n", "b\n"), "\n"), "< x\na\n=\nb\n> y\n\n"),
        # A line with "ab" or a line with "ac"
        (("a", ("b", "c"), "\n"), "< x\nab\n=\nac\n> y\n"),
        # Same thing written diferently
        (("a", ("b\n", "c\n")), "< x\nab\n=\nac\n> y\n"),
        # Line with "a" deleted in alternate followed by "b".
        ((("a\n", ""), "b\n"), "< x\na\n=\n> y\nb\n"),
        # Same with reversed directions.
        ((("", "a\n"), "b\n"), "< x\n=\na\n> y\nb\n"),
        # "a" line followed by "b" or "c" lines
        (
            (
                "a\n",
                ("b\n", "c\n"),
            ),
            "a\n< x\nb\n=\nc\n> y\n",
        ),
        # Conflict in the middle of a line (abd | acd).
        (("a", ("b", "c"), "d\n"), "< x\nabd\n=\nacd\n> y\n"),
        # Two conflicts with one line between them. There was
        # a bug that needed two lines to trigger it:
        #
        (
            ("a\n", ("b\n", "c\n"), "d\n", ("e\n", "f\n")),
            "a\n< x\nb\n=\nc\n> y\nd\n< x\ne\n=\nf\n> y\n",
        ),
        # Two conflicts with two lines between them:
        #
        (
            ("a\n", ("b\n", "c\n"), "d\ne\n", ("f\n", "g\n")),
            "a\n< x\nb\n=\nc\n> y\nd\ne\n< x\nf\n=\ng\n> y\n",
        ),
        # Two conflicts with three lines between them:
        #
        (
            ("a\n", ("b\n", "c\n"), "d\ne\nf\n", ("g\n", "h\n")),
            "a\n< x\nb\n=\nc\n> y\nd\ne\nf\n< x\ng\n=\nh\n> y\n",
        ),
        #
        # Two conflicts in the same line
        (("a", ("b", "c"), "d", ("e", "f"), "g\n"), "< x\nabdeg\n=\nacdfg\n> y\n"),
        #
        # Malformed files without newlines.
        (("a",), "a\n"),
        (("a", ("c", "d")), "< x\nac\n=\nad\n> y\n"),
        (("a", ("c", "")), "< x\nac\n=\na\n> y\n"),
        ((("a", "b"),), "< x\na\n=\nb\n> y\n"),
    ],
)
def test_line_oriented_markup_changes(input_sequence, output):
    output_buffer = io.StringIO()

    # It's important to use a tokenizer with a hard-coded
    # encoding/decoding.  We don't encode() so we can't
    # dynamically determine the encoding.

    tokenizer = NullTokenizer()

    line_oriented_markup_changes(
        output_buffer.write,
        input_sequence,
        "x",
        "y",
        tokenizer,
        markup=TEST_MARKUP,
        header="",
    )

    assert output_buffer.getvalue() == output


@pytest.fixture
def token_map():
    _token_map = tuple(chain(("",), "abcdefg"))
    return _token_map


@pytest.mark.parametrize(
    ["input_sequence", "output"],
    [
        # Empty file remains empty.
        ([()], ""),
        # Just an empty line
        ([(0,)], "\n"),
        # Two empty lines
        ([(0, 0)], "\n\n"),
        # One non-empty line
        ([(1,)], "a\n"),
        # One non-empty line followed by empty line
        ([(1, 0)], "a\n\n"),
        # Two non-empty lines
        ([(1, 2)], "a\nb\n"),
        # A line with "a" or a line with "b"
        (
            [
                Change((1,), (2,)),
            ],
            "< x\na\n=\nb\n> y\n",
        ),
        # Previous case with an extra newline.
        (
            [
                Change((1,), (2,)),
                (0,),
            ],
            "< x\na\n=\nb\n> y\n\n",
        ),
        # Line with "a" deleted in alternate followed by "b".
        (
            [
                Change((1,), ()),
                (2,),
            ],
            "< x\na\n=\n> y\nb\n",
        ),
        # Same with reversed directions.
        (
            [
                Change((), (1,)),
                (2,),
            ],
            "< x\n=\na\n> y\nb\n",
        ),
        # "a" line followed by "b" or "c" lines
        (
            (
                (1,),
                Change((2,), (3,)),
            ),
            "a\n< x\nb\n=\nc\n> y\n",
        ),
        # Two conflicts with one line between them.
        #
        (
            (
                (1,),
                Change((2,), (3,)),
                (4,),
                Change((5,), (6,)),
            ),
            "a\n< x\nb\n=\nc\n> y\nd\n< x\ne\n=\nf\n> y\n",
        ),
        # Two conflicts with two lines between them.
        #
        (
            (
                (1,),
                Change((2,), (3,)),
                (4,),
                (5,),
                Change((6,), (7,)),
            ),
            "a\n< x\nb\n=\nc\n> y\nd\ne\n< x\nf\n=\ng\n> y\n",
        ),
    ],
)
def test_token_oriented_markup_changes(input_sequence, output, token_map):
    output_buffer = io.StringIO()

    token_oriented_markup_changes(
        output_buffer.write,
        tuple(input_sequence),
        "x",
        "y",
        markup=TEST_TOKEN_MARKUP,
        header="",
        tokenizer=token_map,
    )

    assert output_buffer.getvalue() == output
