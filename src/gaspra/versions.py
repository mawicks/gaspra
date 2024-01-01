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
    root_version: TokenSequence = ""
    root_tag: Hashable | None = None

    tree: Tree = field(default_factory=Tree)
    diffs: dict[Hashable, ReducedChangeIterable] = field(default_factory=dict)
    tokenizer: Callable | None = None
    tokens: dict[str, int] = field(default_factory=dict)
    token_map: tuple[str, ...] = field(default_factory=tuple)

    def save(self, version_id: Hashable, version: str):
        required_changesets, expired_changesets, removed_paths = self.tree.insert(
            version_id
        )

        if self.tokenizer is None:
            tokenized = version
        else:
            tokenized = self.tokenizer(version, self.tokens)
            self.token_map = tuple(self.tokens.keys())

        for current_tag, older_tag in required_changesets:
            # The first tag should always match version_id (the version
            # being added).
            if current_tag != version_id:  # pragma: no cover
                raise RuntimeError(f"{current_tag} was expected to be {version_id}")

            # The second tag should never be version_id.  It will be either
            # the root_tag a tag associated with removed_paths.
            if older_tag == self.root_tag:
                older_version = self.root_version
            else:
                old_path = removed_paths[older_tag]
                older_version = self._retrieve_using_path(tuple(old_path))

            self.diffs[current_tag, older_tag] = tuple(
                find_changeset(tokenized, older_version).change_stream()
            )

        for current_tag, older_tag in expired_changesets:
            del self.diffs[current_tag, older_tag]

        self.root_tag = version_id
        self.root_version = tokenized
        return

    def _retrieve_using_path(self, path: Sequence[Hashable]):
        """
        Function to retrieve a version give its path.

        This is intended for internal use in this module.
        """
        if self.root_version is None:  # pragma: no cover
            raise ValueError("Versions have not been initialized.")

        # Initialize with root_version,
        # then apply all of the patches in the path.
        patched = self.root_version

        for n1, n2 in zip(path, path[1:]):
            reduced_changeset = self.diffs[n1, n2]
            patched = apply_forward(reduced_changeset, patched)

        return patched

    def retrieve(self, version_id: Hashable) -> TokenSequence:
        """
        Retrieve a specific version.
        """
        if self.root_version is None:  # pragma: no cover
            raise ValueError("Versions have not been initialized.")

        if version_id == self.root_tag and self.root_version:
            tokenized = self.root_version
        else:
            path = self.tree.path_to(version_id)
            tokenized = self._retrieve_using_path(path)

        if self.tokenizer is None:
            return tokenized
        else:
            return "\n".join(self.token_map[t] for t in cast(Sequence[int], tokenized))
