import pytest

from copy import deepcopy

from gaspra.revision_tree import Tree

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
INSERTED_EDGES = (
    (),
    (("b", "a"),),
    (("c", "b"), ("c", "a")),
    (("z", "c"), ("z", "b")),
    (("x", "z"), ("x", "c")),
    (("y", "x"), ("y", "z")),
    (("q", "y"), ("q", "c")),
)
REMOVED_EDGES = (
    (),
    (),
    (("b", "a"),),
    (("c", "b"),),
    (("z", "c"),),
    (("x", "z"),),
    (("x", "c"),),
)


def test_add_revision():
    test_tree = Tree()

    for node_tag, tree, inserted_edges, removed_edges in zip(
        NODE_TAGS, TREES, INSERTED_EDGES, REMOVED_EDGES
    ):
        edges = {edge for edge in tree}
        inserted_edges = {edge for edge in inserted_edges}
        removed_edges = {edge for edge in removed_edges}

        test_inserted_edges, test_removed_edges = test_tree.insert(node_tag)
        test_inserted_edges = {edge for edge in test_inserted_edges}
        test_removed_edges = {edge for edge in test_removed_edges}

        assert edges == {edge for edge in test_tree.edges()}

        # Check that inserted_edges and removed edges are as expected.
        # These are tested more extensively in
        # test_inserted_and_removed_edges_agree_with_edges()
        assert test_inserted_edges == inserted_edges
        assert test_removed_edges == removed_edges


@pytest.fixture
def tree():
    fixture_tree = Tree()
    for node in NODE_TAGS:
        fixture_tree.insert(node)
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


def test_inserted_and_removed_edges_agree_with_edges():
    tree = Tree()
    accumulated_edges = set()
    for node in NODE_TAGS:
        inserted_edges, removed_edges = tree.insert(node)
        accumulated_edges.update(inserted_edges)
        accumulated_edges.difference_update(removed_edges)

        assert set(tree.edges()) == accumulated_edges


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
