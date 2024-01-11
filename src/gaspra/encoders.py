from collections.abc import Iterable, Sequence
from typing import Protocol
import re

TOKENS = re.compile(rb"[A-Za-z0-9$-]+|.|\n")


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

    def encode(self, contents: bytes):
        raise NotImplemented

    def decode(self, contents: Iterable[int]):
        raise NotImplemented


class NullTokenizer:
    separator = b""

    def encode(self, contents: bytes) -> Sequence[int]:
        return contents

    def decode(self, contents: bytes) -> bytes:
        return contents


class LineEncoder:
    separator = "\n"
    encoding: dict[bytes, int]
    decoding: Sequence[bytes]

    def __init__(self):
        self.encoding = {}

    def encode(self, contents: bytes) -> Sequence[int]:
        lines = contents.split(b"\n")

        encoded, self.decoding = encode(lines, self.encoding)
        return encoded

    def decode(self, contents: Iterable[int]) -> bytes:
        return generic_decode(contents, self.decoding, b"\n")


class SpaceEncoder:
    separator = b" "
    encoding: dict[bytes, int]
    decoding: Sequence[bytes]

    def __init__(self):
        self.encoding = {}

    def encode(self, string: bytes) -> Sequence[int]:
        unencoded_tokens = string.split(b" ")

        encoded, self.decoding = encode(unencoded_tokens, self.encoding)
        return encoded

    def decode(self, contents: Iterable[int]) -> bytes:
        return generic_decode(contents, self.decoding, b" ")


class TokenEncoder:
    separator = b""

    encoding: dict[bytes, int]
    decoding: Sequence[bytes]

    def __init__(self):
        self.encoding = {}

    def encode(self, string: bytes) -> Sequence[int]:
        unencoded_tokens = [token[0] for token in TOKENS.finditer(string)]

        encoded, self.decoding = encode(unencoded_tokens, self.encoding)
        return encoded

    def decode(self, contents: Iterable[int]) -> bytes:
        return generic_decode(contents, self.decoding, b"")
