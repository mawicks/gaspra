import pytest

from gaspra.memory_tree import MemoryTree
from gaspra.db_tree import DBTree
from gaspra.tree import Tree

# Intentionally use tags that are not in lexicographical order
# to make sure there's no unintend dependency on the order.
TAGS = ("a", "b", "c", "z", "x", "y", "q", "r", "s", "t")

# These are the expected paths to all existing tags after each tag from
# TAGS is added in order.
EXPECTED_PATHS = (
    (("a",),),
    (("b", "a"), ("b",)),
    (("c", "a"), ("c", "b"), ("c",)),
    (("z", "c", "a"), ("z", "b"), ("z", "c"), ("z",)),
    (("x", "c", "a"), ("x", "z", "b"), ("x", "c"), ("x", "z"), ("x",)),
    (
        ("y", "x", "c", "a"),
        ("y", "z", "b"),
        ("y", "x", "c"),
        ("y", "z"),
        ("y", "x"),
        ("y",),
    ),
    (
        ("q", "c", "a"),
        ("q", "y", "z", "b"),
        ("q", "c"),
        ("q", "y", "z"),
        ("q", "y", "x"),
        ("q", "y"),
        ("q",),
    ),
)


@pytest.fixture(params=[MemoryTree, DBTree])
def tree(request) -> Tree:
    tree_factory = request.param
    return tree_factory()


def test_containment_changes_after_add(tree):
    base = None
    for id in TAGS:
        assert id not in tree
        tree.add(id, base)
        assert id in tree
        base = id


def test_path_to_returns_single_node_after_add(tree):
    base = None
    for id in TAGS:
        assert id not in tree
        tree.add(id, base)
        assert tuple(tree.path_to(id)) == (id,)
        base = id


def test_path_to_with_linear_change_parent(tree):
    base = None
    for index, id in enumerate(TAGS):
        tree.add(id, base)
        if base:
            tree.change_parent(base, id)

        # Check paths to all existing nodes from node just inserted.
        for earlier_index in range(index + 1):
            path = TAGS[earlier_index : index + 1]
            assert tuple(tree.path_to(TAGS[earlier_index])) == tuple(reversed(path))
        base = id


def test_path_to_after_get_split_and_change_parent(tree):
    base = None
    for tag, paths in zip(TAGS, EXPECTED_PATHS):
        tree.add(tag, base)
        if base is not None:
            split, _ = tree.get_split(base)
            if split != base:
                tree.change_parent(split, tag)
            tree.change_parent(base, tag)
        for path in paths:
            assert tuple(tree.path_to(path[-1])) == path
        base = tag


def test_expected_base_version(tree):
    base = None
    for id in TAGS:
        tree.add(id, base)
        assert base == tree.base_version(id)
        base = id

    # Make sure the base version is still correct after inserting
    # everything.
    base = None
    for id in TAGS:
        assert base == tree.base_version(id)
        base = id
