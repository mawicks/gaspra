from itertools import chain

from collections.abc import Sequence

from gaspra.suffix_automaton import (
    build,
    _get_all_start_positions,
)


def concatenate_strings(string_set: Sequence[str]):
    # Concatenate the members of string_set with end of string "tokens"
    # to separate them. End of string "tokens" are represented by
    # strings of length 2, e.g. "$0", "$1", etc., so there's no
    # possibility of them matching any single unicode character.

    chainlets = [
        chain(string, (f"${index}",)) for index, string in enumerate(string_set)
    ]

    return chain(*chainlets)


def find_lcs(*string_set: str) -> tuple[tuple[int, ...], int | None]:
    """
    Given a sequence of strings, find the longest substring common
    to all members of the sequence.

    Arguments:
       *string_set: Sequence[str]
          Sequence of strings on which to compute the LCS.

    Returns:
       tuple[int, ...]:
          Tuple with the positions of the first occurence in each string
       length:
          Length of the common substring
    """

    # The suffix automaton can be very deep so we must use an interative
    # solution rather than a recursion solution.  The python recursion
    # limit is on the order of 1k and we want to handle strings in
    # `string_set`` much larger than that.

    # The algorithm works as follows: When we don't know which elements
    # of `string_set` share a given node's state, we add that node to
    # the queue of nodes to be processed.

    # At each iteration, we examine the node on the top of the stack and
    # attempt to compute the strings that share its state.  That is
    # possible if the shared strings are known for all of its children.
    # If any of the chidren have unknown shared string membershiops, add
    # those children to the stack so their shared strings will get
    # computed.

    # Initialize the stack with just the root node, for which string
    # membership is assumed to be initially unknown (the root node is
    # always shared by all of the strings, but setting it initially as
    # unknown forces the algorithm to compute the shared strings for it
    # and all of its descendents.)

    # We're interested in the deepest state that *all* of the strings
    # have in common.  As we're computing the common strings for each
    # state, we'll record the maximal state with *all* strings in
    # common.

    # The values in `shared_strings` are sets that represent the set of
    # strings in `string_set` that share a given node's state.  The key
    # is the node's id.
    shared_strings = {}

    root = build(concatenate_strings(string_set))
    if len(string_set) == 0:
        return (), None

    stack = [root]
    max_length = 0
    best_node = root

    while len(stack) > 0:
        top = stack[-1]
        # If we already know the shared strings for the node on the top
        # of the stack, simply remove it.
        if top.id in shared_strings:
            stack.pop()

        # If we don't know the shared_strings for the top of the stack...
        elif all([node.id in shared_strings for node in top.transitions.values()]):
            update_shared_strings(shared_strings, top)

            if (
                len(shared_strings[top.id]) == len(string_set)
                and top.length > max_length
            ):
                max_length = top.length
                best_node = top

            stack.pop()

        # Or add the unknown children to the stack so they get computed.
        else:
            for next_node in top.transitions.values():
                if next_node.id not in shared_strings:
                    stack.append(next_node)

    raw_positions = _get_all_start_positions(best_node, max_length)

    string_positions = get_string_offsets(raw_positions, string_set)

    return tuple(string_positions), max_length


def get_string_offsets(positions, string_set):
    adjusted_positions = []
    next_string_start_pos = 0
    for s in string_set:
        for position in positions:
            if position >= next_string_start_pos:
                adjusted_positions.append(position - next_string_start_pos)
                break
        next_string_start_pos += len(s) + 1  # + 1 is for the separator.
    return adjusted_positions


def update_shared_strings(shared_strings, top):
    shared_strings[top.id] = set()
    for token, child_node in top.transitions.items():
        # If any of the transitions are end of string tokens, then we
        # know the parent state represents a substring associated with
        #  that token. End of string "tokens" are represented by strings
        # of length 2, e.g. "$0", "$1", etc., so there's no possibility
        # of them matching any single unicode character.
        if len(token) > 1:
            shared_strings[top.id].add(token)

        # If any of the transitions are regular charactrers then the
        # parent inherits the child's memberships
        else:
            child_memberships = shared_strings[child_node.id]
            shared_strings[top.id] = shared_strings[top.id].union(child_memberships)
