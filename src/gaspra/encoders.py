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


def generic_decoder(
    contents: Iterable[int], decoding: Sequence[bytes], separator: bytes
):
    return separator.join(decoding[t] for t in contents)


def encode(unencoded_tokens: Iterable[bytes], encoding: dict[bytes, int]):
    for token in unencoded_tokens:
        if token not in encoding:
            encoding[token] = len(encoding)
    return tuple(encoding[token] for token in unencoded_tokens)


class Tokenizer(Protocol):
    def encoder(self, contents: bytes, encoding: dict[bytes, int]):
        raise NotImplemented

    def decoder(self, contents: Iterable[int], decoding: Sequence[bytes]):
        raise NotImplemented


def line_encoder(contents: bytes, encoding: dict[bytes, int]):
    lines = contents.split(b"\n")

    return encode(lines, encoding)


def line_decoder(contents: Iterable[int], decoding: Sequence[bytes]):
    return generic_decoder(contents, decoding, b"\n")


def space_encoder(string: bytes, encoding: dict[bytes, int]):
    unencoded_tokens = string.split(b" ")

    return encode(unencoded_tokens, encoding)


def space_decoder(contents: Iterable[int], decoding: Sequence[bytes]):
    return generic_decoder(contents, decoding, b" ")


def token_encoder(string: bytes, encoding: dict[bytes, int]):
    unencoded_tokens = [token[0] for token in TOKENS.finditer(string)]

    return encode(unencoded_tokens, encoding)


def token_decoder(contents: Iterable[int], decoding: Sequence[bytes]):
    return generic_decoder(contents, decoding, b"")
