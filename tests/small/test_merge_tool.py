import pytest
import io


from gaspra.merge_tool import show_changes_line_oriented

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
        # a bug that took two lines to trigger.
        #
        (
            ("a\n", ("b\n", "c\n"), "d\n", ("e\n", "f\n")),
            "a\n< x\nb\n=\nc\n> y\nd\n< x\ne\n=\nf\n> y\n",
        ),
        # Two conflicts with two lines between them.
        #
        (
            ("a\n", ("b\n", "c\n"), "d\ne\n", ("f\n", "g\n")),
            "a\n< x\nb\n=\nc\n> y\nd\ne\n< x\nf\n=\ng\n> y\n",
        ),
        # Two conflicts with three lines between them.
        #
        (
            ("a\n", ("b\n", "c\n"), "d\ne\nf\n", ("g\n", "h\n")),
            "a\n< x\nb\n=\nc\n> y\nd\ne\nf\n< x\ng\n=\nh\n> y\n",
        ),
        #
        # Malformed files without newlines.
        (("a",), "a\n"),
        (("a", ("c", "d")), "< x\nac\n=\nad\n> y\n"),
        (("a", ("c", "")), "< x\nac\n=\na\n> y\n"),
        ((("a", "b"),), "< x\na\n=\nb\n> y\n"),
    ],
)
def test_show_changes_line_oriented(input_sequence, output):
    output_buffer = io.StringIO()

    show_changes_line_oriented(
        output_buffer.write,
        input_sequence,
        "x",
        "y",
        markup=TEST_MARKUP,
        header="",
    )

    assert output_buffer.getvalue() == output