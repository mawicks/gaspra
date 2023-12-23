from dataclasses import replace
from os.path import commonprefix

from gaspra.changesets import (
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

    fragments0 = list(reversed(list(changeset0._fragments(parent))))
    fragments1 = list(reversed(list(changeset1._fragments(parent))))

    while fragments0 and fragments1:
        fragment0 = fragments0.pop()
        fragment1 = fragments1.pop()

        if isinstance(fragment0, CopyFragment) and isinstance(fragment1, CopyFragment):
            output, fragment0_tail, fragment1_tail = copy_copy(fragment0, fragment1)

        elif isinstance(fragment0, ChangeFragment) and isinstance(
            fragment1, ChangeFragment
        ):
            output, fragment0_tail, fragment1_tail = change_change(fragment0, fragment1)

        elif isinstance(fragment0, CopyFragment) and isinstance(
            fragment1, ChangeFragment
        ):
            output, fragment0_tail, fragment1_tail = copy_change(fragment0, fragment1)

        elif isinstance(fragment0, ChangeFragment) and isinstance(
            fragment1, CopyFragment
        ):
            output, fragment1_tail, fragment0_tail = copy_change(fragment1, fragment0)

        else:
            raise RuntimeError(
                f"Unexpected types: {type(fragment0)} or {type(fragment1)}"
            )

        if fragment0_tail:
            fragments0.append(fragment0_tail)

        if fragment1_tail:
            fragments1.append(fragment1_tail)

        if output:
            yield output

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


def copy_copy(fragment0: CopyFragment, fragment1: CopyFragment):
    if fragment0.length < fragment1.length:
        shorter, longer = fragment0, fragment1
    else:
        shorter, longer = fragment1, fragment0

    long_queue_tail = None
    if shorter.length != longer.length:
        *_, long_queue_tail = split_copy_fragment(longer, shorter.length)

    tail0 = tail1 = None

    if fragment0 == longer:
        tail0 = long_queue_tail
    else:
        tail1 = long_queue_tail

    return shorter, tail0, tail1


def copy_change(copy_fragment, change_fragment):
    output = copy_tail = change_tail = None

    smaller_length = min(copy_fragment.length, change_fragment.length)
    if change_fragment.length == smaller_length:
        output = change_fragment

        # Anything left over?
        if copy_fragment.length > smaller_length:
            *_, copy_tail = split_copy_fragment(copy_fragment, smaller_length)

    else:  # Change is longer than copy implies a conflict.
        head0, head1 = split_change_fragment(
            change_fragment, len(change_fragment.insert), smaller_length
        )
        if head0:
            output = ConflictFragment(
                head0.insert, copy_fragment.insert, smaller_length
            )

        if head1:
            change_tail = head1

    return output, copy_tail, change_tail


def change_change(fragment0: ChangeFragment, fragment1: ChangeFragment):
    """Handle two change blocks appearing at the same location"""
    output = tail0 = tail1 = None

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
        tail1 = change

    elif fragment0.insert == "" and fragment1.length == 0:
        change = ChangeFragment(fragment1.insert, fragment0.delete, fragment0.length)
        tail0 = change

    # Exactly the same changeset can be reesolved without conflict.  Just pass
    # it along.
    elif (len(fragment0.insert) == len(fragment1.insert) == insert_length) and (
        fragment0.length == fragment1.length == delete_length
    ):
        output = fragment0

    elif (
        # Handle the case where the two changesets have a non-empty
        # common prefix. If it isn't non-empty, there's nothing to do.
        # To split/factor the fragment, the part of the insertion that's
        # factored must be a proper substring of both insertions.
        # Otherwise, the conflict can't be detected in the tail.
        # This elif used to be more restrictive:
        #    just insert_length > 0 and delete_length > 0:
        (insert_length > 0 or delete_length > 0)
        and insert_length < len(fragment0.insert)
        and insert_length < len(fragment1.insert)
    ):
        output, tail0 = split_change_fragment(fragment0, insert_length, delete_length)
        *_, tail1 = split_change_fragment(fragment1, insert_length, delete_length)
    else:
        length = min(fragment0.length, fragment1.length)
        head0, tail0 = split_change_fragment(fragment0, len(fragment0.insert), length)
        head1, tail1 = split_change_fragment(fragment1, len(fragment1.insert), length)

        if head0 and head1:
            output = ConflictFragment(head0.insert, head1.insert, length)

    return output, tail0, tail1


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
