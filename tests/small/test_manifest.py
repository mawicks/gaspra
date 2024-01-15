import pytest

from gaspra.versions import Versions
from gaspra.manifest import add_manifest, doc_to_manifest, get_manifest, manifest_to_doc

# Define three "files" with multiple versions with different contents.
ITEM_CONTENTS = {
    # File zero changes on each commit
    "f0v0": b"a",
    "f0v1": b"ab",
    "f0v2": b"abc",
    "f0v3": b"abcd",
    # File one has three versions
    "f1v0": b"1",
    "f1v1": b"12",
    "f1v2": b"123",
    # File two has only two versions
    "f2v0": b"x",
    "f2v1": b"xy",
}

MANIFESTS = {
    "m0": {
        "f0": "f0v0",
        "f1": "f1v0",
        "f2": "f2v0",
    },
    # f0 and f1 change. f2 does not.
    "m1": {
        "f0": "f0v1",
        "f1": "f1v1",
        "f2": "f2v0",
    },
    # f0 and f1 change. f2 does not.
    "m2": {
        "f0": "f0v2",
        "f1": "f1v2",
        "f2": "f2v0",
    },
    # f0 and f2 change. f1 does not.
    "m3": {
        "f0": "f0v3",
        "f1": "f1v2",
        "f2": "f2v1",
    },
}


@pytest.fixture
def loaded_versions():
    versions = Versions()
    base_id = None
    for m_id, manifest in MANIFESTS.items():
        add_manifest(m_id, manifest, versions, ITEM_CONTENTS, base_id)
        base_id = m_id
    return versions


def test_conversions():
    for _, manifest in MANIFESTS.items():
        manifest_doc = manifest_to_doc(manifest)
        assert manifest == doc_to_manifest(manifest_doc)


def test_add_manifest_adds_manifests(loaded_versions):
    for m_id, manifest in MANIFESTS.items():
        assert manifest == get_manifest(loaded_versions, m_id)


def test_add_manifest_adds_all_items(loaded_versions):
    for tag, _ in ITEM_CONTENTS.items():
        assert tag in loaded_versions


def test_all_items_are_retrievable_from_loaded_versions(loaded_versions):
    for tag, contents in ITEM_CONTENTS.items():
        assert contents == loaded_versions.get(tag)


def test_all_items_have_correct_base_version(loaded_versions):
    for tag, _ in ITEM_CONTENTS.items():
        version_info = loaded_versions.version_info(tag)
        tag_version = int(tag[-1])
        if tag_version == 0:
            assert version_info.base_version is None
        else:
            base_tag_version = int(version_info.base_version[-1])
            assert base_tag_version == tag_version - 1


def test_all_non_head_items_are_stored_as_diffs(loaded_versions):
    last_manifest = list(MANIFESTS.keys())[-1]
    head_versions = set(MANIFESTS[last_manifest].values())
    for tag, contents in ITEM_CONTENTS.items():
        if tag not in head_versions:
            version_info = loaded_versions.version_info(tag)
            assert version_info.change_count > 0
            assert version_info.token_count < len(contents)
