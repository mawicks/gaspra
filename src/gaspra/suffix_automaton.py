from __future__ import annotations

from collections.abc import Iterator, Iterable, Sequence
from dataclasses import dataclass, field
import random
from typing import Callable

from gaspra.types import TokenSequence, Separator


@dataclass
class Node:
    id: int
    length: int = 0
    transitions: dict[str | int, Node] = field(default_factory=dict)
    first_endpos: int = 0  # First possible ending position of substring.
    is_terminal: bool = False  # Is this a terminal state?
    link: Node | None = None
    reverse_links: list[Node] = field(default_factory=list)
    empty: str | TokenSequence = ""

    @staticmethod
    def get_factory(empty_sequence: str | TokenSequence):
        generator = make_id_sequence()

        def factory(**kwargs):
            return Node(id=next(generator), empty=empty_sequence, **kwargs)

        return factory


def make_id_sequence() -> Iterator[int]:
    id = 0
    while True:
        yield id
        id += 1


def wrap_node_factory(
    node_factory: Callable[..., Node],
    node_list: list[Node],
):
    """Wrap a node_factory() so that it always appends to a node_list

    Arguments:
        node_factory: Callable[..., Node]
            Node factory to wrap
        node_list: List[Node]
            List to append to when a node gets created
    """

    def wrapped_node_factory(**kwargs):
        new_node = node_factory(**kwargs)
        node_list.append(new_node)
        return new_node

    return wrapped_node_factory


def build(
    input_string: Iterable[str | int | Separator],
    reverse_links=True,
    mark_terminals=True,
    empty: str | tuple[int, ...] = "",
) -> Node:
    """Build a suffix automaton from `input_string`.

    Arguments:
        input_string:  Iterable[str | int]
            Character or byte sequence representing the input.
        reverse_links: bool
            If true, construct reverse_links (needed to find *all*
            occurrences of a string.
        mark_terminals: bool
            If true, flag terminal nodes as such (needed to read suffixes
            back from automaton).  This is typically very fast.

    """
    # Create a list to capture all created nodes to make it easier to
    # iterate over them later.
    node_list = []

    # Decorate node factory so that node_list is updated on every call.
    node_factory = wrap_node_factory(Node.get_factory(empty), node_list)

    # Implemention mostly follows description at
    # https://cp-algorithms.com/string/suffix-automaton.html

    root = node_factory()
    current = root

    for character in input_string:
        current = extend(character, current, node_factory)

    if mark_terminals:
        mark_terminal_nodes(current)

    if reverse_links:
        add_reverse_links(node_list)

    return root


def extend(
    character: str | int,
    last: Node,
    node_factory: Callable[..., Node],
):
    """Extend a partially constructed automaton by one additional character

    Given a suffix automaton that recognizes the suffixes of some string
    "s", extend that automoton to recognize the suffixes of `s +
    character`

    """
    new_node = node_factory(
        length=last.length + 1,
        first_endpos=last.length + 1,
    )

    previous = None
    current = last
    while current is not None and character not in current.transitions:
        current.transitions[character] = new_node
        previous = current
        current = current.link

    if current is None:
        new_node.link = previous
    else:
        q = current.transitions[character]
        if q.length == current.length + 1:
            new_node.link = q
        else:
            new_node.link = insert_node(character, current, q, node_factory)

    return new_node


def insert_node(
    character: str | int,
    p: Node,
    q: Node,
    node_factory: Callable[..., Node],
):
    clone = node_factory(
        length=p.length + 1,
        first_endpos=q.first_endpos,
        link=q.link,
        transitions=q.transitions.copy(),
    )
    q.link = clone

    current = p
    while (
        current is not None
        and character in current.transitions
        and current.transitions[character] == q
    ):
        current.transitions[character] = clone
        current = current.link

    return clone


def mark_terminal_nodes(final_node: Node):
    current = final_node
    while current is not None:
        current.is_terminal = True
        current = current.link
    return


def add_reverse_links(node_list: list[Node]):
    for node in node_list:
        if node.link is not None:
            node.link.reverse_links.append(node)
    return


def find_substring(root: Node, s: Sequence[str | int]) -> int | None:
    current = _find_match_node(root, s)
    if current is None:
        return None
    return current.first_endpos - len(s)


