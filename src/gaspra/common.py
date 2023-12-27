from collections.abc import Iterable
from itertools import chain
import os

from gaspra.types import StringIterable, TokenIterable

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data"),
)


def string_joiner(g: StringIterable) -> str:
    return "".join(g)


def tuple_joiner(g: Iterable[TokenIterable]) -> TokenIterable:
    return tuple(chain(*g))


def get_joiner(empty):
    if isinstance(empty, str):
        joiner = string_joiner
    else:
        joiner = tuple_joiner
    return joiner


if __name__ == "__main__":
    print(DATA_DIR)
