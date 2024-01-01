from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass, field
from typing import Callable, cast

from gaspra.changesets import (
    find_changeset,
    apply_forward,
)
from gaspra.revision_tree import Tree
from gaspra.types import TokenSequence, ReducedChangeIterable


@dataclass
class Versions:
    tree: Tree = field(default_factory=Tree)

    versions: dict[Hashable, Sequence[Hashable]] = field(default_factory=dict)
    diffs: dict[Hashable, ReducedChangeIterable] = field(default_factory=dict)
    parents: dict[Hashable, Hashable] = field(default_factory=dict)

    tokenizer: Callable[[bytes, dict[bytes, int]], Sequence[int]] | None = None
    tokens: dict[bytes, int] = field(default_factory=dict)
    token_map: tuple[bytes, ...] = field(default_factory=tuple)

    def save(self, tag: Hashable, version: bytes):
        changesets_to_create, changesets_to_remove = self.tree.insert(tag)

        if self.tokenizer is None:
            tokenized = version
        else:
            tokenized = self.tokenizer(version, self.tokens)
            self.token_map = tuple(self.tokens.keys())

        self.versions[tag] = tokenized

        for current_tag, older_tag in changesets_to_create:
            current_version = self.retrieve(current_tag)
            older_version = self.retrieve(older_tag)

            self._save_diff(
                current_tag,
                older_tag,
                tuple(find_changeset(current_version, older_version).change_stream()),
            )

        for current_tag, older_tag in changesets_to_remove:
            self._remove_branch(current_tag, older_tag)

        return

    def _save_diff(self, current_tag, older_tag, changeset):
        self.diffs[current_tag, older_tag] = changeset
        self.parents[older_tag] = current_tag
        if older_tag in self.versions:
            del self.versions[older_tag]

    def _remove_branch(self, current_tag, older_tag):
        del self.diffs[current_tag, older_tag]

        # This "if" should not be necessary because
        # parent[older_tag] should already have been overwritten.  It
        # currently doesn't get executed, but we'll leave it here
        # in case the order of calls ever gets changed.
        if self.parents.get(older_tag) == current_tag:
            del self.parents[older_tag]

    def _path_to(self, tag: Hashable) -> Sequence[Hashable]:
        """
        Function to retrieve the path to a version.
        """
        if tag not in self.parents:  # pragma: no cover
            raise ValueError(f"{tag} is not a valid version.")

        path = [tag]
        while tag in self.parents:
            tag = self.parents[tag]
            path.append(tag)

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

    def retrieve(self, tag: Hashable) -> TokenSequence:
        """
        Retrieve a specific version using its tag.
        """
        if tag in self.versions:
            tokenized = self.versions[tag]
        else:
            path = self._path_to(tag)
            tokenized = self._retrieve_using_path(path)

        if self.tokenizer is None:
            return tokenized
        else:
            return b"\n".join(self.token_map[t] for t in cast(Sequence[int], tokenized))
