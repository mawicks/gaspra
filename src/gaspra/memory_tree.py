from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass, field, replace


@dataclass
class Node:
    order_id: int
    parent: Hashable | None = None
    children: list[Hashable] = field(default_factory=list)
    height: int = 1
    size: int = 1
    base_version: Hashable | None = None


@dataclass
class MemoryTree:
    nodes: dict[Hashable, Node] = field(default_factory=dict)

    def __contains__(self, tag: Hashable):
        return tag in self.nodes

    def base_version(self, tag):
        return self.nodes[tag].base_version

    def add(self, tag: Hashable, existing_head: Hashable | None = None):
        """Add the tag to the tree without any connections"""
        self.nodes[tag] = Node(order_id=len(self.nodes), base_version=existing_head)

    def path_to(self, tag: Hashable) -> Sequence[Hashable]:
        """
        Function to retrieve the path to a version.
        """
        if tag not in self.nodes:  # pragma: no cover
            raise ValueError(f"{tag} is not a valid version.")

        path = []
        while tag is not None:
            path.append(tag)
            tag = self.nodes[tag].parent

        return tuple(reversed(path))

    def change_parent(self, tag, new_parent):
        original_node = self.nodes[tag]

        # Remove "tag" from its parents set of children.
        if (
            original_node.parent is not None
            and tag in self.nodes[original_node.parent].children
        ):
            self.nodes[original_node.parent].children.remove(tag)

        # Replace tag's parent.
        node = replace(original_node, parent=new_parent)
        self.nodes[tag] = node

        # Add "tag" to its new parent's set of children.
        if node.parent is not None:
            self.nodes[node.parent].children.append(tag)
            self._update_metrics(node.parent)

        # Recompute spanning tree metrics.
        if original_node.parent is not None:
            self._update_metrics(original_node.parent)

    def get_split(self, tag: Hashable):
        """
        Find the longest path beginning from `tag` to a leaf and
        identify a node near the middle.  The path will be split at that
        node.  This node and the old root will become children of a new
        root.  In the case of a tie for the longest path, follow the
        path with that was added to the network more recently (which
        should be the one with the largest index in children)

        """
        node = self.nodes[tag]
        path_to_split = [tag]
        depth = 1
        # All leaves have a height of one, so within this
        # loop there will always be children.  Because depth
        # starts at one, you cannot enter this loop for a leaf.
        while depth < node.height:
            next_child_index = max(
                (self.nodes[child].height, self.nodes[child].order_id, index)
                for index, child in enumerate(node.children)
            )[2]
            depth += 1
            tag = node.children[next_child_index]
            node = self.nodes[tag]
            path_to_split.append(tag)

        return tag, path_to_split

    def _update_metrics(self, tag):
        """
        Update metrics *above* a node that was moded.  When a node is
        moved from one parent to another, update_metrics() should be
        called for both of the parents (not the node moved)
        """
        while tag is not None:
            node = self.nodes[tag]
            if node.children:
                child_height = max(
                    [self.nodes[child].height for child in node.children]
                )
                size = sum([self.nodes[child].size for child in node.children])
            else:
                child_height = 0
                size = 0
            self.nodes[tag] = replace(node, height=child_height + 1, size=size + 1)
            tag = node.parent
