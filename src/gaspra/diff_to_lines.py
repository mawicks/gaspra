from collections.abc import Hashable, Iterable, Sequence
import io

from gaspra.types import Change


class DiffAccumulator:
    partial_line_into: list[str | Change]
    partial_line_from: list[str | Change]
    finishable: bool

    def __init__(self):
        self.partial_line_into = []
        self.partial_line_from = []
        self.finishable = True

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

    def conditional_add(self, input_fragment: str):
        if (self.partial_line_into and self.partial_line_into[-1] != "\n") or (
            self.partial_line_from and self.partial_line_from[-1] != "\n"
        ):
            if input_fragment:
                self.partial_line_into.append(input_fragment)
                self.partial_line_from.append(input_fragment)
            input_fragment = ""
        return input_fragment

    def add(self, input_fragment: str):
        self.partial_line_into.append(input_fragment)
        self.partial_line_from.append(input_fragment)

    def nonempty(self):
        return bool(self.partial_line_into and self.partial_line_from)

    def finish_conflict(self, input_fragment):
        input_fragment = self.conditional_add(input_fragment)

        yield Change(
            tuple(self.partial_line_into),
            tuple(self.partial_line_from),
        )

        self.partial_line_into.clear()
        self.partial_line_from.clear()

        if input_fragment:
            yield input_fragment

    def flush(self):
        if self.partial_line_from and self.partial_line_from[0]:
            # If not in a conflict, partial_line_into should be
            # exactly the same as partial_line_from.
            self.partial_line_from.append("\n")
            yield "".join(self.accumulator.partial_line_from)  # type: ignore


def to_line_diff(
    fragment_sequence: Iterable[Sequence[Hashable]],
):
    in_conflict = False
    no_output = True
    accumulator = DiffAccumulator()
    for fragment in fragment_sequence:
        if isinstance(fragment, Change):
            in_conflict = True
            accumulator.add_conflict(fragment)
        elif isinstance(fragment, str):
            if accumulator.finishable and accumulator.nonempty():
                yield from accumulator.finish_conflict("")
                in_conflict = False
                no_output = False

            lines = fragment.split("\n")
            if len(lines) > 1:  # Have a newline
                if in_conflict:
                    yield from accumulator.finish_conflict(lines[0] + "\n")
                    if _ := join_with_newline(lines[1:-1]):
                        yield _
                    no_output = False
                else:
                    if _ := join_with_newline(lines[:-1]):
                        yield _
                        no_output = False
                in_conflict = False
                if lines[-1]:
                    accumulator.add(lines[-1])
            elif lines[0]:
                accumulator.add(lines[0])

    if in_conflict:
        if accumulator.finishable:
            tail = ""
        else:
            tail = "\n"
        yield from accumulator.finish_conflict(tail)

    elif accumulator.partial_line_from and accumulator.partial_line_from[0]:
        # If not in a conflict, partial_line_into should be
        # exactly the same as partial_line_from.
        accumulator.partial_line_from.append("\n")
        yield "".join(accumulator.partial_line_from)  # type: ignore
    elif no_output:
        yield ""


def join_with_newline(lines):
    if len(lines) > 0:
        return "\n".join(line for line in lines) + "\n"
    else:
        return ""
