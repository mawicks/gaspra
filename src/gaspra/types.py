from collections.abc import Iterable, Sequence
from collections import namedtuple

TokenSequence = Sequence[int]
Change = namedtuple("Change", ["a", "b"])

Separator = namedtuple("Separator", "index")

ChangeIterable = Iterable[str | TokenSequence | Change]
StringIterable = Iterable[str]
TokenSequenceIterable = Iterable[TokenSequence]
