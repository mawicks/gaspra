from collections.abc import Iterable
from itertools import chain
from typing import Callable
import os

from gaspra.types import StringIterable, TokenSequenceIterable, TokenSequence

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data"),
)


def string_joiner(g: StringIterable) -> str:
    return "".join(g)


def tuple_joiner(g: TokenSequenceIterable) -> TokenSequence:
    return tuple(chain(*g))


StringJoiner = Callable[[Iterable[str]], str]
TokenJoiner = Callable[[TokenSequenceIterable], TokenSequence]


def get_joiner(empty) -> StringJoiner | TokenJoiner:
    if isinstance(empty, str):
        joiner = string_joiner
    else:
        joiner = tuple_joiner
    return joiner


def common_prefix_length(a: str | TokenSequence, b: str | TokenSequence):
    length = min(len(a), len(b))

    for length, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return length

    return length


if __name__ == "__main__":
    print(DATA_DIR)
