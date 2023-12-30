from collections.abc import Sequence

from gaspra.test_helpers.helpers import tokenize

import pytest


from gaspra.multiple_strings import find_lcs, concatenate_strings
from gaspra.types import Separator


def test_concatenate_strings():
    concatenation = list(concatenate_strings(["ab", "cd", "ef"]))

    assert concatenation == [
        "a",
        "b",
        Separator(0),
        "c",
        "d",
        Separator(1),
        "e",
        "f",
        Separator(2),
    ]


def test_concatenate_strings_on_tokens():
    concatenation = list(concatenate_strings([(1, 2), (3, 4), (5, 6)]))

    assert concatenation == [1, 2, Separator(0), 3, 4, Separator(1), 5, 6, Separator(2)]


MULTIPLE_STRING_TEST_CASES = [
    ((), (), None),
    (("", ""), (0, 0), 0),
    (("", "abc"), (0, 0), 0),
    (("abc", ""), (0, 0), 0),
    (("abc", "abc"), (0, 0), 3),
    (("abc", "abcdef"), (0, 0), 3),
    (("abcdef", "def"), (3, 0), 3),
    (("abc", "xbc", "bcxy"), (1, 1, 0), 2),
    (("abcd", "bcdax", "yzbcd"), (1, 0, 2), 3),
]
MULTIPLE_TOKEN_TEST_CASES = [
    (tokenize(string_set), start_positions, length)
    for string_set, start_positions, length in MULTIPLE_STRING_TEST_CASES
]


@pytest.mark.parametrize(
    ["string_set", "start_positions", "length"],
    [
        *MULTIPLE_STRING_TEST_CASES,
        *MULTIPLE_TOKEN_TEST_CASES,
    ],
)
def test_find_lcs_of_multiple_strings(
    string_set: Sequence[str], start_positions, length
):
    assert (start_positions, length) == find_lcs(*string_set)
