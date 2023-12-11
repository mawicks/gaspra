from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, replace


@dataclass
class Node:
    id: int
    length: int = 0
    first_endpos: int = 0  # First possible ending position of substring.
    link: Node | None = None
    transitions: dict[str, Node] = field(default_factory=dict)

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


def build(input_string: str) -> tuple[Node, Node, Iterator[int]]:
    # Implement as described at https://cp-algorithms.com/string/suffix-automaton.html
    id_sequence = make_id_sequence()
    root = Node(next(id_sequence))

    current = root

    for character in input_string:
        current = extend(character, current, id_sequence)

    return root, current, id_sequence


def extend(character: str, last: Node, id_sequence: Iterator[int]):
    new_node = Node(
        id=next(id_sequence),
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
            new_node.link = insert_node(character, current, q, next(id_sequence))

    return new_node


def insert_node(character: str, p: Node, q: Node, id: int):
    clone = replace(
        q,
        id=id,
        length=p.length + 1,
        # Explicitly copy() the transitions dict because replace() makes a
        # shallow copy
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


def is_substring(root: Node, s: str):
    current = root
    for character in s:
        current = current.transitions.get(character)
        if current is None:
            return None
    return current.first_endpos - len(s)


def dump(root: Node, indent: int = 0, dumped: set[int] | None = None):
    if dumped is None:
        dumped = set()

    if root.id in dumped:
        return

    print(f"{' '*indent}{root.id}: (length:{root.length})")
    if root.transitions.items():
        for character, node in root.transitions.items():
            print(f"{' '*indent}  {character} -> {node.id}")
    else:
        print(f"{' '*indent}  No transitions")

    dumped.add(root.id)

    for character, node in root.transitions.items():
        dump(node, indent, dumped)


if __name__ == "__main__":
    for string in ("abcbc", "bananas"):
        print(f"\n{string}")
        root, __ignore__, __ignore__ = build(string)
        dump(root, indent=2)

        def show_match(substring):
            position = is_substring(root, substring)
            print(f"'{substring}': {'no' if position is None else 'yes'} ({position})")

        for k in range(len(string)):
            suffix = string[k:]
            prefix = string[:-k]
            extended_prefix = prefix + "x"

            show_match(suffix)
            show_match(prefix)
            show_match(extended_prefix)
