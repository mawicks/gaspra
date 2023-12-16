from __future__ import annotations
from dataclasses import dataclass
import os

from rich.console import Console

from string_matching.common import DATA_DIR
from string_matching.suffix_automaton import build, find_lcs

console = Console(highlight=False)


def escape(s):
    return s.replace("[", r"\[")
    # return s


@dataclass
class ChangesetLeaf:
    original: str
    modified: str

    original_slice: slice
    modified_slice: slice

    def changes(self):
        yield self

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
        for change in self.prefix.changes():
            yield change

        yield self

        for change in self.suffix.changes():
            yield change

    def apply_forward(self, original: str):
        for fragment in self.prefix.apply_forward(original):
            yield fragment

        yield original[self.common_original]

        for fragment in self.suffix.apply_forward(original):
            yield fragment

    def apply_reverse(self, modified: str):
        for fragment in self.prefix.apply_reverse(modified):
            yield fragment

        yield modified[self.common_modified]

        for fragment in self.suffix.apply_reverse(modified):
            yield fragment

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


def compute_changesets(
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

        prefix = compute_changesets(
            original,
            modified,
            slice(original_slice.start, common_original.start),
            slice(modified_slice.start, common_modified.start),
        )
        suffix = compute_changesets(
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


if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "file1")) as file1, open(
        os.path.join(DATA_DIR, "file2")
    ) as file2:
        original = file1.read()
        modified = file2.read()

    changesets = compute_changesets(original, modified)

    markup = changesets.show(original, modified)

    patched_original = "".join(changesets.apply_forward(original))
    reverse_patched_modified = "".join(changesets.apply_reverse(modified))

    assert patched_original == modified
    assert reverse_patched_modified == original

    console.print(markup)
