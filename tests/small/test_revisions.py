import pytest

from gaspra.revisions import Tree

TREES = (
    (),
    ((0, 1),),
    ((2, 1), (2, 0)),
    ((3, 2), (3, 1), (2, 0)),
)


def test_add_revision():
    tree = Tree()

    for node, expected_tree in enumerate(TREES):
        test_edges = {tuple(sorted(edge)) for edge in expected_tree}

        tree.add(node)
        assert test_edges == {tuple(sorted(edge)) for edge in tree.edges()}
