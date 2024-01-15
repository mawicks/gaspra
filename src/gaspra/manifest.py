import json
from collections.abc import Hashable, Mapping
from gaspra.versions import Versions
from gaspra.types import Tag

Manifest = dict[Tag, Tag]


def add_manifest(
    manifest_tag: Hashable,
    manifest: Manifest,
    versions: Versions,
    contents: Mapping[Tag, bytes],
    base_tag: Hashable | None,
):
    base_manifest = None
    if base_tag is not None:
        base_manifest = versions.get(base_tag)
        if base_manifest is not None:
            base_manifest = doc_to_manifest(base_manifest)

    for name, tag in manifest.items():
        if tag not in versions:
            versions.add(
                tag,
                contents[tag],
                base_manifest[name] if base_manifest is not None else None,
            )

    manifest_doc = manifest_to_doc(manifest)
    versions.add(
        manifest_tag,
        manifest_doc,
        base_tag if base_tag is not None else None,
    )


def get_manifest(versions, tag: Hashable):
    manifest_doc = versions.get(tag)
    return doc_to_manifest(manifest_doc)


def manifest_to_doc(manifest: Manifest):
    return json.dumps(manifest, separators=(",\n", ":")).encode("utf-8")


def doc_to_manifest(manifest_doc: bytes):
    return json.loads(manifest_doc.decode("utf-8"))
