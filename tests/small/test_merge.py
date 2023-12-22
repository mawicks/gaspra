import pytest
from difftools.merge import merge


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
        # Yet another edge case.
        # Branch0: Delete "a"
        # Branch1: Insert "x" before "a"
        # Resolution: Insert "x" before "a" then delete "a".
        ("ab", "b", "xab", "xb"),
        #
        ("abcdefg", "abcxyz", "abcxyz", "abcxyz"),
        #
        ("abcdefghij", "abxyzefghij", "abcdefgpqrij", "abxyzefgpqrij"),
    ],
)
def test_merge(parent, branch1, branch2, merged):
    assert tuple(merge(parent, branch1, branch2)) == (merged,)


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
        #         Then accept insertion of "b" on Branch1
        # An alternate interpretation is
        # Branch0: "a" -> ""
        # Branch1: "a" -> "b" so conflict!
        # We're going with the second interpretation
        # and testing for this being a conflict.
        ("a", "", "b", [("", "b")]),
        (
            "abcdefg",
            "axdpefg",
            "abcdqey",
            ["axd", ("p", "q"), "ey"],
        ),
        ("ab", "xb", "yb", [("x", "y"), "b"]),
        ("ab", "b", "xb", [("", "x"), "b"]),
        #
        # This next set of tests focuses on factoring out common parts
        # of changes.
        # One interpretation of next case:
        # Branch0: spqe -> sxqe -> sxyqe (insert "y" between "x" and "q")
        # Branch1: spqe -> sxqe -> sxze (change "q" -> "z")
        # You could intrepet this as conflict-free resulting in "sxyze",
        # but that assumes the branch0 change came before the branch1
        # change.  They don't commute.  Reverseing the order, Where should
        # "y" go if "q" is absent?
        # The interpretation here is to accept branch1's
        # change: q->z, but to record a conflict in the order of "y" and "z"
        # since branch1 didn't see "y".  This conflict is clear if you
        # view q->z as non-atomic.  Consider it as two steps: deletion
        # of "q" followed by insertion of "z".  The branch1 author might
        # have removed "q" first to produce "sxe".  Merging this change
        # alone with branch0 would produce "sxye".  Now, branch1 inserts
        # "z" between "x" and "e", but should it come before or after "y"
        # in the merge? No doubt this is a conflict.
        # One could argue that "q" should also included in the
        # conflict, but we're taking the position that the replacement
        # q->z is conflict-free (i.e., "q" is gone).  The branch1 author
        # has enough context to make the decision to remove q, i.e., remove
        # "q" immediately before "e". It's only a question of where to
        # place "z".
        ("spqe", "sxyqe", "sxze", ("sx", ("y", "z"), "e")),
        # Same case with null "p"
        ("sqe", "sxyqe", "sxze", ("sx", ("y", "z"), "e")),
        # Same case with null "x" (making it a slightly different case)
        ("spqe", "syqe", "sze", ("s", ("y", "z"), "e")),
        # Same case with null "y" -- CHECK THIS!!!
        ("spqe", "sqe", "sze", ("s", ("", "z"), "e")),
    ],
)
def test_merge_conflict(parent, branch1, branch2, merged):
    # For now, we only testing that the test cases have
    # some kind of merge conflict, not specifically what that is.
    result = merge(parent, branch1, branch2)
    assert tuple(merged) == tuple(result)
