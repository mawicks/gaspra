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
        (("",), "\n"),
        (("\n",), "\n"),
        (("\n\n",), "\n\n"),
        (("a\n",), "a\n"),
        (("a\n\n",), "a\n\n"),
        (("a\nb\n",), "a\nb\n"),
        (("a", ("c\n", "d\n")), "< x\nac\n=\nad\n> y\n"),
        (("a", ("c", "d"), "\n"), "< x\nac\n=\nad\n> y\n"),
        ((("a\n", ""), "b\n"), "< x\na\n=\n> y\nb\n"),
        #
        #
        #
        # Degenerate files without newlines.
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
