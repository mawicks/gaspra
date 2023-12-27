from collections.abc import Iterable
from collections import namedtuple

StringSequence = Iterable[str]
TokenSequence = Iterable[int]

Change = namedtuple("Change", ["a", "b"])
