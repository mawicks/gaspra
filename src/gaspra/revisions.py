from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field


class Direction(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2


@dataclass
class Tree:
    root: Node | None = None
    index: dict[int | str, Node] = field(default_factory=dict)

    def add(self, node_id: int | str):
        old_root = self.root
        new_root = Node(node_id)
        new_root.set_left(old_root)

        # Link in the other direction
        if old_root:
            best_split, direction = find_and_detach_best_split(old_root)
            # Detach with best_split from tree
            if best_split and best_split.parent:
                if direction == Direction.LEFT:
                    best_split.parent.set_left(None)
                else:
                    best_split.parent.set_right(None)
            if best_split != old_root:
                new_root.set_right(best_split)

        self.root = new_root
        self.index[node_id] = new_root

    def edges(self):
        if self.root:
            yield from self.root.edges()

    def find(self, node_id) -> Node | None:
        return self.index.get(node_id)


@dataclass
class Node:
    node_id: int | str
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None

    length: int = 1
    count: int = 1

    def update_state(self):
        count = 1
        length = 1

        if self.left:
            count += self.left.count
            length += self.left.length

        if self.right:
            count += self.right.count
            length += self.right.length

        self.count = count
        self.length = length

    def set_left(self, node):
        self.left = node
        if node:
            node.parent = self
        self.update_state()

    def set_right(self, node):
        self.right = node
        if node:
            node.parent = self
        self.update_state()

    def edges(self):
        if self.left:
            yield (self.node_id, self.left.node_id)
            yield from self.left.edges()
        if self.right:
            yield (self.node_id, self.right.node_id)
            yield from self.right.edges()


def find_and_detach_best_split(current: Node):
    depth = 1
    direction = Direction.NONE
    while current is not None and depth < current.length:
        if current.right is not None and current.left is not None:
            if current.right.length > current.left.length:
                current = current.right
                direction = Direction.RIGHT
            elif current.left.length > current.right.length:
                current = current.left
                direction = Direction.LEFT
            elif current.right.node_id > current.left.node_id:
                current = current.right
                direction = Direction.RIGHT
            else:
                current = current.left
                direction = Direction.LEFT
            depth += 1
        elif current.right is not None:
            current = current.right
            direction = Direction.RIGHT
            depth += 1
        elif current.left is not None:
            current = current.left
            direction = Direction.LEFT
            depth += 1
        else:
            raise RuntimeError("This should not happen!")
    return current, direction
