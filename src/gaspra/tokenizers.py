from collections.abc import Iterable, Sequence
from typing import cast, Protocol
import re

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


def generic_decode(
    contents: Iterable[int], decoding: Sequence[bytes], separator: bytes
):
    return separator.join(decoding[t] for t in contents)


def encode(unencoded_tokens: Iterable[bytes], encoding: dict[bytes, int]):
    for token in unencoded_tokens:
        if token not in encoding:
            encoding[token] = len(encoding)

    decoding = tuple(k for k, _ in encoding.items())

    return tuple(encoding[token] for token in unencoded_tokens), decoding


class Tokenizer(Protocol):
    separator: bytes

    def from_bytes(self, contents: bytes) -> Sequence[int]:
        raise NotImplemented

    def to_bytes(self, contents: Iterable[int]) -> bytes:
        raise NotImplemented


# Here, we assume the input streams are sequences of bytes, typically
# UTF-8.  That way, we don't worry about the encoding of the input file.
# It could juse as well be UTF-8, ISO-8859-x or a binary file.
# LineTokenizer should work fine on many text encodings (UTF-8,
# ISO-8859-x, etc.) Lines are lines in all common encodings.
# ByteTokenizer could split a multibyte unicode character so it should
# only be used on binary files or files known not to contain multi-byte
# characters.  UTF8Tokenizer is probably safer for text known to be
# UTF-8 encoded, but likely slower.  For the time being, SymbolTokenizer
# tokenizes sequences of ASCII alphanumeric symbols.  All other bytes
# get encoded as single tokens, so words with non-ASCII characters would
# get encoded as several tokens.  This should be safe but might produce
# unintuitive results.  If you want to group on "words" or "symbols"
# containing non-ASCII characters, you would need to do some combination
# of UTF8Tokenizer and SymbolTokernizer that decodes the bytes, groups
# the characters into tokens, and then encodes the tokens.
class ByteTokenizer:
    separator = b""

    def from_bytes(self, contents: bytes) -> Sequence[int]:
        return contents

    def to_bytes(self, contents: Iterable[int]) -> bytes:
        return cast(bytes, contents)


class UTF8Tokenizer:
    separator = b""

    def from_bytes(self, contents: bytes) -> Sequence[int]:
        return tuple(ord(c) for c in contents.decode("utf-8"))

    def to_bytes(self, contents: Iterable[int]) -> bytes:
        return "".join(chr(code) for code in contents).encode("utf-8")


class LineTokenizer:
    separator = "\n"
    encoding: dict[bytes, int]
    decoding: Sequence[bytes]

    def __init__(self):
        self.encoding = {}

    def from_bytes(self, contents: bytes) -> Sequence[int]:
        lines = contents.split(b"\n")

        encoded, self.decoding = encode(lines, self.encoding)
        return encoded

    def to_bytes(self, contents: Iterable[int]) -> bytes:
        return generic_decode(contents, self.decoding, b"\n")


class SymbolTokenizer:
    separator = b""

    encoding: dict[bytes, int]
    decoding: Sequence[bytes]

    def __init__(self):
        self.encoding = {}

    def from_bytes(self, contents: bytes) -> Sequence[int]:
        unencoded_tokens = [
            token[0].encode("utf-8")
            for token in SYMBOLS.finditer(contents.decode("utf-8"))
        ]

        encoded, self.decoding = encode(unencoded_tokens, self.encoding)
        return encoded

    def to_bytes(self, contents: Iterable[int]) -> bytes:
        return generic_decode(contents, self.decoding, b"")


class SpaceTokenizer:
    separator = b" "
    encoding: dict[bytes, int]
    decoding: Sequence[bytes]

    def __init__(self):
        self.encoding = {}

    def from_bytes(self, contents: bytes) -> Sequence[int]:
        unencoded_tokens = contents.split(b" ")

        encoded, self.decoding = encode(unencoded_tokens, self.encoding)
        return encoded

    def to_bytes(self, contents: Iterable[int]) -> bytes:
        return generic_decode(contents, self.decoding, b" ")
