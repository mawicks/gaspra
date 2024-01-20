from collections.abc import Hashable, Iterable, Sequence

from gaspra.types import Change


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

    def conditional_add(self, input_fragment: str):
        if not self.finishable:
            if input_fragment:
                self.partial_line_into.append(input_fragment)
                self.partial_line_from.append(input_fragment)
            input_fragment = ""
        return input_fragment

    def add(self, input_fragment: str):
        self.partial_line_into.append(input_fragment)
        self.partial_line_from.append(input_fragment)

    def is_nonempty(self):
        return bool(self.partial_line_into and self.partial_line_from)

    def finish_conflict(self, input_fragment):
        input_fragment = self.conditional_add(input_fragment)

        yield Change(
            tuple(self.partial_line_into),
            tuple(self.partial_line_from),
        )

        self.partial_line_into.clear()
        self.partial_line_from.clear()

        self.in_conflict = False

        if input_fragment:
            yield input_fragment

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


def to_line_diff(
    fragment_sequence: Iterable[Sequence[Hashable]],
):
    accumulator = DiffAccumulator()
    empty = True
    for fragment in fragment_sequence:
        if not fragment:
            continue

        empty = False
        if isinstance(fragment, Change):
            accumulator.add_conflict(fragment)
        elif isinstance(fragment, str):
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

    yield from accumulator.flush()

    if empty:
        yield ""


def join_with_newline(lines):
    if len(lines) > 0:
        return "\n".join(line for line in lines) + "\n"
    else:
        return ""
