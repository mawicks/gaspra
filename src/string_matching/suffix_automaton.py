from __future__ import annotations
from dataclasses import dataclass, field, replace


@dataclass
class Node:
    id: int
    length: int = 0
    first_endpos: int = 0
    link: Node | None = None
    transitions: dict[str, Node] = field(default_factory=dict)


def build(input_string: str):
    # Implement as described at https://cp-algorithms.com/string/suffix-automaton.html
    root = Node(id=0)
    next_id = 1

    current = root

    for character in input_string:
        last = current
        current = Node(id=next_id, length=last.length + 1, first_endpos=last.length + 1)
        next_id += 1

        p = last
        while p is not None and character not in p.transitions:
            p.transitions[character] = current
            p = p.link

        if p is None:
            current.link = root
            continue

        q = p.transitions[character]
        if q.length == p.length + 1:
            current.link = q
            continue

        # Explicitly copy() the transitions dict because replace() makes a
        # shallow copy
        clone = replace(
            q, id=next_id, length=p.length + 1, transitions=q.transitions.copy()
        )
        next_id += 1
        current.link = clone
        q.link = clone

        while (
            p is not None
            and character in p.transitions
            and p.transitions[character] == q
        ):
            p.transitions[character] = clone
            p = p.link

    return root


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
        root = build(string)
        dump(root, 2)

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
