import pytest


from gaspra.changesets import apply_forward, apply_reverse, find_changeset
from gaspra.test_helpers.helpers import random_string


@pytest.mark.parametrize(
    ["s1", "s2"],
    [
        ("", ""),
        ("abcabcabc", ""),
        ("", "abxybcabcx"),
        ("abcabcabc", "abcabcabcxyz"),
        ("abcabcabc", "xyzabcabcabc"),
        ("abcabcabc", "abxybcabcx"),
        (
            random_string("abcdef", 51),
            random_string("abcdef", 53),
        ),
        ((), ()),
        ((1, 2, 3, 1, 2, 3, 1, 2, 3), ()),
    ],
)
def test_find_changesets_and_apply_reproduces_string(s1: str, s2: str):
    changeset = find_changeset(s1, s2)

    assert s2 == apply_forward(changeset, s1)
    assert s1 == apply_reverse(changeset, s2)
