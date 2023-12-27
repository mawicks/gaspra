import pytest
import io


from gaspra.markup import line_oriented_markup_changes, token_oriented_markup_changes
from gaspra.types import Difference

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
    "into": {"prefix": lambda s: f"< {s}", "suffix": lambda _: None},
    "from": {"prefix": lambda _: None, "suffix": lambda s: f"> {s}"},
    "escape": lambda _: _,
    "separator": "=",
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
        # A line with "ab" or a line with "bc"
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
        # Two conflict in the same line
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

    line_oriented_markup_changes(
        output_buffer.write,
        input_sequence,
        "x",
        "y",
        markup=TEST_MARKUP,
        header="",
    )

    assert output_buffer.getvalue() == output


@pytest.fixture
def token_dict():
    return {
        0: "",
        1: "a",
        2: "b",
        3: "c",
        4: "d",
        5: "e",
    }


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
                Difference((1,), (2,)),
            ],
            "< x\na\n=\nb\n> y\n",
        ),
        # Previous case with an extra newline.
        (
            [
                Difference((1,), (2,)),
                (0,),
            ],
            "< x\na\n=\nb\n> y\n\n",
        ),
    ],
)
def test_token_oriented_markup_changes(input_sequence, output, token_dict):
    output_buffer = io.StringIO()

    def writer(s):
        output_buffer.write(s)
        output_buffer.write("\n")

    token_oriented_markup_changes(
        writer,
        tuple(input_sequence),
        token_dict,
        "x",
        "y",
        markup=TEST_TOKEN_MARKUP,
        header="",
    )

    assert output_buffer.getvalue() == output
