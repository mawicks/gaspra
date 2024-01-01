import pytest


from gaspra.changesets import (
    old_apply_forward,
    old_apply_reverse,
    diff,
    find_changeset,
    apply_forward,
    apply_reverse,
)
from gaspra.test_helpers.helpers import random_string, tokenize
from gaspra.types import Change


FIND_CHANGESETS_STRING_CASES = [
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
]

FIND_CHANGESETS_BYTES_CASES = [
    (s1.encode("utf-8"), s2.encode("utf-8")) for s1, s2 in FIND_CHANGESETS_STRING_CASES
]

FIND_CHANGESETS_TOKEN_CASES = [
    (tokenize(s1), tokenize(s2)) for s1, s2 in FIND_CHANGESETS_STRING_CASES
]


@pytest.mark.parametrize(
    ["s1", "s2"],
    [
        *FIND_CHANGESETS_STRING_CASES,
        *FIND_CHANGESETS_BYTES_CASES,
        *FIND_CHANGESETS_TOKEN_CASES,
    ],
)
def test_find_changesets_and_apply_forward_reproduces_string(s1: str, s2: str):
    changeset = find_changeset(s1, s2)
    assert s2 == old_apply_forward(changeset, s1)


@pytest.mark.parametrize(
    ["s1", "s2"],
    [
        *FIND_CHANGESETS_STRING_CASES,
        *FIND_CHANGESETS_BYTES_CASES,
        *FIND_CHANGESETS_TOKEN_CASES,
    ],
)
def test_find_changesets_and_alt_apply_forward_reproduces_string(s1: str, s2: str):
    changeset = find_changeset(s1, s2)
    alt_changeset = changeset.reduce()
    assert s2 == apply_forward(alt_changeset, s1)


@pytest.mark.parametrize(
    ["s1", "s2"],
    [
        *FIND_CHANGESETS_STRING_CASES,
        *FIND_CHANGESETS_BYTES_CASES,
        *FIND_CHANGESETS_TOKEN_CASES,
    ],
)
def test_find_changesets_and_apply_reverse_reproduces_string(s1: str, s2: str):
    changeset = find_changeset(s1, s2)
    assert s1 == old_apply_reverse(changeset, s2)


@pytest.mark.parametrize(
    ["s1", "s2"],
    [
        *FIND_CHANGESETS_STRING_CASES,
        *FIND_CHANGESETS_BYTES_CASES,
        *FIND_CHANGESETS_TOKEN_CASES,
    ],
)
def test_find_changesets_and_alt_apply_reverse_reproduces_string(s1: str, s2: str):
    changeset = find_changeset(s1, s2)
    reduced_changeset = list(changeset.reduce())
    assert s1 == apply_reverse(reduced_changeset, s2)


# We use "named" tuples for the "diffs" in the sequence so that we can
# easily which tuples are diffs and which are sequences of tokens.  Make
# sure the tuples that should be named are named.  For the string case,
# *all* tuples should named.  When the token sequence is provided as a
# tuple, only the change tuples would be named.  Since it's difficult to
# identify the "right" answer in the tuple of tokens case, we check only
# the string/bytstring cases.  The token case uses exactly the same
# code, so if the named tuples are in the right place when processing
# strings, they should also be in the right place when processing
# tokens.


@pytest.mark.parametrize(
    ["s1", "s2"],
    [
        *FIND_CHANGESETS_STRING_CASES,
        *FIND_CHANGESETS_BYTES_CASES,
    ],
)
def test_all_string_changeset_tuples_are_typed(s1: str, s2: str):
    diffed = diff(s1, s2)
    assert all(
        isinstance(change, Change) or type(change) in (bytes, str) for change in diffed
    )
