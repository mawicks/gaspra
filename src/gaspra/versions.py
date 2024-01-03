from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass, field, replace
from typing import Callable, cast

from gaspra.changesets import (
    find_changeset,
    apply_forward,
)
from gaspra.revision_tree import Tree
from gaspra.types import TokenSequence, ReducedChangeIterable


def check_connectivity(edges_to_create, edges_to_remove):
    """
    This is a sanity check that we don't destroy connectivity
    by removing an edge to a node without replacing it with
    another path.
    """
    new_destinations = set(pair[1] for pair in edges_to_create)

    if not all(
        pair[1] in new_destinations for pair in edges_to_remove
    ):  # pragma: no cover
        raise RuntimeError(
            "Removing an edge to a node without replacing it with another path"
        )


@dataclass
class Linkage:
    parent: Hashable | None = None
    children: set[Hashable] = field(default_factory=set)
    depth: int = 1
    descendents: int = 1


@dataclass
class Versions:
    tree: Tree = field(default_factory=Tree)

    versions: dict[Hashable, Sequence[Hashable]] = field(default_factory=dict)
    diffs: dict[Hashable, ReducedChangeIterable] = field(default_factory=dict)
    linkage: dict[Hashable, Linkage] = field(default_factory=dict)

    tokenizer: Callable[[bytes, dict[bytes, int]], Sequence[int]] | None = None
    decoder: Callable[[Sequence[int], Sequence[bytes]], bytes] | None = None
    tokens: dict[bytes, int] = field(default_factory=dict)
    token_map: tuple[bytes, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if (self.tokenizer is not None and self.decoder is None) or (
            self.tokenizer is None and self.decoder is not None
        ):  # pragma: no cover
            raise ValueError(
                "Either both tokenizer and decoder must be set or neither."
            )

    def save(self, tag: Hashable, version: bytes):
        edges_to_create, edges_to_remove = self.tree.insert(tag)
        check_connectivity(edges_to_create, edges_to_remove)

        if self.tokenizer is None:
            tokenized = version
        else:
            tokenized = self.tokenizer(version, self.tokens)
            self.token_map = tuple(self.tokens.keys())

        self.versions[tag] = tokenized
        self.linkage[tag] = Linkage()

        for current_tag, older_tag in edges_to_create:
            current_version = self._retrieve_raw(current_tag)
            older_version = self._retrieve_raw(older_tag)

            self._add_edge(
                current_tag,
                older_tag,
                tuple(find_changeset(current_version, older_version).change_stream()),
            )

        for current_tag, older_tag in edges_to_remove:
            self._remove_edge(current_tag, older_tag)

        return

    def _add_edge(self, parent_tag, child_tag, changeset):
        self.diffs[parent_tag, child_tag] = changeset

        # It's a spanning tree so a node can have only one
        # parent.  When adding an edge, the new parent
        # steals the child from any pre-existing parent.
        self._change_parent(child_tag, parent_tag)

        # Older tag is no longer at the head of a branch
        # so remove it from versions.
        if child_tag in self.versions:
            del self.versions[child_tag]

    def _change_parent(self, tag, new_parent):
        original_linkage = self.linkage[tag]

        # Remove "tag" from its parents set of children.
        if (
            original_linkage.parent is not None
            and tag in self.linkage[original_linkage.parent].children
        ):
            self.linkage[original_linkage.parent].children.remove(tag)

        # Replace tag's parent.
        linkage = replace(original_linkage, parent=new_parent)
        self.linkage[tag] = linkage

        # Add "tag" to its new parent's set of children.
        if linkage.parent is not None:
            self.linkage[linkage.parent].children.add(tag)
            self.update_metrics(linkage.parent)

        # Recompute spanning tree metrics.
        if original_linkage.parent is not None:
            self.update_metrics(original_linkage.parent)

    def update_metrics(self, tag):
        """
        Update metrics *above* a node that was moded.  When a node is
        moved from one parent to another, update_metrics() should be
        called for both of the parents (not the node moved)
        """
        while tag is not None:
            linkage = self.linkage[tag]
            if linkage.children:
                child_depth = max(
                    [self.linkage[child].depth for child in linkage.children]
                )
                descendents = sum(
                    [self.linkage[child].descendents for child in linkage.children]
                )
            else:
                child_depth = 0
                descendents = 0
            self.linkage[tag] = replace(
                linkage, depth=child_depth + 1, descendents=descendents + 1
            )
            tag = linkage.parent

    def _remove_edge(self, parent_tag, child_tag):
        # Don't remove the edge if current_tag is still the parent of
        # older_tag.
        if self.linkage[parent_tag].parent != child_tag:
            del self.diffs[parent_tag, child_tag]
        else:  # pragma: no cover
            raise RuntimeError(f"Trying to remove an essential edge")

    def _path_to(self, tag: Hashable) -> Sequence[Hashable]:
        """
        Function to retrieve the path to a version.
        """
        if tag not in self.linkage:  # pragma: no cover
            raise ValueError(f"{tag} is not a valid version.")

        path = []
        while tag is not None:
            path.append(tag)
            tag = self.linkage[tag].parent

        return tuple(reversed(path))

    def _retrieve_using_path(self, path: Sequence[Hashable]):
        """
        Function to retrieve a version give its path.

        This is intended for internal use in this module.
        """
        # Initialize with root_version,
        # then apply all of the patches in the path.
        patched = self.versions[path[0]]

        for n1, n2 in zip(path, path[1:]):
            reduced_changeset = self.diffs[n1, n2]
            patched = apply_forward(reduced_changeset, patched)

        return patched

    def _retrieve_raw(self, tag: Hashable) -> Sequence[Hashable]:
        """
        Retrieve a specific raw (meaning it's left tokenized) version
        using its tag.
        """
        if tag in self.versions:
            raw = self.versions[tag]
        else:
            path = self._path_to(tag)
            raw = self._retrieve_using_path(path)

        return raw

    def retrieve(self, tag: Hashable) -> TokenSequence:
        """
        Retrieve a specific version using its tag.
        """
        raw = self._retrieve_raw(tag)

        if self.decoder is None:
            return raw
        else:
            return self.decoder(cast(Sequence[int], raw), self.token_map)
