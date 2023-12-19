from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, replace
import os

from rich.console import Console

from string_matching.common import DATA_DIR
from string_matching.suffix_automaton import build, find_lcs

console = Console(highlight=False)


@dataclass
class CopyFragment:
    insert: str
    length: int


@dataclass
class ChangeFragment:
    insert: str
    delete: str
    length: int


@dataclass
class ConflictFragment:
    version1: str
    version2: str
    length: int


@dataclass
class ChangesetLeaf:
    original: str
    modified: str

    original_slice: slice
    modified_slice: slice

    def changes(self):
        yield self

    def fragments(self, __ignored__):
        # Construction of the tree creates "empty" changesets.
        # Omit those from the output stream.
        if self.modified or self.original:
            yield ChangeFragment(
                insert=self.modified, delete=self.original, length=len(self.original)
            )

    def apply_forward(self, __ignored__: str):
        yield self.modified

    def apply_reverse(self, __ignored__: str):
        yield self.original

    def show(self, __original__: str, __modified__: str) -> str:
        result = ""

        if self.original:
            result += f"[red strike]{escape(self.original)}[/]"
            # result += f"[delete]{escape(self.original_str)}[/delete]"
        if self.modified:
            result += f"[green]{escape(self.modified)}[/]"
        # result += f"[insert]{escape(self.modified_str)}[/insert]"

        return result

    def __str__(self):
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

    def changes(self):
        yield from self.prefix.changes()
        yield self
        yield from self.suffix.changes()

    def fragments(self, original):
        yield from self.prefix.fragments(original)
        copy = original[self.common_original]
        yield CopyFragment(insert=copy, length=len(copy))
        yield from self.suffix.fragments(original)

    def apply_forward(self, original: str):
        yield from self.prefix.apply_forward(original)
        yield original[self.common_original]
        yield from self.suffix.apply_forward(original)

    def apply_reverse(self, modified: str):
        yield from self.prefix.apply_reverse(modified)
        yield modified[self.common_modified]
        yield from self.suffix.apply_reverse(modified)

    def show(self, original: str, modified: str):
        return (
            self.prefix.show(original, modified)
            + escape(original[self.common_original])
            + self.suffix.show(original, modified)
        )

    def __str__(self):
        s_original = f"{self.common_original.start}:{self.common_original.stop}"
        s_modified = f"{self.common_modified.start}:{self.common_modified.stop}"
        return f"original[{s_original}]/modified[{s_modified}]\n"


def escape(s):
    return s.replace("[", r"\[")
    # return s


def find_changeset(
    original: str,
    modified: str,
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


def apply_forward(changeset, original: str):
    patched_original = "".join(changeset.apply_forward(original))
    return patched_original


def apply_reverse(changeset, modified: str):
    reverse_patched_modified = "".join(changeset.apply_reverse(modified))
    return reverse_patched_modified


if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "file1")) as file1, open(
        os.path.join(DATA_DIR, "file2")
    ) as file2:
        original = file1.read()
        modified = file2.read()

    changeset = find_changeset(original, modified)

    markup = changeset.show(original, modified)

    patched_original = apply_forward(changeset, original)
    reverse_patched_modified = apply_reverse(changeset, modified)

    assert patched_original == modified
    assert reverse_patched_modified == original

    console.print(markup)
