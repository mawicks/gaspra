import pytest

from copy import deepcopy

from gaspra.revisions import Tree

# These are intentially not in alphabetical order to make
# sure the tree doesn't depend on ordering in some way
# The list of trees is shorter but matches what should be
# expected after adding the first seven NODE_TAGS.
# These are zipped together for the only test that looks for
# specific trees.  For the other tests, which test tree properties,
# we use the full set of NODE_TAGS.
NODE_TAGS = ("a", "b", "c", "z", "x", "y", "q", "r", "s", "t")
TREES = (
    (),
    (("b", "a"),),
    (("c", "b"), ("c", "a")),
    (("z", "c"), ("z", "b"), ("c", "a")),
    (("x", "z"), ("x", "c"), ("z", "b"), ("c", "a")),
    (("y", "x"), ("y", "z"), ("x", "c"), ("z", "b"), ("c", "a")),
    (("q", "y"), ("q", "c"), ("y", "x"), ("y", "z"), ("z", "b"), ("c", "a")),
)


def test_add_revision():
    tree = Tree()

    for node_tag, expected_tree in zip(NODE_TAGS, TREES):
        test_edges = {edge for edge in expected_tree}

        tree.add(node_tag)
        assert test_edges == {edge for edge in tree.edges()}


@pytest.fixture
def tree():
    fixture_tree = Tree()
    for node in NODE_TAGS:
        fixture_tree.add(node)
    return fixture_tree


def test_all_paths_lead_to_root(tree):
    for node_name in NODE_TAGS:
        path = tree.path_to(node_name)
        assert len(path) > 0
        assert path[0] == NODE_TAGS[-1]
        assert path[-1] == node_name


def test_reevaluate(tree):
    tree_copy = deepcopy(tree)
    tree_copy._invalidate()
    tree_copy.reevaluate()
    for node_name in NODE_TAGS:
        original_state = tree._get_state(node_name)
        new_state = tree_copy._get_state(node_name)
        assert original_state == new_state


def test_revision_tree_properties(tree):
    # Check that each node is in the tree and has nore more than one
    # parent.
    present_nodes = set()
    parent_counts = {}
    for edge in tree.edges():
        present_nodes.update(edge)
        child = edge[1]
        parent_counts[child] = parent_counts.get(child, 0) + 1

    orphan_count = 0
    for node in NODE_TAGS:
        # All inserted nodes should be present in the tree
        assert node in present_nodes

        # All nodes should have no more than one parent
        assert parent_counts.get(node, 0) <= 1

        if node not in parent_counts:
            orphan_count += 1

    # There should be exactly one orphan node in the tree (the root)
    assert orphan_count == 1
