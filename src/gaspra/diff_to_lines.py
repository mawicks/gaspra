from collections.abc import Hashable, Iterable, Sequence

from gaspra.types import Change, DiffIterable


class DiffAccumulator:
    partial_line_into: list[str | Change]
    partial_line_from: list[str | Change]
    finishable: bool
    in_conflict: bool

    def __init__(self):
        self.partial_line_into = []
        self.partial_line_from = []
        self.finishable = True
        self.in_conflict = False

    def clear(self):
        self.partial_line_into.clear()
        self.partial_line_from.clear()
        self.finishable = True

    def add_conflict(self, conflict: Change):
        self.partial_line_into.append(Change(conflict.a, ""))
        self.partial_line_from.append(Change("", conflict.b))

        if conflict.a:
            a_finishable = conflict.a[-1:] == "\n"
        else:
            a_finishable = self.finishable

        if conflict.b:
            b_finishable = conflict.b[-1:] == "\n"
        else:
            b_finishable = self.finishable

        self.finishable = a_finishable and b_finishable
        self.in_conflict = True

    def conditional_add(self, fragment: str):
        if not self.finishable:
            if fragment:
                self.add(fragment)

            fragment = ""
        return fragment

    def add(self, fragment: str):
        self.partial_line_into.append(fragment)
        self.partial_line_from.append(fragment)

        self.finishable = (fragment[-1:] == "\n") if fragment else self.finishable

    def is_nonempty(self):
        return bool(self.partial_line_into and self.partial_line_from)

    def finish_conflict(self, fragment):
        fragment = self.conditional_add(fragment)

        yield Change(
            tuple(self.partial_line_into),
            tuple(self.partial_line_from),
        )

        self.partial_line_into.clear()
        self.partial_line_from.clear()

        self.in_conflict = False

        if fragment:
            yield fragment

    def flush(self):
        if self.in_conflict:
            tail = "" if self.finishable else "\n"
            yield from self.finish_conflict(tail)

        elif self.partial_line_from and self.partial_line_from[0]:
            # If not in a conflict, partial_line_into should be exactly
            # the same as partial_line_from so we disregard
            # partial_line_into
            self.partial_line_from.append("\n")
            yield "".join(self.partial_line_from)  # type: ignore


def to_line_diff(fragment_sequence: DiffIterable):
    accumulator = DiffAccumulator()
    empty = True
    for fragment in fragment_sequence:
        if not fragment:
            continue

        empty = False

        yield from handle_fragment(fragment, accumulator)

    yield from accumulator.flush()

    if empty:
        yield ""


def handle_fragment(fragment, accumulator):
    if isinstance(fragment, Change):
        accumulator.add_conflict(fragment)

    elif isinstance(fragment, str):
        # Don't finish an accumulating conflict on spaces/newlines.
        if accumulator.in_conflict and fragment.isspace():
            accumulator.add(fragment)
            return

        if accumulator.finishable and accumulator.is_nonempty():
            yield from accumulator.finish_conflict("")

        lines = fragment.split("\n")
        if len(lines) > 1:  # Have a newline
            if accumulator.in_conflict:
                yield from accumulator.finish_conflict(lines[0] + "\n")
                if joined := join_with_newline(lines[1:-1]):
                    yield joined
            else:
                if joined := join_with_newline(lines[:-1]):
                    yield joined

            if lines[-1]:
                accumulator.add(lines[-1])
        else:
            accumulator.add(lines[0])


def join_with_newline(lines):
    if len(lines) > 0:
        return "\n".join(line for line in lines) + "\n"
    else:
        return ""


# Following routine is very similar to consolidate_*() functions in
# merge.py.  There's an opportunity for some refactoring.


def consolidate(stream: DiffIterable) -> DiffIterable:
    """Loop through change stream of strange and Change objeccts
    and consolidate the change objects.

    It's not important whether strings or level1 chnage objects
    get consolidated, but the level 0 Change objects should be.
    """
    a_fragments = []
    b_fragments = []
    for fragment in stream:
        if isinstance(fragment, Change):
            # At this level, Change components should be
            # sequences so use extend() rather than append()
            a_fragments.extend(fragment.a)
            b_fragments.extend(fragment.b)
        else:
            if a_fragments or b_fragments:
                yield Change(tuple(a_fragments), tuple(b_fragments))
                a_fragments.clear()
                b_fragments.clear()

            yield fragment
    if a_fragments or b_fragments:
        yield Change(tuple(a_fragments), tuple(b_fragments))


def consolidated_line_diff(stream: DiffIterable) -> DiffIterable:
    yield from consolidate(to_line_diff(stream))
