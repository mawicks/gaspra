import time
from gaspra.suffix_automaton import build, find_substring_all


from gaspra.test_helpers.random_strings import random_string

COMPLEXITY_TEST_COEFFICIENT = 3.0
COMPLEXITY_TEST_EXPONENT = 1.5
RECURSION_TEST_LENGTH = 2_000  # 961 works. 962 fails with a recursive implementation


def test_find_substring_all_depth():
    """
    This test on a long string with a lot of matches is separated
    from earlier tests above because it's long-running and tends to
    clutter up logs.  It can be run occasionally.
    """
    query_string = "a"
    automaton_string = query_string * RECURSION_TEST_LENGTH
    root = build(automaton_string)
    result = tuple(find_substring_all(root, "a"))
    expected_result = tuple(range(RECURSION_TEST_LENGTH))
    assert result == expected_result


def test_construction_time_is_approximately_linear():
    """
    This is an attempt to verify that the construction
    time is linear.  It's likely easy to insert something in the
    algorithm that makes it quadratic and this test should catch that.
    It takes some time to run, however.
    """
    string_1 = random_string("abcdefg", 10_000, 41)
    string_2 = random_string("abcdefg", 100_000, 42)
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
