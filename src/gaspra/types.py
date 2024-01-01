from collections.abc import Hashable, Iterable, Sequence
from collections import namedtuple

TokenSequence = Sequence[Hashable]

StringIterable = Iterable[str]
BytesIterable = Iterable[bytes]
TokenSequenceIterable = Iterable[TokenSequence]

Separator = namedtuple("Separator", "index")
Change = namedtuple("Change", ["a", "b"])
ChangeIterable = Iterable[TokenSequence | Change]
ReducedChangeIterable = Iterable[tuple[slice, slice] | Change]
