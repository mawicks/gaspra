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

    # The values in `shared_strings` are sets that represent the set of
    # strings in `string_set` that share a given node's state.  The
    # key is the node's id.
    shared_strings = {}

    # The suffix automaton can be very deep so we must use an
    # interative solution rather than a recursion solution.
    # The python recursion limit is on the order of 1k and we want
    # to handle strings in `string_set`` much larger than that.

    # The algorithm works as follows: When we don't know which
    # elements of `string_set` share a given node's state, we add
    # that node to the queue of nodes to be processed.

    # At each iteration, we examine the node on the top of
    # the stack and attempt to compute the strings that share its state.
    # That is possible if the shared strings are known for all of its
    # children. If any of the chidren have unknown shared string
    # membershiops, add those children to the stack so their shared
    # strings will get computed.

    # Initialize the stack with just the root node, for which string
    # membership is assumed to be initially unknown (the root
    # node is always shared by all of the strings, but setting it
    # initially as unknown forces the algorithm to compute the shared
    # strings for it and all of its descendents.)

    # We're interested in the deepest state that *all* of the strings
    # have in common.  As we're computing the common strings for each
    # state, we'll record the maximal state with *all* strings in common.

    stack = [root]
    max_length = 0
    best_endpos = 0

    while len(stack) > 0:
        top = stack[-1]
        # If we already know the shared strings for the node on the top of the
        # stack, simply remove it.
        if top.id in shared_strings:
            stack.pop()
        # If we don't know the shared_strings for the top of the stack...
        elif all([node.id in shared_strings for node in top.transitions.values()]):
            shared_strings[top.id] = set()
            for token, child_node in top.transitions.items():
                # If any of the transitions are end of string tokens,
                # then we know the parent state represents a substring
                # associated with that token
                if isinstance(token, int):
                    shared_strings[top.id].add(token)
                # If any of the transitions are regular charactrers
                # then the parent inherits the child's memberships
                elif isinstance(token, str):
                    child_memberships = shared_strings[child_node.id]
                    shared_strings[top.id] = shared_strings[top.id].union(
                        child_memberships
                    )

                else:
                    raise RuntimeError(f"Unexpected branch token: {token}")
            if (
                len(shared_strings[top.id]) == len(string_set)
                and top.length > max_length
            ):
                max_length = top.length
                best_endpos = top.first_endpos

            stack.pop()

        # Or add the unknown children to the stack so they get computed.
        else:
            for next_node in top.transitions.values():
                if next_node.id not in shared_strings:
                    stack.append(next_node)

    return best_endpos - max_length, max_length
