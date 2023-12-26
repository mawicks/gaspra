import pytest
import io


from gaspra.merge_tool import show_changes_line_oriented, GIT_MARKUP


@pytest.mark.parametrize(
    ["input_sequence", "output"],
    [
        (("",), "\n"),
        (("\n",), "\n"),
        (("\n\n",), "\n\n"),
        (("a",), "a\n"),
        (("a\n",), "a\n"),
        (("a\n\n",), "a\n\n"),
        (("a\nb\n",), "a\nb\n"),
        (("a", ("c", "d")), "<<<<<<< x\nac\n=======\nad\n>>>>>>> y\n"),
        (("a", ("c", "")), "<<<<<<< x\nac\n=======\na\n>>>>>>> y\n"),
        ((("a", "b"),), "<<<<<<< x\na\n=======\nb\n>>>>>>> y\n"),
    ],
)
def test_show_changes_line_oriented(input_sequence, output):
    output_buffer = io.StringIO()

    show_changes_line_oriented(
        output_buffer.write,
        input_sequence,
        "x",
        "y",
        markup=GIT_MARKUP,
        header="",
    )

    assert output_buffer.getvalue() == output
