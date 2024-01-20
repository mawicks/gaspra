from collections.abc import Iterable, Sequence
from typing import cast, Generic, Protocol, TypeVar
import re

from gaspra.types import Change, DiffIterable, TokenIterable, TokenSequence, Token
from gaspra.changesets import diff_token_sequences
from gaspra.merge import merge_token_sequence

SYMBOLS = re.compile(r"[\w\d$-]+|.|\n")


def line_encode_strings(
    *string_set: str,
):
    encoded = []
    encoding = {}

    for s in string_set:
        lines = s.split("\n")

        for line in lines:
            if line not in encoding:
                encoding[line] = len(encoding)

        encoded.append(tuple(encoding[line] for line in lines))
    decoding = tuple(encoding.keys())
    return tuple([decoding, *encoded])


BytesOrStr = TypeVar("BytesOrStr", bytes, str)


def generic_decode(
    contents: Iterable[int], decoding: Sequence[BytesOrStr], separator: BytesOrStr
):
    return separator.join(decoding[t] for t in contents)


def generic_encode(
    unencoded_tokens: Iterable[BytesOrStr], encoding: dict[BytesOrStr, int]
):
    for token in unencoded_tokens:
        if token not in encoding:
            encoding[token] = len(encoding)

    decoding = tuple(k for k, _ in encoding.items())

    return tuple(encoding[token] for token in unencoded_tokens), decoding


class Tokenizer(Protocol, Generic[BytesOrStr]):
    def encode(self, contents: BytesOrStr) -> TokenSequence:
        raise NotImplementedError

    def decode(self, contents: TokenIterable) -> BytesOrStr:
        raise NotImplementedError


# In the Tokenizer implementations, we do a lot of casing under the
# assumption that to_bytes()/to_str() is only called on something
# produced by from_bytes()/from_str() from the same tokenizer.  The
# caller shouldn't care what's in the result of from from_bytes other
# than being Iterable[Hashable] so that it can be passed to the suffix
# automaton code, and the caller should only call to_bytes() on
# something produced by from_bytes() using the same tokenizer.
# Likewise, to_str() should only be called on something produced by
# from_str() from the same tokenizer.  Calling to_str() on something
# produced by from_bytes() may not even produce a string.

# Here, we assume the input streams are str or byte (typically UTF-8).
# Often we use byte so that we don't need to know anything about the
# encoding of the input.  It could juse as well be UTF-8, ISO-8859-x or
# a binary file.  LineTokenizer should work fine on bytes using many
# different text encodings (UTF-8, # ISO-8859-x, etc.) Lines are lines
# in all common encodings.  NullTokenizer could split a multibyte
# unicode character so its from_bytes() method should only be used on
# binary files or files known not to contain multi-byte characters.
# UTF8Tokenizer is probably safer for text known to be UTF-8 encoded,
# but likely slower.


class NullTokenizer(Generic[BytesOrStr]):
    source_type: type | None = None

    """
    The methods in NullTokenizer are no-ops.  NullTokenizer
    is used to simplifiy code by always requiring a tokenizer.
    """

    def encode(self, contents: BytesOrStr) -> BytesOrStr:
        if self.source_type and self.source_type != type(contents):
            raise RuntimeError("Can't mix type of 'contents' in different calls.")

        self.source_type = type(contents)
        return contents

    def decode(self, contents: TokenIterable) -> BytesOrStr:
        return cast(BytesOrStr, contents)


class CharTokenizer(Generic[BytesOrStr]):
    source_type: type | None = None

    def encode(self, contents: BytesOrStr) -> Sequence[int]:
        if self.source_type and self.source_type != type(contents):
            raise RuntimeError("Can't mix type of 'contents' in different calls.")

        self.source_type = type(contents)

        if isinstance(contents, bytes):
            return tuple(ord(c) for c in contents.decode("utf-8"))
        else:
            return tuple(ord(c) for c in contents)

    def decode(self, contents: TokenIterable) -> BytesOrStr:
        if self.source_type is bytes:
            return cast(
                BytesOrStr,
                b"".join(chr(cast(int, code)).encode("utf-8") for code in contents),
            )
        else:
            return cast(
                BytesOrStr,
                "".join(chr(cast(int, code)) for code in contents),
            )


