import pytest
from string_matching.merge import do_merge


# @pytest.mark.xfail
@pytest.mark.parametrize(
    ["parent", "branch1", "branch2", "merge"],
    [
        ("abcdefghij", "abxyzefghij", "abcdefgpqrij", "abxyzefgpqrij"),
        ("abcdefg", "abcxyz", "abcxyz", "abcxyz"),
    ],
)
def test_merge(parent, branch1, branch2, merge):
    assert do_merge(parent, branch1, branch2) == merge
