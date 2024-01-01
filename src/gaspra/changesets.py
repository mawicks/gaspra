from __future__ import annotations
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass
from itertools import chain
import os

from gaspra.common import DATA_DIR
from gaspra.suffix_automaton import build, find_lcs
from gaspra.types import Change, ChangeIterable, TokenSequence


@dataclass
class CopyFragment:
    insert: str | TokenSequence
    length: int


@dataclass
class ChangeFragment:
    insert: str | TokenSequence
    delete: str | TokenSequence
    length: int


@dataclass
class ConflictFragment:
    version1: str | TokenSequence
    version2: str | TokenSequence


@dataclass
class ChangesetLeaf:
    original: str | TokenSequence
    modified: str | TokenSequence

    original_slice: slice
    modified_slice: slice

    def _fragments(
        self, _: str | TokenSequence
    ) -> Iterable[ChangeFragment | CopyFragment]:
        # Construction of the tree creates "empty" changesets.
        # Omit those from the output stream.
        if self.modified or self.original:
            yield ChangeFragment(
                insert=self.modified,
                delete=self.original,
                length=len(
                    self.original,
                ),
            )

    def fragments(self, _: str | TokenSequence) -> ChangeIterable:
        # Construction of the tree creates "empty" changesets.
        # Omit those from the output stream.
        if self.modified or self.original:
            yield Change(self.modified, self.original)

    def apply_forward(self, _: str | TokenSequence):
        yield self.modified

    def apply_reverse(self, _: str | TokenSequence):
        yield self.original

    # Exclude __str__ from coverage because it's only used for debugging.
    def __str__(self):  # pragma: no cover
        result = ""
        if self.original:
            result += f"original: {self.original}\n"
        if self.modified:
            result += f"modified: {self.modified}\n"
        return result


@dataclass
class Changeset:
    common_original: slice
    common_modified: slice

    prefix: Changeset | ChangesetLeaf
    suffix: Changeset | ChangesetLeaf

    def _fragments(
        self, original: str | TokenSequence
    ) -> Iterable[ChangeFragment | CopyFragment]:
        yield from self.prefix._fragments(original)
        copy = original[self.common_original]
        yield CopyFragment(insert=copy, length=len(copy))
        yield from self.suffix._fragments(original)

    def fragments(self, original: str | TokenSequence) -> ChangeIterable:
        yield from self.prefix.fragments(original)
        yield original[self.common_original]
        yield from self.suffix.fragments(original)

    def apply_forward(self, original: str | TokenSequence):
        yield from self.prefix.apply_forward(original)
        yield original[self.common_original]
        yield from self.suffix.apply_forward(original)

    def apply_reverse(self, modified: str | TokenSequence):
        yield from self.prefix.apply_reverse(modified)
        yield modified[self.common_modified]
        yield from self.suffix.apply_reverse(modified)

    # Exclude __str__ from coverage because it's only used for debugging.
    def __str__(self):  # pragma: no cover
        s_original = f"{self.common_original.start}:{self.common_original.stop}"
        s_modified = f"{self.common_modified.start}:{self.common_modified.stop}"
        return f"original[{s_original}]/modified[{s_modified}]\n"


def diff(
    original: str | TokenSequence, modified: str | TokenSequence
) -> ChangeIterable:
    """Returns the changes between a and b.

    Arguments:
        original: str
            The "original" tring
        modified: str
            The "modified" string

    Returns:
        Iterable[str]
            The changes between a and b.  Each item in the sequence is
            either a string or a tuple of two strings.  If the item is a
            string, it is unchanged test between `original` and
            ``modified`.  If the item is a [named] tuple, the first
            string is the string inserted at that point in `original` to
            get `modified` and the second string is the string that was
            deleted.

    """
    changeset = find_changeset(original, modified)
    yield from changeset.fragments(original)


def find_changeset(
    original: str | TokenSequence,
    modified: str | TokenSequence,
    original_slice: slice = slice(0, None),
    modified_slice: slice = slice(0, None),
) -> Changeset | ChangesetLeaf:
    automaton_original = build(original[original_slice])

    common_offset_original, common_offset_modified, common_length = find_lcs(
        automaton_original, modified[modified_slice]
    )

    if common_length == 0:
        changeset = ChangesetLeaf(
            original=original[original_slice],
            modified=modified[modified_slice],
            original_slice=original_slice,
            modified_slice=modified_slice,
        )
    else:
        common_original = slice(
            original_slice.start + common_offset_original,
            original_slice.start + common_offset_original + common_length,
        )
        common_modified = slice(
            modified_slice.start + common_offset_modified,
            modified_slice.start + common_offset_modified + common_length,
        )

        prefix = find_changeset(
            original,
            modified,
            slice(original_slice.start, common_original.start),
            slice(modified_slice.start, common_modified.start),
        )
        suffix = find_changeset(
            original,
            modified,
            slice(common_original.stop, original_slice.stop),
            slice(common_modified.stop, modified_slice.stop),
        )
        changeset = Changeset(
            prefix=prefix,
            suffix=suffix,
            common_original=common_original,
            common_modified=common_modified,
        )

    return changeset


def join_changes(version, changed):
    if type(version) is bytes or type(version) is str:
        patched_version = version[0:0].join(changed)
    else:
        patched_version = tuple(chain(*changed))
    return patched_version


def apply_forward(changeset, original: Sequence[Hashable]):
    changes = changeset.apply_forward(original)
    return join_changes(original, changes)


def apply_reverse(changeset, modified: str):
    changes = changeset.apply_reverse(modified)
    return join_changes(modified, changes)


if __name__ == "__main__":  # pragma: no cover
    from rich.console import Console

    console = Console(highlight=False)

    with open(os.path.join(DATA_DIR, "file1")) as file1, open(
        os.path.join(DATA_DIR, "file2")
    ) as file2:
        version = file1.read()
        modified = file2.read()

    changeset = find_changeset(version, modified)

    patched_original = apply_forward(changeset, version)
    reverse_patched_modified = apply_reverse(changeset, modified)

    assert patched_original == modified
    assert reverse_patched_modified == version
