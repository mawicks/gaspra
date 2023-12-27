from collections.abc import Sequence

from gaspra.test_helpers.helpers import tokenize

import pytest


from gaspra.multiple_strings import find_lcs, concatenate_strings


def test_concatenate_strings():
    concatenation = list(concatenate_strings(["ab", "cd", "ef"]))

    assert concatenation == ["a", "b", "$0", "c", "d", "$1", "e", "f", "$2"]


def test_concatenate_strings_on_tokens():
    concatenation = list(concatenate_strings([(1, 2), (3, 4), (5, 6)]))

    assert concatenation == [1, 2, "$0", 3, 4, "$1", 5, 6, "$2"]


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
        ((), (), None),
        (("", ""), (0, 0), 0),
        (("", "abc"), (0, 0), 0),
        (("abc", ""), (0, 0), 0),
        (("abc", "abc"), (0, 0), 3),
        (("abc", "abcdef"), (0, 0), 3),
        (("abcdef", "def"), (3, 0), 3),
        (("abc", "xbc", "bcxy"), (1, 1, 0), 2),
        (("abcd", "bcdax", "yzbcd"), (1, 0, 2), 3),
        (((), ()), (0, 0), 0),
        (((), (1, 2, 3)), (0, 0), 0),
        (((1, 2, 3), ()), (0, 0), 0),
        (((1, 2, 3), (1, 2, 3)), (0, 0), 3),
        (((1, 2, 3), (1, 2, 3, 4, 5)), (0, 0), 3),
        (((1, 2, 3, 4, 5, 6), (4, 5, 6)), (3, 0), 3),
        (((1, 2, 3), (4, 2, 3), (2, 3, 4, 5)), (1, 1, 0), 2),
        (((1, 2, 3, 4), (2, 3, 4, 1, 5), (6, 7, 2, 3, 4)), (1, 0, 2), 3),
    ],
)
def test_find_lcs_of_multiple_strings(
    string_set: Sequence[str], start_positions, length
):
    assert (start_positions, length) == find_lcs(*string_set)
