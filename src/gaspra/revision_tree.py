from __future__ import annotations
from collections.abc import Hashable, Iterable
from enum import Enum
from dataclasses import dataclass, field


class Direction(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2


@dataclass
class Tree:
    """
    Implement a tree having several properties useful for revision
    control.  Edges represent diffs.  The idea is to have a path from
    the current version, which is stored verbatime in the root node, to
    the previous version.  Only the changes are stored for non-root
    versions.  The idea was to keep the path from the root to any
    version "short" and the number of diffs stored "small".  When adding
    a node we wnat to minimize the number of diffs to recompute.  A
    number of constraints make this different from a typical binary tree
    implementation.  One is the requirement that the most recent node
    needs to be at the root.  Also, recent versions needs to be near the
    top, so one child of the root node is the previous version.  The
    second child of the root node is a branch of the tree that is split
    off to "balance" the tree's path length.  From the construction of
    the tree it's easy to show that construction is O(n) in storage.
    The max path length appears to be O(n^(1/2) (unproven, but it
    appears to lay the nodes on a nearly square grid).  If that's true,
    finding which branch to split, and splitting it, would be O(n^(1/2)),
    making construction O(n^{3/2). That matches timing experiments
    very precisely. Under that assumption, the reevaluate() call,
    which is only necessary when initializing a pre-existing tree, would
    be O(n).  Here are some coplexity extimates:

    Adding a node to an existing tree: O(sqrt(n))
    Calling path_to(): O(sqrt(n))
    Loading an existing tree and calling reevaluate(): O(n)
    """

    root: Node | None = None
    index: dict[Hashable, Node] = field(default_factory=dict)

    def insert(
        self, node_tag: Hashable
    ) -> tuple[
        Iterable[tuple[Hashable, Hashable]],
        Iterable[tuple[Hashable, Hashable]],
    ]:
        """
        Insert node_tag into the revision tree, notifying caller of
        inserted and removed edges.

        Arguments:
            node_tag: Hashable - A unique tag to reference the node
                being added.

        Returns:
            Iterable[tuple[Hashable, Hashable]] - Sequence of inserted
            edges as tuple(from, to).
            Iterable[tuple[Hashable, Hashable]] - Sequence of removed
            edges as tuple(from, to)
            dict[Hashable, Iterable[Hashable]] - A dictionary of paths
               that were removed (if nay).  The key is a node tag whose
               connectivity was changed and the value is the path
               leading to that node that no longer exists.  Currently,
               there is at most ne relocated node.


        """
        inserted_edges = []
        removed_edges = []

        old_root = self.root
        new_root = Node(node_tag, node_id=len(self.index))

        if old_root:
            inserted_edges.append((new_root.node_tag, old_root.node_tag))

            # Link in the other direction
            best_split, direction = find_and_detach_best_split(old_root)
            if best_split != old_root:
                if best_split and best_split.parent:
                    # Detach best_split from tree
                    removed_edges.append(
                        (best_split.parent.node_tag, best_split.node_tag)
                    )
                    if direction == Direction.LEFT:
                        best_split.parent.set_left(None)
                    else:
                        best_split.parent.set_right(None)
                # Add the new link.
                inserted_edges.append((new_root.node_tag, best_split.node_tag))
                new_root.set_right(best_split)

        new_root.set_left(old_root)
        self.root = new_root
        self.index[node_tag] = new_root
        return inserted_edges, removed_edges

    def edges(self):
        if self.root:
            yield from self.root.edges()

    def path_to(self, node_tag: Hashable) -> tuple[int | str, ...]:
        path = []
        current = self.index[node_tag]
        while current:
            path.append(current.node_tag)
            current = current.parent
        return tuple(reversed(path))

    def reevaluate(self):
        for node in self.index.values():
            # For each terminal node, ripple up the tree.
            if node.left is None and node.right is None:
                current = node
                while current:
                    current.update_states()
                    current = current.parent

    def _invalidate(self):
        """This exists only for testing reevaluate().  Don't call outside of a test."""
        for node in self.index.values():
            node._clear_state()

    def _get_state(self, node_id) -> tuple[int, int] | None:
        """
        This shouldn't be very useful except in testing. To avoid
        exposing the implementaiton, we avoid returning a Node type to
        the user and only return the data.
        """
        node = self.index.get(node_id)
        if node:
            return node.count, node.length


@dataclass
class Node:
    node_tag: Hashable
    node_id: int
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None

    length: int = 1
    count: int = 1

    def update_states(self):
        # Can't update just a single node.
        # If we change a node's state we must also
        # propagate the state up the tree.
        current = self
        while current:
            count = 1
            length = 1

            if current.left:
                count += current.left.count
                length += current.left.length

            if current.right:
                count += current.right.count
                length += current.right.length

            current.count = count
            current.length = length
            current = current.parent

    def _clear_state(self):
        """This exists only for testing.  Don't call outside of a test."""

        self.count = 0
        self.length = 0

    def set_left(self, node):
        self.left = node
        if node:
            node.parent = self
        self.update_states()

    def set_right(self, node):
        self.right = node
        if node:
            node.parent = self
        self.update_states()

    def edges(self):
        if self.left:
            yield (self.node_tag, self.left.node_tag)
            yield from self.left.edges()
        if self.right:
            yield (self.node_tag, self.right.node_tag)
            yield from self.right.edges()


def find_and_detach_best_split(root: Node):
    depth = 1
    direction = Direction.NONE
    current = root
    while current is not None and depth < current.length:
        if current.right is not None and current.left is not None:
            if current.right.length > current.left.length:
                current = current.right
                direction = Direction.RIGHT
            else:
                # This is the path for right length < left length *and*
                # also the case of a tie.  In a tie, we're intentionally
                # using the left node because it will always be the
                # newer revision.  This is a consequence of how
                # revisions get inserted.
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
        else:  # pragma: no cover
            raise RuntimeError("This should not happen!")
    return current, direction


def timing_experiment():  # pragma: no cover
    from time import perf_counter_ns
    import math

    N_RATIO = 10
    N1 = 5_000
    N2 = N_RATIO * N1
    start = perf_counter_ns()
    tree = Tree()
    for node in range(N1):
        tree.insert(node)
    duration1 = perf_counter_ns() - start

    start = perf_counter_ns()
    tree = Tree()
    for node in range(N2):
        tree.insert(node)
    duration2 = perf_counter_ns() - start

    # Compare to O(n^(3/2))
    ratio = duration2 / duration1
    complexity_exponent = math.log(ratio) / math.log(N_RATIO)
    print(f"Time complexity assuming O[N^(3/2)]: {complexity_exponent:.2f}")


if __name__ == "__main__":  # pragma: no cover
    timing_experiment()
