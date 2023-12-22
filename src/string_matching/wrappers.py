from typing import Iterable

import string_matching.suffix_automaton as sa


def find_substring(search_in: str, search_for: str) -> Iterable[int]:
    """Find all occurences of search_for in search_in

    Arguments:
        search_in: str
            The string to be searched
        search_for: str
            The string to search for

    Returns
        Iterable[int]
            Sequence of locations in search_in where search_for was found
    """

    root = sa.build(search_in)
    return sa.find_substring_all(root, search_for)


def find_lcs(s1: str, s2: str):
    """Returns the locations of the earliest occurences of the LCS of s1 and s2

    Arguments:
       s1: str
          - The first string
       s2: str
          - The second string

    Returns:
        int:
           The position of the LCS in s1
        int:
           The position of the LCS in s2
        int:
           The length of the LCS.
    """
    root = sa.build(s1)
    p1, p2, length = sa.find_lcs(root, s2)
    return p1, p2, length
