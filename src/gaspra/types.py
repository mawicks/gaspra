from collections.abc import Iterable, Sequence
from collections import namedtuple

TokenSequence = Sequence[int]

StringIterable = Iterable[str]
TokenIterable = Iterable[TokenSequence]

Change = namedtuple("Change", ["a", "b"])
