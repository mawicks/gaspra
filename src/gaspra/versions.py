from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass, field

from gaspra.changesets import Changeset, ChangesetLeaf, find_changeset, apply_forward
from gaspra.revision_tree import Tree
from gaspra.types import TokenSequence


@dataclass
class Versions:
    root_version: TokenSequence | None = None
    root_tag: Hashable | None = None

    tree: Tree = field(default_factory=Tree)
    diffs: dict[Hashable, Changeset | ChangesetLeaf] = field(default_factory=dict)

    def save(self, version_id: Hashable, version: TokenSequence):
        required_changesets, expired_changesets, old_path = self.tree.insert(version_id)
        for tag_1, tag_2 in required_changesets:
            # tag_1 should always match version_id
            if tag_1 == version_id:
                version_1 = version
            else:
                raise RuntimeError(f"{tag_1} was expected to be {version_id}")

            # tag_2 should never be version_id but could be root_tag
            # or some other tag.
            if tag_2 == self.root_tag:
                version_2 = self.root_version
            else:
                version_2 = self.retrieve_using_path(tuple(old_path))

            self.diffs[tag_1, tag_2] = find_changeset(version_1, version_2)

        for tag_1, tag_2 in expired_changesets:
            del self.diffs[tag_1, tag_2]

        self.root_tag = version_id
        self.root_version = version
        return

    def retrieve_using_path(self, path: Sequence[Hashable]):
        if self.root_version is None:
            raise ValueError("Versions have not been initialized.")

        # Initialize with root_version,
        # then apply all of the patches in the path.
        patched = self.root_version

        for n1, n2 in zip(path, path[1:]):
            changeset = self.diffs[n1, n2]
            patched = apply_forward(changeset, patched)

        return patched

    def retrieve(self, version_id: Hashable) -> TokenSequence:
        if self.root_version is None:
            raise ValueError("Versions have not been initialized.")

        if version_id == self.root_tag and self.root_version:
            return self.root_version

        path = self.tree.path_to(version_id)

        return self.retrieve_using_path(path)
