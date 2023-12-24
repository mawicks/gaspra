from dataclasses import replace
from os.path import commonprefix

from gaspra.changesets import (
    ChangeFragment,
    ConflictFragment,
    CopyFragment,
    diff,
    find_changeset,
)

OutputType = CopyFragment | ChangeFragment | ConflictFragment
InputType = CopyFragment | ChangeFragment


def merge(parent: str, branch0: str, branch1: str):
    changeset0 = find_changeset(parent, branch0)
    changeset1 = find_changeset(parent, branch1)

    fragments0 = list(reversed(list(changeset0._fragments(parent))))
    fragments1 = list(reversed(list(changeset1._fragments(parent))))

    merged = _merge(fragments0, fragments1)

    return accumulate_result(merged)


def accumulate_result(output):
    conflict_free_accumulation = ""
    conflict_accumulation = ("", "")
    nothing_has_been_output = True
    for fragment in output:
        if isinstance(fragment, ConflictFragment):
            # Flush the conflict free string we've been accumulating.
            if conflict_free_accumulation:
                yield conflict_free_accumulation
                nothing_has_been_output = False
                conflict_free_accumulation = ""

            c1, c2 = conflict_accumulation
            conflict_accumulation = (c1 + fragment.version1, c2 + fragment.version2)
        else:
            if any(conflict_accumulation):
                diff_sequence = diff(*reversed(conflict_accumulation))
                yield from diff_sequence
                nothing_has_been_output = False
                conflict_accumulation = ("", "")

            conflict_free_accumulation += fragment.insert

    # Flush the conflict free string we've been accumulating and
    # return empty string if no output yet.
    if any(conflict_accumulation):
        yield conflict_accumulation
        nothing_has_been_output = False

    if conflict_free_accumulation:
        yield conflict_free_accumulation
        nothing_has_been_output = False

    if nothing_has_been_output:
        yield ""


def _merge(fragments0: list[InputType], fragments1):
    """Process changes in fragments0 and fragments1 until
    they are empty.  Note, this function modifies the passed lists"""

    within_conflict = False

    while fragments0 and fragments1:
        fragment0 = fragments0.pop()
        fragment1 = fragments1.pop()

        output, tail0, tail1, within_conflict = process_fragments(
            fragment0,
            fragment1,
            within_conflict,
        )

        if output:
            yield output

        # If the fragments weren't fully processed, push their tails
        # back onto their respective stacks.

        if tail0:
            fragments0.append(tail0)

        if tail1:
            fragments1.append(tail1)

    # We've exhausted one of the input queues.  Flush the
    # other one if there's anything left.
    if fragments0 or fragments1:
        yield from flush_remaining(fragments0, fragments1, within_conflict)


def flush_remaining(fragments0, fragments1, within_conflict):
    remaining = fragments0 or fragments1
    for item in reversed(remaining):
        if within_conflict and remaining == fragments0:
            yield ConflictFragment(item.insert, "", 0)
        elif within_conflict:
            yield ConflictFragment("", item.insert, 0)
        else:
            yield item


def process_fragments(fragment0, fragment1, within_conflict: bool):
    if isinstance(fragment0, CopyFragment) and isinstance(fragment1, CopyFragment):
        output, tail0, tail1 = copy_copy(fragment0, fragment1)
        within_conflict = False

    elif within_conflict:
        output, tail0, tail1 = pending_conflict(fragment0, fragment1)

    elif isinstance(fragment0, ChangeFragment) and isinstance(
        fragment1, ChangeFragment
    ):
        output, tail0, tail1, within_conflict = change_change(fragment0, fragment1)

    elif isinstance(fragment0, CopyFragment) and isinstance(fragment1, ChangeFragment):
        output, tail0, tail1 = copy_change(fragment0, fragment1)

    elif isinstance(fragment0, ChangeFragment) and isinstance(fragment1, CopyFragment):
        output, tail1, tail0 = copy_change(fragment1, fragment0)

    else:
        raise RuntimeError(f"Unexpected types: {type(fragment0)} or {type(fragment1)}")

    return output, tail0, tail1, within_conflict