def find_substring_all(root: Node, s: str) -> Iterable[int]:
    current = _find_match_node(root, s)
    if current is None:
        return ()

    return _get_all_start_positions(current, len(s))


def _get_all_start_positions(current, length):
    candidates = sorted(
        node.first_endpos - length for node in follow_reverse_links(current)
    )

    positions = dedup_sorted(candidates)
    return positions


def _find_match_node(root: Node, s: Iterable[str | int]) -> Node | None:
    current = root
    for character in s:
        current = current.transitions.get(character)
        if current is None:
            return None
    return current


def follow_reverse_links(current):
    # Use a non-resursive solution
    to_do = [current]
    all = []
    while len(to_do) > 0:
        current = to_do.pop()
        all.append(current)
        for child in current.reverse_links:
            to_do.append(child)
    return all


def dedup_sorted(sequence: Iterable[int]) -> list[int]:
    deduped = []
    for candidate in sequence:
        if len(deduped) == 0 or candidate != deduped[-1]:
            deduped.append(candidate)
    return deduped


def find_lcs(root: Node, s: str | TokenSequence) -> tuple[int, int, int]:
    """Return the starting positions and length of an LCS.

    The LCS is the longest common substring of the
    string used to construct the automaton rooted at `root`
    and the passed string `s`.

    Arguments:
        root: Node
            Root node of a suffix automaton for one of the strings
        s: str
            The string searched for substrings in common with the
            automaton string

    Returns:
        int
            The starting position of the match in the automaton string
        int
            The starting position of the match in `s`
        int
            The length of the common substring

    """
    longest_match_length = current_match_length = 0
    longest_match_s1_endpos = longest_match_s2_endpos = 0

    current = root
    for position, character in enumerate(s):
        while (
            next := current.transitions.get(character)
        ) is None and current.link is not None:
            current = current.link
            current_match_length = current.length

        if next is not None:
            current_match_length += 1
            current = next
        # This block can be indented but the sample implementation has
        # it this way.
        if current_match_length > longest_match_length:
            longest_match_length = current_match_length
            longest_match_s1_endpos = current.first_endpos
            longest_match_s2_endpos = position + 1

    return (
        longest_match_s1_endpos - longest_match_length,
        longest_match_s2_endpos - longest_match_length,
        longest_match_length,
    )


def all_suffixes(current: Node) -> Iterator[str | tuple[int, ...]]:
    """Iterate over every suffix in the automaton.

    The only purpose for this is in a test that ensures the automaton
    produces all suffixes and only suffixes.
    """
    if current.is_terminal:
        yield current.empty

    for token, node in current.transitions.items():
        for substring in all_suffixes(node):
            if isinstance(token, str) and isinstance(substring, str):
                yield token + substring
            elif isinstance(token, int) and isinstance(substring, tuple):
                yield (token,) + substring  # (character,)  # + substring
            else:
                raise ValueError(f"Unexpected type {type(token)}")


def dump(root: Node, indent: int = 0, dumped: set[int] | None = None):
    if dumped is None:
        dumped = set()

    if root.id in dumped:
        return

    print(
        f"{' '*indent}{root.id}: (length:{root.length}, "
        f"is_terminal:{root.is_terminal})"
    )
    if root.transitions.items():
        for character, node in root.transitions.items():
            print(f"{' '*indent}  {character} -> {node.id}")
    else:
        print(f"{' '*indent}  No transitions")

    dumped.add(root.id)

    for character, node in root.transitions.items():
        dump(node, indent, dumped)


if __name__ == "__main__":
    random_string = "".join(random.choices("XYZ", k=10))
    for string in ("abcbc", "bananas", random_string):
        print(f"\n{string}")
        root = build(string)
        dump(root, indent=2)

        print("\nAll suffixes:")
        for item in sorted(all_suffixes(root), key=len):
            print(f"'{item}'")
        print()

        def show_match(substring):
            position = find_substring(root, substring)
            print(f"'{substring}': {'no' if position is None else 'yes'} ({position})")

        for k in range(len(string)):
            suffix = string[k:]
            prefix = string[:-k]
            random_substring = "".join(random.choices(string, k=len(string) - k))

            show_match(suffix)
            show_match(prefix)
            show_match(random_substring)
