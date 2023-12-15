from __future__ import annotations
from dataclasses import dataclass
import os

from string_matching.common import DATA_DIR
from string_matching.suffix_automaton import build, find_lcs


@dataclass
class Changeset:
    prefix: Changeset | LeafChangeset
    suffix: Changeset | LeafChangeset
    common: str = ""

    def __str__(self) -> str:
        return str(self.prefix) + self.common + str(self.suffix)


@dataclass
class LeafChangeset:
    original: str = ""
    modified: str = ""

    def __str__(self) -> str:
        result = ""
        if self.original:
            result += f"<DELETE>{self.original}</DELETE>"
        if self.modified:
            result += f"<INSERT>{self.modified}</INSERT>"
        return result


def compute_changesets(original: str, modified: str) -> Changeset | LeafChangeset:
    original_automaton = build(original)
    original_position, modified_position, length = find_lcs(
        original_automaton, modified
    )

    if length == 0:
        changeset = LeafChangeset(original=original, modified=modified)
    else:
        common = original[original_position : original_position + length]
        prefix = compute_changesets(
            original[:original_position], modified[:modified_position]
        )
        suffix = compute_changesets(
            original[original_position + length :],
            modified[modified_position + length :],
        )
        changeset = Changeset(prefix=prefix, common=common, suffix=suffix)

    return changeset


if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "file1")) as file1, open(
        os.path.join(DATA_DIR, "file2")
    ) as file2:
        s1 = file1.read()
        s2 = file2.read()

    changesets = compute_changesets(s1, s2)

    print(changesets)
