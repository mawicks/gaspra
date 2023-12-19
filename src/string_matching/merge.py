from dataclasses import replace

from string_matching.changesets import (
    find_changeset,
    CopyFragment,
    ChangeFragment,
    ConflictFragment,
)


def do_merge(parent: str, branch0: str, branch1: str):
    changeset0 = find_changeset(parent, branch0)
    changeset1 = find_changeset(parent, branch1)

    fragments0 = list(reversed(list(changeset0.fragments(parent))))
    fragments1 = list(reversed(list(changeset1.fragments(parent))))

    output = []
    while fragments0 and fragments1:
        fragment0 = fragments0.pop()
        fragment1 = fragments1.pop()

        if isinstance(fragment0, CopyFragment) and isinstance(fragment1, CopyFragment):
            copy_copy(fragment0, fragment1, fragments0, fragments1, output)

        elif isinstance(fragment0, ChangeFragment) and isinstance(
            fragment1, ChangeFragment
        ):
            change_change(fragment0, fragment1, fragments0, fragments1, output)

        elif isinstance(fragment0, CopyFragment) and isinstance(
            fragment1, ChangeFragment
        ):
            copy_change(fragment0, fragment1, fragments0, fragments1, output)

        elif isinstance(fragment0, ChangeFragment) and isinstance(
            fragment1, CopyFragment
        ):
            copy_change(fragment1, fragment0, fragments1, fragments0, output)

        else:
            raise RuntimeError(
                f"Unexpected types: {type(fragment0)} or {type(fragment1)}"
            )

        continue

    if fragments0 or fragments1:
        remaining = fragments0 or fragments1
        output.extend(reversed(remaining))

    result = "".join([fragment.insert for fragment in output])
    return result


def copy_copy(
    fragment0: CopyFragment,
    fragment1: CopyFragment,
    fragment0_queue,
    fragment1_queue,
    output,
):
    if fragment0.length < fragment1.length:
        shorter, longer = fragment0, fragment1
        long_queue = fragment1_queue
    else:
        shorter, longer = fragment1, fragment0
        long_queue = fragment0_queue

    output.append(shorter)
    if shorter.length != longer.length:
        __ignored__, tail = split_copy_fragment(longer, shorter.length)
        long_queue.append(tail)
    return


def copy_change(
    copy_fragment, change_fragment, copy_fragment_queue, change_fragment_queue, output
):
    smaller_length = min(copy_fragment.length, change_fragment.length)
    if change_fragment.length == smaller_length:
        output.append(change_fragment)
        # Anything left over?
        if copy_fragment.length > smaller_length:
            __ignored__, copy_tail = split_copy_fragment(copy_fragment, smaller_length)
            copy_fragment_queue.append(copy_tail)
    else:  # Change is longer than copy implies a conflict.
        head0, head1 = split_change_fragment(
            change_fragment, len(change_fragment.insert), smaller_length
        )
        if head0:
            output.append(
                ConflictFragment(head0.insert, copy_fragment.insert, smaller_length)
            )
        if head1:
            change_fragment_queue.append(head1)


def change_change(
    fragment0: ChangeFragment, fragment1: ChangeFragment, fragments0, fragments1, output
):
    insert_length, delete_length = common_head_of_change(fragment0, fragment1)
    if insert_length > 0 or delete_length > 0:
        head0, tail0 = split_change_fragment(fragment0, insert_length, delete_length)
        output.append(head0)
        fragments0.append(tail0)
        __x__, tail1 = split_change_fragment(fragment1, insert_length, delete_length)
        fragments1.append(tail1)
    else:
        length = min(fragment0.length, fragment1.length)
        head0, tail0 = split_change_fragment(fragment0, len(fragment0.insert), length)
        head1, tail1 = split_change_fragment(fragment1, len(fragment1.insert), length)
        if head0 and head1:
            output.append(ConflictFragment(head0.insert, head1.insert, length))
        if tail0:
            fragments0.append(tail0)
        if tail1:
            fragments1.append(tail1)


def split_copy_fragment(fragment: CopyFragment, length: int):
    head = replace(fragment, insert=fragment.insert[:length], length=length)
    tail = replace(
        fragment, insert=fragment.insert[length:], length=fragment.length - length
    )
    return head, tail


def split_change_fragment(fragment: ChangeFragment, insert_length, length: int):
    head = tail = None
    if length > 0:
        head = replace(
            fragment,
            insert=fragment.insert[:insert_length],
            delete=fragment.delete[:length],
            length=length,
        )
    if length < fragment.length:
        tail = replace(
            fragment,
            insert=fragment.insert[insert_length:],
            delete=fragment.delete[length:],
            length=fragment.length - length,
        )
    return head, tail


def common_length(s1, s2):
    length = 0
    max_length = min(len(s1), len(s2))
    for length, (c1, c2) in enumerate(zip(s1, s2)):
        if c1 != c2:
            break
    else:
        length = max_length
    return length


def common_head_of_change(change1: ChangeFragment, change2: ChangeFragment):
    insert_length = common_length(change1.insert, change2.insert)
    delete_length = common_length(change1.delete, change2.delete)

    return insert_length, delete_length
