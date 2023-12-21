from dataclasses import replace
from os.path import commonprefix

from string_matching.changesets import (
    find_changeset,
    CopyFragment,
    ChangeFragment,
    ConflictFragment,
)

OutputType = CopyFragment | ChangeFragment | ConflictFragment
InputType = CopyFragment | ChangeFragment


def _merge(parent: str, branch0: str, branch1: str):
    changeset0 = find_changeset(parent, branch0)
    changeset1 = find_changeset(parent, branch1)

    fragments0 = list(reversed(list(changeset0.fragments(parent))))
    fragments1 = list(reversed(list(changeset1.fragments(parent))))

    while fragments0 and fragments1:
        fragment0 = fragments0.pop()
        fragment1 = fragments1.pop()

        if isinstance(fragment0, CopyFragment) and isinstance(fragment1, CopyFragment):
            yield from copy_copy(fragment0, fragment1, fragments0, fragments1)

        elif isinstance(fragment0, ChangeFragment) and isinstance(
            fragment1, ChangeFragment
        ):
            yield from change_change(fragment0, fragment1, fragments0, fragments1)

        elif isinstance(fragment0, CopyFragment) and isinstance(
            fragment1, ChangeFragment
        ):
            yield from copy_change(fragment0, fragment1, fragments0, fragments1)

        elif isinstance(fragment0, ChangeFragment) and isinstance(
            fragment1, CopyFragment
        ):
            yield from copy_change(fragment1, fragment0, fragments1, fragments0)

        else:
            raise RuntimeError(
                f"Unexpected types: {type(fragment0)} or {type(fragment1)}"
            )

        continue

    if fragments0 or fragments1:
        remaining = fragments0 or fragments1
        yield from reversed(remaining)


def merge(parent: str, branch0: str, branch1: str):
    return accumulate_result(_merge(parent, branch0, branch1))


def accumulate_result(output):
    conflict_free = ""
    no_output_yet = True
    for fragment in output:
        if isinstance(fragment, ConflictFragment):
            if conflict_free:
                yield conflict_free
                conflict_free = ""

            yield (fragment.version1, fragment.version2)
            no_output_yet = False
        else:
            conflict_free += fragment.insert

    if conflict_free or no_output_yet:
        yield conflict_free


def copy_copy(
    fragment0: CopyFragment,
    fragment1: CopyFragment,
    fragment0_queue,
    fragment1_queue,
):
    if fragment0.length < fragment1.length:
        shorter, longer = fragment0, fragment1
        long_queue = fragment1_queue
    else:
        shorter, longer = fragment1, fragment0
        long_queue = fragment0_queue

    if shorter.length != longer.length:
        __ignored__, tail = split_copy_fragment(longer, shorter.length)
        long_queue.append(tail)

    yield shorter
    return


def copy_change(
    copy_fragment, change_fragment, copy_fragment_queue, change_fragment_queue
):
    smaller_length = min(copy_fragment.length, change_fragment.length)
    if change_fragment.length == smaller_length:
        # Anything left over?
        if copy_fragment.length > smaller_length:
            __ignored__, copy_tail = split_copy_fragment(copy_fragment, smaller_length)
            copy_fragment_queue.append(copy_tail)
        yield change_fragment

    else:  # Change is longer than copy implies a conflict.
        head0, head1 = split_change_fragment(
            change_fragment, len(change_fragment.insert), smaller_length
        )
        if head1:
            change_fragment_queue.append(head1)

        if head0:
            yield ConflictFragment(head0.insert, copy_fragment.insert, smaller_length)


def change_change(
    fragment0: ChangeFragment,
    fragment1: ChangeFragment,
    fragments0: list[InputType],
    fragments1: list[InputType],
):
    """Handle two change blocks appearing at the same location"""

    insert_length, delete_length = common_head_of_change(fragment0, fragment1)

    # This is an edge case that showed up in testing.
    # If one change is a pure insertion (no deletion) and the other
    # is a pure deletion (no insertion), they can be combined into a single
    # conflict-free change.  It needs to be pushed back onto
    # the input list to be processed properly
    # One input sequence was [insert x/delete nothing][s]
    # The other input sequence was [insert nothing/delete s]
    # These are transformed to the sequences
    # 1) [s] and 2) [insert x/delete s]
    # by pushing [insert x/delete s] back onto the input queue
    # which has the affect of inserting 's' at position
    # where 's' was.

    if fragment0.length == 0 and fragment1.insert == "":
        change = ChangeFragment(fragment0.insert, fragment1.delete, fragment1.length)
        fragments1.append(change)

    elif fragment0.insert == "" and fragment1.length == 0:
        change = ChangeFragment(fragment1.insert, fragment0.delete, fragment0.length)
        fragments0.append(change)

    # Exactly the same changeset can be reesolved without conflict.  Just pass
    # it along.
    elif (len(fragment0.insert) == len(fragment1.insert) == insert_length) and (
        fragment0.length == fragment1.length == delete_length
    ):
        yield fragment0

    # Handle the case where the two changesets have non-empty common prefix.
    elif insert_length > 0 and delete_length > 0:
        head0, tail0 = split_change_fragment(fragment0, insert_length, delete_length)
        if tail0:
            fragments0.append(tail0)
        __x__, tail1 = split_change_fragment(fragment1, insert_length, delete_length)
        if tail1:
            fragments1.append(tail1)

        if head0:
            yield head0

    else:
        length = min(fragment0.length, fragment1.length)
        head0, tail0 = split_change_fragment(fragment0, len(fragment0.insert), length)
        head1, tail1 = split_change_fragment(fragment1, len(fragment1.insert), length)
        if tail0:
            fragments0.append(tail0)
        if tail1:
            fragments1.append(tail1)

        if head0 and head1:
            yield ConflictFragment(head0.insert, head1.insert, length)


def split_copy_fragment(fragment: CopyFragment, length: int):
    head = tail = None
    if length > 0:
        head = replace(fragment, insert=fragment.insert[:length], length=length)
    if length < fragment.length:
        tail = replace(
            fragment, insert=fragment.insert[length:], length=fragment.length - length
        )
    return head, tail


def split_change_fragment(fragment: ChangeFragment, insert_length, length: int):
    head = tail = None
    if length > 0 or insert_length > 0:
        head = replace(
            fragment,
            insert=fragment.insert[:insert_length],
            delete=fragment.delete[:length],
            length=length,
        )
    if length < fragment.length or insert_length < len(fragment.insert):
        tail = replace(
            fragment,
            insert=fragment.insert[insert_length:],
            delete=fragment.delete[length:],
            length=fragment.length - length,
        )
    return head, tail


def common_head_of_change(change1: ChangeFragment, change2: ChangeFragment):
    insert_length = len(commonprefix((change1.insert, change2.insert)))
    delete_length = len(commonprefix((change1.delete, change2.delete)))

    return insert_length, delete_length
