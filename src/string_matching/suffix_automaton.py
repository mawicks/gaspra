from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Callable
import random


@dataclass
class Node:
    id: int
    length: int = 0
    transitions: dict[str, Node] = field(default_factory=dict)
    first_endpos: int = 0  # First possible ending position of substring.
    is_terminal: bool = False  # Is this a terminal state?
    link: Node | None = None

    @staticmethod
    def get_factory():
        generator = make_id_sequence()

        def factory(**kwargs):
            return Node(id=next(generator), **kwargs)

        return factory


def make_id_sequence() -> Iterator[int]:
    id = 0
    while True:
        yield id
        id += 1


def build(input_string: str) -> tuple[Node, Node, Callable[..., Node]]:
    # Implement as described at https://cp-algorithms.com/string/suffix-automaton.html
    node_factory = Node.get_factory()
    root = node_factory()

    current = root

    for character in input_string:
        current = extend(character, current, node_factory)

    mark_terminals(current)

    return root, current, node_factory


def extend(character: str, last: Node, node_factory):
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


def insert_node(character: str, p: Node, q: Node, node_factory):
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


def mark_terminals(final_node):
    current = final_node
    while current is not None:
        current.is_terminal = True
        current = current.link
    return


def is_substring(root: Node, s: str):
    current = root
    for character in s:
        current = current.transitions.get(character)
        if current is None:
            return None
    return current.first_endpos - len(s)


def all_suffixes(current: Node) -> Iterator[str]:
    """
    Iterate over every suffix in the automaton.  The only purpose
    for this is in a test that ensures the automaton produces all suffixes
    and only suffixes.
    """
    if current.is_terminal:
        yield ""

    for character, node in current.transitions.items():
        for substring in all_suffixes(node):
            yield character + substring


def dump(root: Node, indent: int = 0, dumped: set[int] | None = None):
    if dumped is None:
        dumped = set()

    if root.id in dumped:
        return

    print(
        f"{' '*indent}{root.id}: (length:{root.length}, is_terminal:{root.is_terminal})"
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
        root, __ignore__, __ignore__ = build(string)
        dump(root, indent=2)

        print("\nAll suffixes:")
        l = sorted(all_suffixes(root), key=len)
        for item in l:
            print(f"'{item}'")
        print()

        def show_match(substring):
            position = is_substring(root, substring)
            print(f"'{substring}': {'no' if position is None else 'yes'} ({position})")

        for k in range(len(string)):
            suffix = string[k:]
            prefix = string[:-k]
            random_substring = "".join(random.choices(string, k=len(string) - k))

            show_match(suffix)
            show_match(prefix)
            show_match(random_substring)
