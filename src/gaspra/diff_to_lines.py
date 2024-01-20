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

    def add(self, input_fragment: str):
        if (self.partial_line_into and self.partial_line_into[-1] != "\n") or (
            self.partial_line_from and self.partial_line_from[-1] != "\n"
        ):
            if input_fragment:
                self.partial_line_into.append(input_fragment)
                self.partial_line_from.append(input_fragment)
            input_fragment = ""
        return input_fragment

    def finish_conflict(self, input_fragment):
        input_fragment = self.add(input_fragment)

        yield Change(
            tuple(self.partial_line_into),
            tuple(self.partial_line_from),
        )

        self.partial_line_into.clear()
        self.partial_line_from.clear()

        if input_fragment:
            yield input_fragment


def split_and_add_conflict(
    partial_line_into: list[str | Change],
    partial_line_from: list[str | Change],
    fragment: Change,
    finishable: bool,
) -> bool:
    partial_line_into.append(Change(fragment.a, ""))
    partial_line_from.append(Change("", fragment.b))

    if fragment.a:
        a_finishable = fragment.a[-1:] == "\n"
    else:
        a_finishable = finishable

    if fragment.b:
        b_finishable = fragment.b[-1:] == "\n"
    else:
        b_finishable = finishable

    return a_finishable and b_finishable


def update_partials(partial_line_into, partial_line_from, input_fragment):
    if (partial_line_into and partial_line_into[-1] != "\n") or (
        partial_line_from and partial_line_from[-1] != "\n"
    ):
        if input_fragment:
            partial_line_into.append(input_fragment)
            partial_line_from.append(input_fragment)
        input_fragment = ""
    return input_fragment


def finish_conflict(partial_line_into, partial_line_from, input_fragment):
    input_fragment = update_partials(
        partial_line_into, partial_line_from, input_fragment
    )

    yield Change(
        tuple(partial_line_into),
        tuple(partial_line_from),
    )

    partial_line_into.clear()
    partial_line_from.clear()

    if input_fragment:
        yield input_fragment


def to_line_diff(
    fragment_sequence: Iterable[Sequence[Hashable]],
):
    in_conflict = False
    no_output = True
    partial_line_into: list[str | Change] = []
    partial_line_from: list[str | Change] = []
    conflict_is_finishable = True
    for fragment in fragment_sequence:
        if isinstance(fragment, Change):
            in_conflict = True
            conflict_is_finishable = split_and_add_conflict(
                partial_line_into,
                partial_line_from,
                fragment,
                conflict_is_finishable,
            )
        elif isinstance(fragment, str):
            if conflict_is_finishable and (partial_line_from or partial_line_into):
                yield from finish_conflict(
                    partial_line_into,
                    partial_line_from,
                    "",
                )
                in_conflict = False
                conflict_is_finishable = True
                no_output = False

            lines = fragment.split("\n")
            if len(lines) > 1:  # Have a newline
                if in_conflict:
                    yield from finish_conflict(
                        partial_line_into,
                        partial_line_from,
                        lines[0] + "\n",
                    )
                    conflict_is_finishable = True
                    if _ := join_with_newline(lines[1:-1]):
                        yield _
                    no_output = False
                else:
                    if _ := join_with_newline(lines[:-1]):
                        yield _
                        no_output = False
                in_conflict = False
                if lines[-1]:
                    partial_line_into.append(lines[-1])
                    partial_line_from.append(lines[-1])
            elif lines[0]:
                partial_line_into.append(lines[0])
                partial_line_from.append(lines[0])

    if in_conflict:
        if (
            isinstance(partial_line_into[-1], Change)
            and partial_line_into[-1].a[-1:] != "\n"
        ) or (
            isinstance(partial_line_from[-1], Change)
            and partial_line_from[-1].b[-1:] != "\n"
        ):
            tail = "\n"
        else:
            tail = ""
        yield from finish_conflict(partial_line_into, partial_line_from, tail)
    elif partial_line_from and partial_line_from[0]:
        # If not in a conflict, partial_line_into should be
        # exactly the same as partial_line_from.
        partial_line_from.append("\n")
        yield "".join(partial_line_from)  # type: ignore
    elif no_output:
        yield ""


def join_with_newline(lines):
    if len(lines) > 0:
        return "\n".join(line for line in lines) + "\n"
    else:
        return ""
