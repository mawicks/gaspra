import pytest
import random
import time

random.seed(42)

from string_matching.suffix_automaton import build, all_suffixes, find_substring

build_and_search_test_strings = [
    "bananas",
    "abcbc",
    "".join(random.choices("ABC", k=20)),
]

substring_test_strings = [("bananas", "xnanananx", "anana")]


@pytest.mark.parametrize(
    "string",
    build_and_search_test_strings,
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
    build_and_search_test_strings,
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


COMPLEXITY_TEST_COEFFICIENT = 3.0
COMPLEXITY_TEST_EXPONENT = 1.5


def test_construction_time_is_approximately_linear():
    """
    This is an attempt to verify that the construction
    time is linear.  It's likely easy to insert something in the
    algorithm that makes it quadratic and this test should catch that.
    It takes some time to run, however.
    """
    string_1 = "".join(random.choices("ABCDEFG", k=10_000))
    string_2 = "".join(random.choices("ABCDEFG", k=100_000))
    start = time.perf_counter_ns()
    build(string_1)
    end_1 = time.perf_counter_ns()
    build(string_2)
    end_2 = time.perf_counter_ns()
    time_1 = end_1 - start
    time_2 = end_2 - start

    time_ratio = time_2 / time_1
    string_ratio = len(string_2) / len(string_1)

    if string_ratio < 2.0 * COMPLEXITY_TEST_COEFFICIENT:
        raise ValueError("Choose test strings with a larger ratio of their lengths")

    # Use two tests in case k gets changed above.
    # Both assume a fairly large ratio of string lengths (say 10).
    # First check that it's less than about O(n^1.5)
    assert time_ratio < string_ratio**COMPLEXITY_TEST_EXPONENT
    # Then check for approximate linearity with a small
    # coefficient greater than 1 to provide some slop.
    assert time_ratio < COMPLEXITY_TEST_COEFFICIENT * string_ratio


@pytest.mark.parametrize("string", build_and_search_test_strings)
def test_find_substring_is_true_on_all_substrings(string):
    """
    Build automaton for "string" and check that every non-trivial
    substring is correctly detected.
    """
    root = build(string)[0]

    for start in range(len(string)):
        for end in range(start + 1, len(string)):
            substring = string[start:end]
            position = find_substring(root, substring)
            assert position is not None
            assert string[position : position + len(substring)] == substring


@pytest.mark.parametrize("string", build_and_search_test_strings)
def test_find_substring_is_correct_on_random_letters(string):
    """
    Build automaton for "string" and check that non-trivial
    random strings of different lengths selected from characters
    of "string" are detected (or not detected) correctly.
    """
    root = build(string)[0]

    for k in range(len(string)):
        candidate = "".join(random.choices(string, k=k + 1))
        position = find_substring(root, candidate)
        assert string.find(candidate) == position or position is None
