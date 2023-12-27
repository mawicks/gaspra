from collections.abc import Iterable, Sequence
from collections import namedtuple

TokenSequence = Sequence[int]
Change = namedtuple("Change", ["a", "b"])

ChangeSequence = Iterable[str | TokenSequence | Change]
StringIterable = Iterable[str]
TokenIterable = Iterable[TokenSequence]
