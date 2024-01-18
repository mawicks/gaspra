from dataclasses import replace

from gaspra.changesets import (
    ChangeFragment,
    ConflictFragment,
    CopyFragment,
    find_changeset,
)
from gaspra.common import get_joiner, common_prefix_length
from gaspra.types import Change, TokenSequence


OutputType = CopyFragment | ChangeFragment | ConflictFragment
InputType = CopyFragment | ChangeFragment


def merge_token_sequence(
    parent: str | TokenSequence,
    branch0: str | TokenSequence,
    branch1: str | TokenSequence,
):
    """
    This is a fairly low-level function.  For most use cases
    you should use tokenizers.merge()
    """

    empty = parent[0:0]

    changeset0 = find_changeset(parent, branch0)
    changeset1 = find_changeset(parent, branch1)

    fragments0 = list(reversed(list(changeset0._stream(parent))))
    fragments1 = list(reversed(list(changeset1._stream(parent))))

    merged = _merge(fragments0, fragments1)

    return consolidate(merged, empty=empty)


def consolidate(fragments, empty: str | TokenSequence = ""):
    """Consolidate consecutive fragments of similar types
    into a single segment"""

    # Make two passes though the output.  In the first
    # past, conflicts and consolidated (and possibly expanded
    # into copy and conflict fragments
    # In the second pass, consolidate copy and conflict fragments
    # with one another and don't expand the conflict fragments.
    # The second pass is required because some of the copy fragments
    # that get consolidated in the second pass are created from
    # the conflict expansions in the first pass.

    yield from consolidate_all(
        consolidate_conflicts(fragments, empty=empty), empty=empty
    )

    return


def consolidate_conflicts(input_stack, empty: str | TokenSequence = ""):
    join = get_joiner(empty)
    input_stack = list(reversed(list(input_stack)))

    while input_stack:
        # Loop through and consolidate contiguous ConflictFragments
        # First collect a contiguous gruop
        conflict_group = []
        while input_stack and isinstance(input_stack[-1], ConflictFragment):
            conflict_group.append(input_stack.pop())

        # Do a combination of consolidation and re-splitting with find_changeset()
        version1 = join(fragment.version1 for fragment in conflict_group)
        version2 = join(fragment.version2 for fragment in conflict_group)

        for fragment in find_changeset(version2, version1)._stream(version2):
            if isinstance(fragment, CopyFragment):
                yield fragment
            elif isinstance(fragment, ChangeFragment):
                yield ConflictFragment(
                    fragment.insert,
                    fragment.delete,
                )
            else:  # pragma: no cover
                raise ValueError(f"Unexpected fragment type: {type(fragment)}")

        # For now, just copy the other fragment types.  They will be
        # consolidated in the second pass.
        while input_stack and isinstance(
            input_stack[-1], CopyFragment | ChangeFragment
        ):
            yield input_stack.pop()


def consolidate_all(staged, empty: str | TokenSequence = ""):
    join = get_joiner(empty)

    staged = list(reversed(list(staged)))

    something_has_been_output = False
    while staged:
        # Loop through and consolidate contiguous ConflictFragments
        conflict_group = []
        while staged and isinstance(staged[-1], ConflictFragment):
            conflict_group.append(staged.pop())
        version1 = join(fragment.version1 for fragment in conflict_group)
        version2 = join(fragment.version2 for fragment in conflict_group)

        if version1 or version2:
            yield Change(version1, version2)
            something_has_been_output = True

        # Loop through and consolidate the other types
        copy_or_change_group = []
        while staged and isinstance(staged[-1], CopyFragment | ChangeFragment):
            copy_or_change_group.append(staged.pop())
        insert = join(fragment.insert for fragment in copy_or_change_group)
        if insert:
            yield insert
            something_has_been_output = True

    if not something_has_been_output:
        yield empty


def _merge(fragments0: list[InputType], fragments1):
    """This is an extremely low level merge function only meant
    to be called within this module.

    Process changes in fragments0 and fragments1 until
    they are empty.

    Note, this function modifies the passed lists"""

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
            yield ConflictFragment(item.insert, "")
        elif within_conflict:
            yield ConflictFragment("", item.insert)
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

    else:  # pragma: no cover
        raise RuntimeError(f"Unexpected types: {type(fragment0)} or {type(fragment1)}")

    return output, tail0, tail1, within_conflict


def pending_conflict(fragment0: InputType, fragment1: InputType):
    min_length = min(fragment0.length, fragment1.length)

    head0, tail0 = split_fragment(fragment0, min_length)
    head1, tail1 = split_fragment(fragment1, min_length)

    from0 = head0.insert if head0 else ""
    from1 = head1.insert if head1 else ""

    output = ConflictFragment(from0, from1)
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
            output = ConflictFragment(head0.insert, copy_fragment.insert)

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
    # This is an optimization.  The ordinary_conflict() function below
    # should also remove even if this test is omitted.
    if are_identical_changes(fragment0, fragment1, insert_length, delete_length):
        return fragment0, None, None, False

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

    return (fragment0.length == 0 and len(fragment1.insert) == 0) or (
        len(fragment0.insert) == 0 and fragment1.length == 0
    )


def compose_changes(fragment0, fragment1):
    if fragment0.length == 0 and len(fragment1.insert) == 0:
        tail1 = ChangeFragment(
            fragment0.insert,
            fragment1.delete,
            fragment1.length,
        )
        return None, None, tail1
    elif len(fragment0.insert) == 0 and fragment1.length == 0:
        tail0 = ChangeFragment(
            fragment1.insert,
            fragment0.delete,
            fragment0.length,
        )
        return None, tail0, None
    else:  # pragma: no cover
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
        output = ConflictFragment(head0.insert, head1.insert)

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
    # Note: don't use the commonprefix() function from
    # os.path because this one has to work on sequences of ints

    insert_length = common_prefix_length(change1.insert, change2.insert)
    delete_length = common_prefix_length(change1.delete, change2.delete)

    return insert_length, delete_length
