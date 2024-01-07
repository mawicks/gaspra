import pytest

from gaspra.db_collections import DBCollection

N = 3


@pytest.fixture
def collection():
    return DBCollection("collection")


def test_set_items_are_in_collection(collection):
    for item in range(N):
        collection[str(item)] = b"x"
        assert str(item) in collection


def test_set_items_are_retrievable(collection):
    for item in range(N):
        collection[str(item)] = str(item).encode("utf-8")
        assert collection[str(item)] == str(item).encode("utf-8")


def test_length_matches_inserted_items(collection):
    assert len(collection) == 0
    for item in range(N):
        collection[str(item)] = b"x"
        assert len(collection) == item + 1


def test_overwrite_retrieves_later_values(collection):
    for item in range(N):
        collection["x"] = str(item).encode("utf-8")
        assert collection["x"] == str(item).encode("utf-8")


def test_iterate_yields_inserted_values(collection):
    for item in range(N):
        collection[str(item)] = b"x"

    assert tuple(collection) == tuple(str(i) for i in range(3))


def test_delete_removes_item(collection):
    for item in range(N):
        collection[str(item)] = b"x"

    for item in range(N):
        del collection[str(item)]
        assert len(collection) == 2 - item
        assert str(item) not in collection


def test_accessing_missing_value_raises(collection):
    with pytest.raises(KeyError):
        collection["a"]


def test_deleting_missing_value_raises(collection):
    with pytest.raises(KeyError):
        del collection["a"]
