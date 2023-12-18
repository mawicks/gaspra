from collections.abc import Sequence

import pytest


from string_matching.multiple_strings import find_lcs, concatenate_strings


@pytest.mark.parametrize(
    "string_set,expected_start_position,expected_length",
    [
        ((), 0, 0),
        (("", ""), 0, 0),
        (("", "abc"), 0, 0),
        (("abc", ""), 0, 0),
        (("abc", "abc"), 0, 3),
        (("abc", "abcdef"), 0, 3),
        (("abcdef", "def"), 3, 3),
        (("abc", "xbc", "bcxy"), 1, 2),
        (("abcd", "bcdax", "yzbcd"), 1, 3),
    ],
)
def test_find_lcs_of_multiple_strings(
    string_set: Sequence[str], expected_start_position, expected_length
):
    start_position, length = find_lcs(string_set)

    assert start_position == expected_start_position
    assert length == expected_length


def test_concatenate_strings():
    concatenation = list(concatenate_strings(["ab", "cd", "ef"]))

    assert concatenation == ["a", "b", "$0", "c", "d", "$1", "e", "f", "$2"]
