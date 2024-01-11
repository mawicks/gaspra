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
    return tuple(encoding[token] for token in unencoded_tokens)


class Tokenizer(Protocol):
    separator: bytes

    @staticmethod
    def encode(contents: bytes, encoding: dict[bytes, int]):
        raise NotImplemented

    @staticmethod
    def decode(contents: Iterable[int], decoding: Sequence[bytes]) -> bytes:
        raise NotImplemented


class NullTokenizer:
    separator = b""

    @staticmethod
    def encode(contents: bytes, _) -> Sequence[int]:
        return contents

    @staticmethod
    def decode(contents: bytes, _) -> bytes:
        return contents


class LineEncoder:
    separator = "\n"

    @staticmethod
    def encode(contents: bytes, encoding: dict[bytes, int]) -> Sequence[int]:
        lines = contents.split(b"\n")

        return encode(lines, encoding)

    @staticmethod
    def decode(contents: Iterable[int], decoding: Sequence[bytes]) -> bytes:
        return generic_decode(contents, decoding, b"\n")


class SpaceEncoder:
    separator = b" "

    @staticmethod
    def encode(string: bytes, encoding: dict[bytes, int]) -> Sequence[int]:
        unencoded_tokens = string.split(b" ")

        return encode(unencoded_tokens, encoding)

    @staticmethod
    def decode(contents: Iterable[int], decoding: Sequence[bytes]) -> bytes:
        return generic_decode(contents, decoding, b" ")


class TokenEncoder:
    separator = b""

    @staticmethod
    def encode(string: bytes, encoding: dict[bytes, int]) -> Sequence[int]:
        unencoded_tokens = [token[0] for token in TOKENS.finditer(string)]

        return encode(unencoded_tokens, encoding)

    @staticmethod
    def decode(contents: Iterable[int], decoding: Sequence[bytes]) -> bytes:
        return generic_decode(contents, decoding, b"")
