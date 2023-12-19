from collections.abc import Sequence

import pytest


from string_matching.multiple_strings import find_lcs, concatenate_strings


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
    ],
)
def test_find_lcs_of_multiple_strings(
    string_set: Sequence[str], start_positions, length
):
    assert (start_positions, length) == find_lcs(string_set)


def test_concatenate_strings():
    concatenation = list(concatenate_strings(["ab", "cd", "ef"]))

    assert concatenation == ["a", "b", "$0", "c", "d", "$1", "e", "f", "$2"]
