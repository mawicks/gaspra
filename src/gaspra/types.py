from collections.abc import Hashable, Iterable, Sequence
from collections import namedtuple
from typing import TypeVar

Token = Hashable
TokenVar = TypeVar("TokenVar", bound=Hashable)
Tag = TypeVar("Tag", bound=Hashable)
TokenSequence = Sequence[Token]
TokenIterable = Iterable[Token]
TokenSequenceVar = TypeVar("TokenSequenceVar", str, bytes, Sequence[int])

StringIterable = Iterable[str]
BytesIterable = Iterable[bytes]
TokenSequenceIterable = Iterable[TokenSequence]

Separator = namedtuple("Separator", "index")
Change = namedtuple("Change", ["a", "b"])
Common = namedtuple("Common", ["a_slice", "b_slice"])
DiffIterable = Iterable[TokenSequence | Change]
ReducedChangeIterable = Iterable[Common | Change]
StrippedChangeIterable = Iterable[slice | TokenSequence]
StrippedChangeSequence = Sequence[slice | TokenSequence]
