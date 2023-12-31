import pytest

from gaspra.revisions import Tree

TREES = (
    (),
    ((1, 0),),
    ((2, 1), (2, 0)),
    ((3, 2), (3, 1), (2, 0)),
    ((4, 3), (4, 2), (3, 1), (2, 0)),
    ((5, 4), (5, 3), (4, 2), (3, 1), (2, 0)),
    ((6, 5), (6, 2), (5, 4), (5, 3), (3, 1), (2, 0)),
)


def test_add_revision():
    tree = Tree()

    for node, expected_tree in enumerate(TREES):
        test_edges = {edge for edge in expected_tree}

        tree.add(node)
        assert test_edges == {edge for edge in tree.edges()}


TREE_FIXTURE_SIZE = 10


@pytest.fixture
def tree():
    fixture_tree = Tree()
    for node in range(TREE_FIXTURE_SIZE):
        fixture_tree.add(node)
    return fixture_tree


def test_all_nodes_are_indexed(tree):
    for node_id in range(TREE_FIXTURE_SIZE):
        found = tree.find(node_id)
        assert found is not None and found.node_id == node_id


def test_all_paths_lead_to_root(tree):
    for node_id in range(TREE_FIXTURE_SIZE):
        current = tree.find(node_id)
        while current.parent is not None:
            current = current.parent
        assert current is not None and current.node_id == TREE_FIXTURE_SIZE - 1


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
    for node in range(TREE_FIXTURE_SIZE):
        # All inserted nodes should be present in the tree
        assert node in present_nodes

        # All nodes should have no more than one parent
        assert parent_counts.get(node, 0) <= 1

        if node not in parent_counts:
            orphan_count += 1

    # There should be exactly one orphan node in the tree (the root)
    assert orphan_count == 1
