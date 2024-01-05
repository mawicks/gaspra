from __future__ import annotations
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass
from itertools import chain
import os

from gaspra.common import DATA_DIR
from gaspra.suffix_automaton import build, find_lcs
from gaspra.types import (
    Change,
    ChangeIterable,
    ReducedChangeIterable,
    StrippedChangeIterable,
    TokenSequence,
)


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

    def _stream(
        self, _: str | TokenSequence
    ) -> Iterable[ChangeFragment | CopyFragment]:
        """Turn tree into a stream for additional processing.
        Construction of the tree creates "empty" changesets.  Omit those
        from the output stream."""
        if self.modified or self.original:
            yield ChangeFragment(
                insert=self.modified,
                delete=self.original,
                length=len(
                    self.original,
                ),
            )

    def diff_stream(self, _: str | TokenSequence) -> ChangeIterable:
        """Produce a simpler output stream than _stream() suitable
        or building diff output."""

        # Construction of the tree creates "empty" changesets.
        # Omit those from the output stream.
        if self.modified or self.original:
            yield Change(self.modified, self.original)

    def change_stream(self) -> ReducedChangeIterable:
        """Produce a simple output stream containing only changes.

        Elements of the stream are 1) tuple with pairs of
        slices of common fragments from the two strings and 2) named
        tuple pairs of type `Change` for fragments that are different.
        The simpler objects can returned to a caller without exposing
        the Change tree implementation."""

        # Construction of the tree creates "empty" changesets.  Omit
        # those from the output stream.
        if self.modified or self.original:
            yield Change(self.modified, self.original)

    def old_apply_forward(self, _: str | TokenSequence):
        yield self.modified

    def old_apply_reverse(self, _: str | TokenSequence):
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

    def _stream(
        self, original: str | TokenSequence
    ) -> Iterable[ChangeFragment | CopyFragment]:
        """Turn tree into a stream for additional processing."""

        # Construction of the tree creates "empty" changesets.  Omit
        # those from the output stream.

        yield from self.prefix._stream(original)
        copy = original[self.common_original]
        yield CopyFragment(insert=copy, length=len(copy))
        yield from self.suffix._stream(original)

    def diff_stream(self, original: str | TokenSequence) -> ChangeIterable:
        """Produce a simpler output stream than _stream() suitable
        or building diff output."""

        yield from self.prefix.diff_stream(original)
        yield original[self.common_original]
        yield from self.suffix.diff_stream(original)

    def change_stream(self) -> ReducedChangeIterable:
        """Produce a simple output stream containing only changes.

        Elements of the stream are 1) tuple with pairs of
        slices of common fragments from the two strings and 2) named
        tuple pairs of type `Change` for fragments that are different.
        The simpler objects can returned to a caller without exposing
        the Change tree implementation."""

        yield from self.prefix.change_stream()
        yield (self.common_original, self.common_modified)
        yield from self.suffix.change_stream()

    def old_apply_forward(self, original: str | TokenSequence):
        yield from self.prefix.old_apply_forward(original)
        yield original[self.common_original]
        yield from self.suffix.old_apply_forward(original)

    def old_apply_reverse(self, modified: str | TokenSequence):
        yield from self.prefix.old_apply_reverse(modified)
        yield modified[self.common_modified]
        yield from self.suffix.old_apply_reverse(modified)

    # Exclude __str__ from coverage because it's only used for debugging.
    def __str__(self):  # pragma: no cover
        s_original = f"{self.common_original.start}:{self.common_original.stop}"
        s_modified = f"{self.common_modified.start}:{self.common_modified.stop}"
        return f"original[{s_original}]/modified[{s_modified}]\n"


def strip_forward(stream: ReducedChangeIterable) -> StrippedChangeIterable:
    """Return just the forward changes from a changeset."""
    for change in stream:
        if isinstance(change, Change):
            yield change.a
        else:
            yield change[0]


def strip_reverse(stream: ReducedChangeIterable) -> StrippedChangeIterable:
    """Return just the reverse changes from a changeset."""
    for change in stream:
        if isinstance(change, Change):
            yield change.b
        else:
            yield change[1]


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
    yield from changeset.diff_stream(original)


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


def apply(stripped_changeset: StrippedChangeIterable, version: Sequence[Hashable]):
    """
    Apply a changeset to a version sequence.

    A StrippedChangeIterable is produced from strip_forward() or strip_reverse()
    has no sense of direction.  It just applies the changes to the string.
    """

    def _apply():
        for item in stripped_changeset:
            if type(item) is slice:
                yield version[item]
            else:
                yield item

    return join_changes(version, _apply())


def apply_forward(
    reduced_changeset: ReducedChangeIterable, original: Sequence[Hashable]
):
    return apply(strip_forward(reduced_changeset), original)


def apply_reverse(
    reduced_changeset: ReducedChangeIterable, modified: Sequence[Hashable]
):
    return apply(strip_reverse(reduced_changeset), modified)


def old_apply_forward(changeset, original: Sequence[Hashable]):
    changes = changeset.old_apply_forward(original)
    return join_changes(original, changes)


def old_apply_reverse(changeset, modified: str):
    changes = changeset.old_apply_reverse(modified)
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

    patched_original = old_apply_forward(changeset, version)
    reverse_patched_modified = old_apply_reverse(changeset, modified)

    assert patched_original == modified
    assert reverse_patched_modified == version
