from typing import Iterable

import gaspra.suffix_automaton as sa


def find_substring(search_in: str, search_for: str) -> Iterable[int]:
    """Find all occurences of search_for in search_in

    Arguments:
        search_in: str
            The string to be searched
        search_for: str
            The string to search for

    Returns
        Iterable[int]
            Positions of every occurrence of `search_for` in `seach_in`.
    """

    root = sa.build(search_in)
    return sa.find_substring_all(root, search_for)


def find_lcs(a: str, b: str):
    """Returns the locations of the first occurences of the LCS of s1 and s2 in
    each string.

    Arguments:
        a: str
            - The first string
        a: str
            - The second string

    Returns:
        int:
            The position of the LCS in s1
        int:
            The position of the LCS in s2
        int:
            The length of the LCS.

    Note that the empty string is always a common substring, occurring at the
    beginning of both lists.
    """
    root = sa.build(a)
    pa, pb, length = sa.find_lcs(root, b)
    return pa, pb, length
