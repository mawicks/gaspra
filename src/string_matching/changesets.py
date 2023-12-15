from __future__ import annotations
from dataclasses import dataclass
import os

from string_matching.common import DATA_DIR
from string_matching.suffix_automaton import build, find_lcs


@dataclass
class Changeset:
    before: Changeset | None = None
    common: str = ""
    after: Changeset | None = None


def compute_changesets(s1: str, s2: str):
    if s1 == "" or s2 == "":
        changeset = Changeset()

    else:
        s1_automaton = build(s1)
        s1_position, s2_position, length = find_lcs(s1_automaton, s2)

        before = compute_changesets(s1[:s1_position], s2[:s2_position])
        common = s1[s1_position : s1_position + length]
        after = compute_changesets(s1[s1_position + length :], s2[s2_position + length])

        changeset = Changeset(before=before, common=common, after=after)

    return changeset


if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "file1")) as file1, open(
        os.path.join(DATA_DIR, "file2")
    ) as file2:
        s1 = file1.read()
        s2 = file2.read()

    change_sets = compute_change_sets(s1, s2)

    "Done"
