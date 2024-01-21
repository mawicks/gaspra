import pytest

from helpers.helpers import encode


@pytest.mark.parametrize(
    "test_input,expected",
    [
        # Individual strings
        ("", ()),
        ("a", (97,)),
        ("ab", (97, 98)),
        # Sequences of strings
        (("a", "b"), ((97,), (98,))),
        (["a", "b"], ((97,), (98,))),
        # Sequence of [strings or sequences of strings]
        ((("a", "b"),), (((97,), (98,)),)),
        ([("a", "b")], (((97,), (98,)),)),
        (("c", ("a", "b")), ((99,), ((97,), (98,)))),
        (["c", ("a", "b")], ((99,), ((97,), (98,)))),
        (["c", ["a", "b"]], ((99,), ((97,), (98,)))),
    ],
)
def test_encode(test_input, expected):
    assert encode(test_input) == expected
