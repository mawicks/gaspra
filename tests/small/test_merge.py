import pytest
from string_matching.merge import merge


# @pytest.mark.xfail
@pytest.mark.parametrize(
    ["parent", "branch1", "branch2", "merged"],
    [
        # No changes, all empty
        ("", "", "", ""),
        #
        # No changes, non-empty
        ("a", "a", "a", "a"),
        #
        # Same change both branches, beginning from empty
        ("", "a", "a", "a"),
        #
        # Remove everything on both branches
        ("a", "", "", ""),
        #
        # Remove everything on one branch, do nothing on the other.
        ("a", "", "a", ""),
        #
        # Beginning empty, insert on one branch, do nothing on the other.
        ("", "a", "", "a"),
        #
        # Beginning non-empty, Insert on one branch, do nothing on the other.
        ("a", "ax", "a", "ax"),
        #
        # Beginning non-empty, delete on one branch, do nothing on the other.
        ("ax", "a", "ax", "a"),
        #
        # Insert at beginning and end on different branches.
        ("a", "xa", "ay", "xay"),
        #
        # Delete at beginning and end on different branches.
        ("abc", "bc", "ab", "b"),
        #
        # Insert at beginning and deletion at end.
        ("ab", "xab", "a", "xa"),
        #
        # Adjacent deletions which result in removing everything.
        ("ab", "b", "a", ""),
        #
        # Should this be a conflict case?  It's definitely
        # an edge case, but handle it this way:  Inserting
        # token 'x' on one branch just before a token 'a' that was
        # deleted on the other branch leaves the inerted token
        # 'x' at the position where 'a' would have been.
        ("a", "xa", "", "x"),
        #
        # A slightly more interpreable variation
        # Branch 0 says, "insert 'x' after the '.'"
        # Branch 1 says, "remove "a".  The merge is interpreted
        # to be "insert 'x' after the '.', then remove 'a'
        (".a", ".xa", ".", ".x"),
        #
        # This is another edge case.  The correct interpretation is
        # Branch0: Insert "b" after "a"
        # Branch1: Change "a" -> "x"
        # Result "xb"
        ("a", "ab", "x", "xb"),
        #
        #
        ("abcdefg", "abcxyz", "abcxyz", "abcxyz"),
        #
        ("abcdefghij", "abxyzefghij", "abcdefgpqrij", "abxyzefgpqrij"),
    ],
)
def test_merge(parent, branch1, branch2, merged):
    assert merge(parent, branch1, branch2)[0] == merged


@pytest.mark.parametrize(
    ["parent", "branch1", "branch2", "merged"],
    [
        ("", "a", "b", [("a", "b")]),
        #
        # Another questionable case:
        # One interpretation is
        # Branch0: Delete "a"
        # Branch1: Delete "a", then insert "b"
        # Result: Branches both want to delete "a" so accept that.
        # An alternate interpretation is
        # Branch0: "a" -> ""
        # Branch1: "a" -> "b" so conflict!
        # We're going with the second interpretation
        # and testing for this being a conflict.
        ("a", "", "b", [("", "b")]),
    ],
)
def test_merge_conflict(parent, branch1, branch2, merged):
    # For now, we only testing that the test cases have
    # some kind of merge conflict, not specifically what that is.
    result = merge(parent, branch1, branch2)
    assert tuple(merged) == tuple(result)
