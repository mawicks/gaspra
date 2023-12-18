import random

from typing import Literal

import pytest


from string_matching.changesets import apply_forward, apply_reverse, find_changeset

from helpers.random_strings import random_string


@pytest.mark.parametrize(
    "s1,s2",
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
    ],
)
def test_find_changesets_and_apply_reproduces_string(s1: str, s2: str):
    changeset = find_changeset(s1, s2)

    assert s2 == apply_forward(changeset, s1)
    assert s1 == apply_reverse(changeset, s2)