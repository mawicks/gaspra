import pytest
import random

random.seed(42)

from string_matching.suffix_automaton import build, all_suffixes

test_strings = [
    "bananas",
    "abcbc",
    "".join(random.choices("ABC", k=20)),
]


@pytest.mark.parametrize(
    "string",
    test_strings,
)
def test_automaton_generates_only_suffixes(string):
    """
    Ensure that everything produced by the automaton is a suffix.
    Passing this along with the companion test
    test_automaton_generates_each_length_once()
    ensures that all suffixes are generated, each only once.
    """
    automaton = build(string)[0]
    for string in all_suffixes(automaton):
        # Assert that string is indeed a suffix
        assert string.endswith(string)


@pytest.mark.parametrize(
    "string",
    test_strings,
)
def test_automaton_generates_each_length_once(string):
    """
    Ensure that a string of every possible suffix length is generated
    by the automaton once and only once. Passing this along with the
    companion test test_automaton_generates_only_suffixes ensures that
    the automaton generates all of the suffixes are generated, each
    only once.
    """
    lengths = set(range(len(string) + 1))
    automaton = build(string)[0]

    for string in all_suffixes(automaton):
        assert len(string) in lengths
        # Remove len(string) so that repeats are detected.
        lengths.remove(len(string))

    # Check that every possible length was generated.
    assert len(lengths) == 0
