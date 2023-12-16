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
class LeafChangeset:
    original: slice
    modified: slice

    def changes(self):
        yield self

    def show(self, original, modified) -> str:
        result = ""

        original_slice = original[self.original]
        modified_slice = modified[self.modified]

        if original_slice:
            result += f"[red strike]{escape(original_slice)}[/]"
            # result += f"[delete]{escape(self.original)}[/delete]"
        if modified_slice:
            result += f"[green]{escape(modified_slice)}[/]"
        # result += f"[insert]{escape(self.original)}[/insert]"
        return result

    def __str__(self):
        result = ""
        if self.original.stop is None or self.original.stop > self.original.start:
            result += f"original[{self.original.start}:{self.original.stop}]\n"
        if self.modified.stop is None or self.modified.stop > self.modified.start:
            result += f"modified[{self.modified.start}:{self.modified.stop}]\n"
        return result


@dataclass
class Changeset:
    common_original: slice
    common_modified: slice

    prefix: Changeset | LeafChangeset
    suffix: Changeset | LeafChangeset

    def changes(self):
        for change in self.prefix.changes():
            yield change

        yield self

        for change in self.suffix.changes():
            yield change

    def show(self, original, modified):
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
) -> Changeset | LeafChangeset:
    automaton_original = build(original[original_slice])

    common_offset_original, common_offset_modified, common_length = find_lcs(
        automaton_original, modified[modified_slice]
    )

    if common_length == 0:
        changeset = LeafChangeset(
            original=original_slice,
            modified=modified_slice,
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

    for changeset in changesets.changes():
        print(str(changeset))

    markup = changesets.show(original, modified)

    console.print(markup)

    # print(str(changesets))
