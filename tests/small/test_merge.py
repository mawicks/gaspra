import pytest
from string_matching.merge import do_merge


# @pytest.mark.xfail
@pytest.mark.parametrize(
    ["parent", "branch1", "branch2", "merge"],
    [
        # No changes, all empty
        ("", "", "", ""),
        # No changes, non-empty
        ("a", "a", "a", "a"),
        # Same change from empty
        ("", "a", "a", "a"),
        # Remove everything on both branches
        ("a", "", "", ""),
        # Insert at beginning and end on different branches.
        ("a", "xa", "ay", "xay"),
        # Insert at beginning and deletion at end.
        ("ab", "xab", "a", "xa"),
        # Adjacent deletions which result in removing everything.
        ("ab", "b", "a", ""),
        # Should this be a conflict case?  It's definitely
        # an edge case, but handle it this way:  Inserting
        # token 'x' on one branch just before a token 'a' that was
        # deleted on the other branch leaves the inerted token
        # 'x' at the position where 'a' would have been.
        ("a", "xa", "", "x"),
        # A slightly more interpreable variation
        # Branch 0 says, "insert 'x' after the '.'"
        # Branch 1 says, "remove "a".  The merge is interpreted
        # to be "insert 'x' after the '.', then remove 'a'
        (".a", ".xa", ".", ".x"),
        ("abcdefg", "abcxyz", "abcxyz", "abcxyz"),
        ("abcdefghij", "abxyzefghij", "abcdefgpqrij", "abxyzefgpqrij"),
    ],
)
def test_merge(parent, branch1, branch2, merge):
    assert do_merge(parent, branch1, branch2) == merge
