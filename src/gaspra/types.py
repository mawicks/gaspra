from collections.abc import Iterable
from collections import namedtuple

StringSequence = Iterable[str]
TokenSequence = Iterable[int]

Difference = namedtuple("Difference", ["a", "b"])
