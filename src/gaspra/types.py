from collections.abc import Hashable, Iterable, Sequence
from collections import namedtuple

TokenSequence = Sequence[Hashable]
Change = namedtuple("Change", ["a", "b"])

Separator = namedtuple("Separator", "index")

ChangeIterable = Iterable[str | TokenSequence | Change]
StringIterable = Iterable[str]
TokenSequenceIterable = Iterable[TokenSequence]
