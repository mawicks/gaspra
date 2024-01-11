from gaspra.versions import Versions

from gaspra.encoders import SpaceEncoder

VERSIONS = {
    0: "a b c d e f g",
    1: "a c e f g",
    2: "a c d x y g",
    3: "a c d x y g x y z",
    4: "d x y g x y    z",
    5: "d x y g x y z q r    s",
}


def test_containment_changes_after_insertion():
    versions = Versions()

    base = None
    for id, version in VERSIONS.items():
        assert id not in versions
        assert versions.get(id) is None
        versions.add(id, version.encode("utf-8"), base)
        assert id in versions
        assert versions.get(id) is not None
        base = id


def test_retrieved_versions_match():
    versions = Versions()

    base = None
    for id, version in VERSIONS.items():
        versions.add(id, version.encode("utf-8"), base)
        base = id

    for id, version in VERSIONS.items():
        retrieved_version = versions.get(id)
        assert retrieved_version == version.encode("utf-8")


def test_versions_with_encoder():
    versions = Versions(tokenizer=SpaceEncoder)

    base = None
    for id, version in VERSIONS.items():
        versions.add(id, version.encode("utf-8"), base)
        base = id

    for id, version in VERSIONS.items():
        retrieved_version = versions.get(id)
        assert retrieved_version == version.encode("utf-8")
        base = id


def test_expected_version_info():
    versions = Versions()

    base = None
    for id, version in VERSIONS.items():
        versions.add(id, version.encode("utf-8"), base)

        # When a version is first inserted is should be stored verbatim.
        # We'll check the length later after all versions have been
        # added and then length should decrease.
        version_info = versions.version_info(id)
        assert version_info is not None
        assert version_info.token_count == len(version)
        assert base == version_info.base_version

        base = id

    base = None
    # All non-head versions should be diffs.
    for id, version in list(VERSIONS.items())[:-1]:
        version_info = versions.version_info(id)
        assert version_info is not None
        assert version_info.base_version == base
        assert version_info.token_count < len(version)
        assert version_info.change_count > 0

        base = id
