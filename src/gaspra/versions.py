from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Callable, cast

from gaspra.changesets import (
    find_changeset,
    apply,
    strip_forward,
)
from gaspra.tree import Tree
from gaspra.types import StrippedChangeSequence


@dataclass
class VersionInfo:
    base_version: Hashable | None = None
    token_count: int = 0
    change_count: int = 0


@dataclass
class Versions:
    head_version: dict[Hashable, bytes] = field(default_factory=dict)
    diffs: dict[Hashable, StrippedChangeSequence] = field(default_factory=dict)
    tree: Tree = field(default_factory=Tree)

    # Encoder converts bytes to tokens (ints)
    encoder: Callable[[bytes, Mapping[bytes, int]], Sequence[int]] = lambda x, _: x
    # Decoder converts tokens (ints) to bytes
    decoder: Callable[[Sequence[int], Sequence[bytes]], bytes] = lambda x, _: cast(
        bytes, x
    )

    def add(self, tag: Hashable, version: bytes, existing_head: Hashable | None = None):
        # Encode/tokenize `version` if requested
        split, path_to_split = self.tree.add(tag, existing_head)

        self.head_version[tag] = version

        # `tag` always get existing_head as a child. It also
        # gets `split` as a child if it exists.  The order
        # of adding children is important to establish the
        # convention that older nodes appear in the child list
        # first.

        # If there is an appropriate split, move it up to be a child of `tag`
        if split is not None and path_to_split is not None and split != existing_head:
            split_version = self._retrieve_using_path(path_to_split)

            self._add_edge(
                tag,
                split,
                self._make_changeset(version, split_version),
            )
            self.tree.change_parent(split, tag)

        # If there was a pre-existing head, make it a child of `tag`
        if existing_head is not None:
            existing_head_version = self.head_version[existing_head]
            self._add_edge(
                tag,
                existing_head,
                self._make_changeset(version, existing_head_version),
            )

        return

    def _make_changeset(self, original: bytes, modified: bytes):
        encoding = {}
        decoding = ()
        encoded_original = self.encoder(original, encoding)
        encoded_modified = self.encoder(modified, encoding)
        decoding = tuple(encoding.keys())

        encoded_changeset = tuple(
            strip_forward(
                find_changeset(encoded_original, encoded_modified).change_stream()
            )
        )

        changeset = tuple(
            c if type(c) is slice else self.decoder(c, decoding)
            for c in encoded_changeset
        )
        return changeset

    def _add_edge(self, parent_tag, child_tag, changeset):
        self.diffs[child_tag] = changeset

        # It's a spanning tree so a node can have only one
        # parent.  When adding an edge, the new parent
        # steals the child from any pre-existing parent.
        self.tree.change_parent(child_tag, parent_tag)

        # Older tag is no longer at the head of a branch
        # so remove it from versions.
        if child_tag in self.head_version:
            del self.head_version[child_tag]

    def _retrieve_using_path(self, path: Sequence[Hashable]) -> bytes:
        """
        Function to retrieve a version give its path.

        This is intended for internal use in this module.
        """
        # Initialize with root_version,
        # then apply all of the patches in the path.
        patched = self.head_version[path[0]]
        encoding = {}
        encoded_patched = self.encoder(patched, encoding)

        for n2 in path[1:]:
            stripped_changeset = self.diffs[n2]
            encoded_stripped_changeset = tuple(
                c if type(c) is slice else self.encoder(c, encoding)
                for c in stripped_changeset
            )
            encoded_patched = apply(encoded_stripped_changeset, encoded_patched)

        decoding = tuple(encoding.keys())
        return self.decoder(encoded_patched, decoding)

    def get(self, tag: Hashable) -> bytes | None:
        """
        Retrieve a specific version using its tag.
        """
        if tag not in self.tree:
            return None

        if tag in self.head_version:
            raw = self.head_version[tag]
        else:
            path = self.tree.path_to(tag)
            raw = self._retrieve_using_path(path)

        return raw

    def version_info(self, tag: Hashable) -> VersionInfo | None:
        """
        Return information about a version.
        """
        if tag not in self.tree:
            return None

        if tag in self.diffs:
            changeset = self.diffs[tag]
            token_count = sum(len(c) for c in changeset if not isinstance(c, slice))
            change_count = len(changeset)
        else:
            token_count = len(self.head_version[tag])
            change_count = 0
        return VersionInfo(
            base_version=self.tree.base_version(tag),
            token_count=token_count,
            change_count=change_count,
        )

    def __contains__(self, tag: Hashable):
        return tag in self.tree
