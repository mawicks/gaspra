from itertools import chain

from collections.abc import Sequence

from string_matching.suffix_automaton import build


def concatenate_strings(string_set: Sequence[str]):
    chainlets = [chain(string, (index,)) for index, string in enumerate(string_set)]

    return chain(*chainlets)


def find_lcs(string_set: Sequence[str]) -> tuple[int, int]:
    """
    Given a sequence of strings, find the longest substring common
    to all members of the sequence.

    Returns:
       int - position of occurence in first string
       length - length of common substring
    """
    root = build(concatenate_strings(string_set))

    string_memberships = {}

    # `stack` contains a list of nodes for which we don't know
    # whether they represent a substring of the members of string_set
    # Initialize it with just the root node, for which nothing is known.
    stack = [root]
    max_length = 0
    best_endpos = 0

    while len(stack) > 0:
        top = stack[-1]
        # If we already know the membership of the top of the stack, simply remove it.
        if top.id in string_memberships:
            stack.pop()
        # If we don't know the membership of the top of the stack...
        else:
            # Either compute it, if all of its children are known...
            if all(
                [node.id in string_memberships for node in top.transitions.values()]
            ):
                string_memberships[top.id] = set()
                for token, child_node in top.transitions.items():
                    # If any of the transitions are end of string tokens,
                    # then we know the parent state represents a substring
                    # associated with that token
                    if isinstance(token, int):
                        string_memberships[top.id].add(token)
                    # If any of the transitions are regular charactrers
                    # then the parent inherits the child's memberships
                    elif isinstance(token, str):
                        child_memberships = string_memberships[child_node.id]
                        string_memberships[top.id] = string_memberships[top.id].union(
                            child_memberships
                        )

                    else:
                        raise RuntimeError(f"Unexpected branch token: {token}")
                if (
                    len(string_memberships[top.id]) == len(string_set)
                    and top.length > max_length
                ):
                    max_length = top.length
                    best_endpos = top.first_endpos

            # Or add the unknown children to the stack so they get computed.
            for next_node in top.transitions.values():
                if next_node.id not in string_memberships:
                    stack.append(next_node)

    return best_endpos - max_length, max_length
