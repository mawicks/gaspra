import pytest

from difftools.wrappers import find_substring, find_lcs, changes

# The `wrappers` module provides simple calls which are wrappers with
# a simple interface that calls other functions in the package.
# Most of the testing occurs on the underlying methods.
# Testing here is minimal.  It checks mainly that the functions
# exist and can be called for a simple case.


@pytest.mark.parametrize(
    ["search_in", "search_for", "positions"],
    [
        ("Artistic alarms alarm artistically.", "stic", (4, 26)),
        ("Artistic alarms alarm artistically.", "ti", (2, 5, 24, 27)),
    ],
)
def test_find_substring(search_in, search_for, positions):
    assert positions == tuple(find_substring(search_in, search_for))


def test_find_lcs():
    a = "Fantastic farmers farm finely."
    b = "Artistic alarms alarm artistically."
    result = tuple(find_lcs(a, b))
    assert result == (5, 4, 5)


def test_changes():
    original = "The quick brown fox jumps over the lazy dog near the riverbank."
    modified = "The quick brown fox leaps over the lazy dogs near the river"
    result = list(changes(original, modified))
    assert result == [
        "The quick brown fox ",
        ("lea", "jum"),
        "ps over the lazy dog",
        ("s", ""),
        " near the river",
        ("", "bank."),
    ]