class LineTokenizer(Generic[BytesOrStr]):
    source_type: type | None = None

    bytes_encoding: dict[BytesOrStr, int]
    bytes_decoding: Sequence[BytesOrStr]

    def __init__(self):
        self.bytes_encoding = {}

    def encode(self, contents: BytesOrStr) -> Sequence[int]:
        if self.source_type and self.source_type != type(contents):
            raise RuntimeError("Can't mix type of 'contents' in different calls.")
        self.source_type = type(contents)

        if isinstance(contents, bytes):
            # As long as the contents of lines are treated as atomic,
            # there's no need to decode them before splitting them.
            split_on = cast(BytesOrStr, b"\n")
        else:
            split_on = cast(BytesOrStr, "\n")

        split = cast(list[BytesOrStr], contents.split(split_on))
        lines = [*(line + split_on for line in split[:-1]), split[-1]]
        encoded, self.bytes_decoding = generic_encode(lines, self.bytes_encoding)
        return encoded

    def decode(self, contents: Iterable[Token]) -> BytesOrStr:
        contents = cast(Iterable[int], contents)
        if self.source_type is bytes:
            joiner = b""
        else:
            joiner = ""
        return generic_decode(contents, self.bytes_decoding, cast(BytesOrStr, joiner))


class SymbolTokenizer(Generic[BytesOrStr]):
    source_type: type | None = None

    encoding: dict[BytesOrStr, int]
    decoding: Sequence[BytesOrStr]

    def __init__(self):
        self.encoding = {}

    def encode(self, contents: BytesOrStr) -> Sequence[int]:
        if self.source_type and self.source_type != type(contents):
            raise RuntimeError("Can't mix type of 'contents' in different calls.")
        self.source_type = type(contents)

        if type(contents) is bytes:
            unencoded_tokens = [
                token[0].encode("utf-8")
                for token in SYMBOLS.finditer(contents.decode("utf-8"))
            ]
        elif type(contents) is str:
            unencoded_tokens = [token[0] for token in SYMBOLS.finditer(contents)]
        else:
            raise RuntimeError(f"Unexpected type of contents: {type(contents)}")

        unencoded_tokens = cast(list[BytesOrStr], unencoded_tokens)
        encoded, self.decoding = generic_encode(unencoded_tokens, self.encoding)
        return encoded

    def decode(self, contents: TokenIterable) -> bytes:
        contents = cast(Iterable[int], contents)

        if self.source_type == bytes:
            joiner = b""
        else:
            joiner = ""

        return generic_decode(contents, self.decoding, cast(BytesOrStr, joiner))


def decode_and_transform_changes(
    changes: DiffIterable, tokenizer: Tokenizer, transform=lambda _: _
) -> DiffIterable:
    """
    Decode a changeset.  Changesets are first computed on token stream.
    This function decodes each token in a Changeestto a str or a bytes
    object.

    It also applies an optional function escape() to the result.
    """
    for change in changes:
        if isinstance(change, Change):
            yield Change(
                transform(tokenizer.decode(change.a)),
                transform(tokenizer.decode(change.b)),
            )
        else:
            yield transform(tokenizer.decode(change))


def diff(
    original, modified, tokenizer: Tokenizer = NullTokenizer(), transformer=lambda _: _
):
    """
    High level diff() call that optionally encodes the sequences to be
    compared, compares the sequences, decodes, and transforms the
    result.  This is the diff() function for most use cases.

    """
    encoded_original = tokenizer.encode(original)
    encoded_modified = tokenizer.encode(modified)

    changes = diff_token_sequences(encoded_original, encoded_modified)
    transformed = decode_and_transform_changes(changes, tokenizer, transformer)
    return transformed


def merged(
    parent,
    current,
    other,
    tokenizer: Tokenizer = NullTokenizer(),
    transformer=lambda _: _,
):
    """
    High level diff() call that optionally encodes the sequences to be
    compared, compares the sequences, decodes, and transforms the
    result.  This is the diff() function for most use cases.

    """
    encoded_parent = tokenizer.encode(parent)
    encoded_current = tokenizer.encode(current)
    encoded_other = tokenizer.encode(other)

    changes = merge_token_sequence(encoded_parent, encoded_current, encoded_other)
    merged = decode_and_transform_changes(changes, tokenizer, transformer)
    return merged
