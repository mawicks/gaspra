from gaspra.versions import Versions

from gaspra.tokenizers import space_tokenizer, space_token_decoder

VERSIONS = {
    0: "a b c d e f g",
    1: "a c e f g",
    2: "a c d x y g",
    3: "a c d x y g x y z",
    4: "d x y g x y z",
    5: "d x y g x y z q r s",
}


def test_versions():
    versions = Versions()

    base = None
    for id, version in VERSIONS.items():
        versions.save(id, version.encode("utf-8"), base)
        base = id

    base = None
    for id, version in VERSIONS.items():
        retrieved_version, base_version = versions.retrieve(id)

        assert retrieved_version == version.encode("utf-8")
        assert base_version == base

        base = id


def test_versions_with_tokenizer():
    versions = Versions(tokenizer=space_tokenizer, decoder=space_token_decoder)

    base = None
    for id, version in VERSIONS.items():
        versions.save(id, version.encode("utf-8"), base)
        base = id

    base = None
    for id, version in VERSIONS.items():
        retrieved_version, base_version = versions.retrieve(id)

        assert retrieved_version == version.encode("utf-8")
        assert base_version == base

        base = id
