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
class Changeset:
    prefix: Changeset | LeafChangeset
    suffix: Changeset | LeafChangeset
    common: str

    def __str__(self) -> str:
        return str(self.prefix) + escape(self.common) + str(self.suffix)


@dataclass
class LeafChangeset:
    original: str
    modified: str
    original_position: int
    modified_position: int

    def __str__(self) -> str:
        result = ""
        if self.original:
            result += f"[red strike]{escape(self.original)}[/]"
            # result += f"[delete]{escape(self.original)}[/delete]"
        if self.modified:
            result += f"[green]{escape(self.modified)}[/]"
            # result += f"[insert]{escape(self.original)}[/insert]"
        return result


def compute_changesets(
    original: str, modified: str, original_position: int = 0, modified_position: int = 0
) -> Changeset | LeafChangeset:
    original_automaton = build(original)
    lcs_position_original, lcs_position_modified, length = find_lcs(
        original_automaton, modified
    )

    if length == 0:
        changeset = LeafChangeset(
            original=original,
            modified=modified,
            original_position=original_position,
            modified_position=modified_position,
        )
    else:
        common = original[lcs_position_original : lcs_position_original + length]
        prefix = compute_changesets(
            original[:lcs_position_original],
            modified[:lcs_position_modified],
            original_position=original_position,
            modified_position=modified_position,
        )
        suffix = compute_changesets(
            original[lcs_position_original + length :],
            modified[lcs_position_modified + length :],
            original_position=original_position + lcs_position_original + length,
            modified_position=modified_position + lcs_position_modified + length,
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

    console.print(str(changesets))
    # print(str(changesets))
