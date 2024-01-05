from collections.abc import Hashable, Iterable, Sequence
from collections import namedtuple
from typing import TypeVar

Token = TypeVar("Token", bound=Hashable)
Tag = TypeVar("Tag", bound=Hashable)
TokenSequence = Sequence[Token]
# TokenSequence = Sequence[Hashable]

StringIterable = Iterable[str]
BytesIterable = Iterable[bytes]
TokenSequenceIterable = Iterable[TokenSequence]

Separator = namedtuple("Separator", "index")
Change = namedtuple("Change", ["a", "b"])
ChangeIterable = Iterable[TokenSequence | Change]
ReducedChangeIterable = Iterable[tuple[slice, slice] | Change]
StrippedChangeIterable = Iterable[slice | TokenSequence]
StrippedChangeSequence = Sequence[slice | TokenSequence]
