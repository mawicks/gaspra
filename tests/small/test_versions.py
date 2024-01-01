import pytest

from gaspra.versions import Versions

VERSIONS = {
    0: "a b c d e f g",
    1: "a c e f g",
    2: "a c d x y g",
    3: "a c d x y g x y z",
    4: "d x y g x y z",
    5: "d x y g x y z q r s",
}


def test_revisions():
    versions = Versions()

    for id, version in VERSIONS.items():
        versions.save(id, version)

    for id, version in VERSIONS.items():
        retrieved_version = versions.retrieve(id)

        assert retrieved_version == version
    "DONE"
