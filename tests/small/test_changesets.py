import pytest


from gaspra.changesets import apply_forward, apply_reverse, diff, find_changeset
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
    assert s2 == apply_forward(changeset, s1)


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
    assert s1 == apply_reverse(changeset, s2)


# We use "named" tuples for the "diffs" in the sequence so that we can
# easily which tuples are diffs and which are sequences of tokens.  Make
# sure the tuples that should be named are named.  For the string case,
# all tuples should named.  For the token case, it's ambigious, so we
# check only the string case.  The token case uses exactly the same
# code, so if the named tuples are in the right place when processing
# strings, they should also be in the right place when processing
# tokens.


@pytest.mark.parametrize(
    ["s1", "s2"],
    FIND_CHANGESETS_STRING_CASES,
)
def test_all_string_changeset_tuples_are_typed(s1: str, s2: str):
    diffed = diff(s1, s2)
    assert all(
        isinstance(change, Change) or isinstance(change, str) for change in diffed
    )