def pending_conflict(fragment0: InputType, fragment1: InputType):
    min_length = min(fragment0.length, fragment1.length)

    head0, tail0 = split_fragment(fragment0, min_length)
    head1, tail1 = split_fragment(fragment1, min_length)

    from0 = head0.insert if head0 else ""
    from1 = head1.insert if head1 else ""

    output = ConflictFragment(from0, from1, min_length)
    return output, tail0, tail1


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

    if has_composable_changes(fragment0, fragment1):
        return (*compose_changes(fragment0, fragment1), False)

    # Determine how much is common between the two changesets
    insert_length, delete_length = common_prefix_lengths(fragment0, fragment1)

    # Exactly the same changeset can simply be passed along.
    if are_identical_changes(fragment0, fragment1, insert_length, delete_length):
        return fragment0, None, None, False

    if insert_length > 0 or delete_length > 0:
        return (
            *factor_common_prefix(fragment0, fragment1, insert_length, delete_length),
            True,
        )

    return (*ordinary_conflict(fragment0, fragment1), True)


def has_composable_changes(fragment0, fragment1):
    # This is an edge case that showed up in testing. If one change is a
    # pure insertion (no deletion) and the other is a pure deletion (no
    # insertion), they can be combined into a single conflict-free
    # change.  It needs to be pushed back onto the input list to be
    # processed properly One input sequence was [insert x/delete
    # nothing][s] The other input sequence was [insert nothing/delete
    # s]. These are transformed to the sequences 1) [s] and 2) [insert
    # x/delete s] by pushing [insert x/delete s] back onto the input
    # queue which has the affect of inserting 's' at position where 's'
    # was.  See compose_changes() for how the changes are composed.

    return (fragment0.length == 0 and fragment1.insert == "") or (
        fragment0.insert == "" and fragment1.length == 0
    )


def compose_changes(fragment0, fragment1):
    if fragment0.length == 0 and fragment1.insert == "":
        tail1 = ChangeFragment(
            fragment0.insert,
            fragment1.delete,
            fragment1.length,
        )
        return None, None, tail1
    elif fragment0.insert == "" and fragment1.length == 0:
        tail0 = ChangeFragment(
            fragment1.insert,
            fragment0.delete,
            fragment0.length,
        )
        return None, tail0, None
    else:
        raise ValueError("Changes are not composable")


def are_identical_changes(
    fragment0,
    fragment1,
    insert_length,
    delete_length,
):
    return (len(fragment0.insert) == len(fragment1.insert) == insert_length) and (
        fragment0.length == fragment1.length == delete_length
    )


def has_factorable_common_prefix(
    fragment0,
    fragment1,
    insert_length,
    delete_length,
):
    """Check for the case where the two changesets have a non-empty
    common prefix. If it isn't non-empty, there's nothing to do.  To
    split/factor the fragment, the part of the insertion that's factored
    must be a proper substring of both insertions.  Otherwise, the
    conflict can't be detected in the tail.  This elif used to be more
    restrictive: just insert_length > 0 and delete_length > 0:
    """
    return insert_length > 0 or delete_length > 0


def factor_common_prefix(
    fragment0: ChangeFragment,
    fragment1: ChangeFragment,
    insert_length,
    delete_length,
):
    output, tail0 = split_change_fragment(
        fragment0,
        insert_length,
        delete_length,
    )
    *_, tail1 = split_change_fragment(
        fragment1,
        insert_length,
        delete_length,
    )
    return output, tail0, tail1


def ordinary_conflict(fragment0, fragment1):
    output = None

    length = min(fragment0.length, fragment1.length)
    head0, tail0 = split_change_fragment(
        fragment0,
        len(fragment0.insert),
        length,
    )
    head1, tail1 = split_change_fragment(
        fragment1,
        len(fragment1.insert),
        length,
    )

    if head0 and head1:
        output = ConflictFragment(head0.insert, head1.insert, length)

    return output, tail0, tail1


def split_fragment(fragment: InputType, length: int):
    if isinstance(fragment, CopyFragment):
        return split_copy_fragment(fragment, length)
    if isinstance(fragment, ChangeFragment):
        return split_change_fragment(fragment, len(fragment.insert), length)


def split_copy_fragment(fragment: CopyFragment, length: int):
    head = tail = None
    if length > 0:
        head = replace(
            fragment,
            insert=fragment.insert[:length],
            length=length,
        )
    if length < fragment.length:
        tail = replace(
            fragment,
            insert=fragment.insert[length:],
            length=fragment.length - length,
        )
    return head, tail


def split_change_fragment(
    fragment: ChangeFragment,
    insert_length,
    length: int,
):
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


def common_prefix_lengths(
    change1: ChangeFragment,
    change2: ChangeFragment,
):
    insert_length = len(commonprefix((change1.insert, change2.insert)))
    delete_length = len(commonprefix((change1.delete, change2.delete)))

    return insert_length, delete_length
