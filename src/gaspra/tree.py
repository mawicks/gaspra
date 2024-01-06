from collections.abc import Hashable, Sequence
from typing import Protocol


class Tree(Protocol):
    def __contains__(self, tag: Hashable):
        raise NotImplementedError

    def base_version(self, tag) -> Hashable:
        raise NotImplementedError

    def add(self, tag: Hashable, existing_head: Hashable | None = None):
        raise NotImplementedError

    def path_to(self, tag: Hashable) -> Sequence[Hashable] | None:
        raise NotImplementedError

    def change_parent(self, tag, new_parent):
        raise NotImplementedError

    def get_split(self, tag: Hashable):
        raise NotImplementedError
