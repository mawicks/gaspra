import pytest
from string_matching.merge import do_merge


# @pytest.mark.xfail
@pytest.mark.parametrize(
    ["parent", "branch1", "branch2", "merge"],
    [
        ("", "", "", ""),
        ("", "a", "a", "a"),
        ("a", "", "", ""),
        ("a", "xa", "ay", "xay"),
        ("abcdefg", "abcxyz", "abcxyz", "abcxyz"),
        ("abcdefghij", "abxyzefghij", "abcdefgpqrij", "abxyzefgpqrij"),
    ],
)
def test_merge(parent, branch1, branch2, merge):
    assert do_merge(parent, branch1, branch2) == merge
