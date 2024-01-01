import pytest

from gaspra.common import common_prefix_length


@pytest.mark.parametrize(
    "s1, s2, length",
    [
        ("", "", 0),
        ("", "a", 0),
        ("x", "y", 0),
        ("xy", "yz", 0),
        ("a", "a", 1),
        ("ab", "ab", 2),
        ("ab", "ac", 1),
        ("abc", "abd", 2),
        ("abcd", "abde", 2),
    ],
)
def test_common_prefix_length(s1, s2, length):
    assert common_prefix_length(s1, s2) == length
