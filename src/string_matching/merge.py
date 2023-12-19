from dataclasses import replace

from string_matching.changesets import find_changeset, FragmentType


def do_merge(parent: str, branch0: str, branch1: str):
    changeset0 = find_changeset(parent, branch0)
    changeset1 = find_changeset(parent, branch1)

    fragments0 = list(reversed(list(changeset0.fragments(parent))))
    fragments1 = list(reversed(list(changeset1.fragments(parent))))

    output = []
    while fragments0 and fragments1:
        fragment0 = fragments0.pop()
        fragment1 = fragments1.pop()

        if (
            fragment0.fragment_type == fragment1.fragment_type == FragmentType.COPY
            or fragment0.fragment_type == fragment1.fragment_type == FragmentType.SKIP
        ):
            # Marching inserts and matching copies are treated exactly the same.
            copy_copy(fragment0, fragment1, fragments0, fragments1, output)

        elif (
            fragment0.fragment_type == FragmentType.COPY
            and fragment1.fragment_type == FragmentType.SKIP
        ):
            copy_skip(fragment0, fragment1, fragments0, fragments1, output)
        elif (
            fragment0.fragment_type == FragmentType.SKIP
            and fragment1.fragment_type == FragmentType.COPY
        ):
            copy_skip(fragment1, fragment0, fragments1, fragments0, output)

        elif fragment0.fragment_type == FragmentType.INSERT != fragment1.fragment_type:
            insert_other(fragment0, fragment1, fragments1, output)
        elif fragment1.fragment_type == FragmentType.INSERT != fragment0.fragment_type:
            insert_other(fragment1, fragment0, fragments0, output)
        elif fragment0.fragment_type == fragment1.fragment_type == FragmentType.INSERT:
            insert_insert(fragment0, fragment1, output)
        continue

    if fragments0 or fragments1:
        remaining = fragments0 or fragments1
        output.extend(reversed(remaining))

    result = "".join(
        [
            fragment.content
            for fragment in output
            if fragment.fragment_type != FragmentType.SKIP
        ]
    )
    return result


def copy_copy(fragment0, fragment1, fragment0_queue, fragment1_queue, output):
    if fragment0.length < fragment1.length:
        shorter, longer = fragment0, fragment1
        long_queue = fragment1_queue
    else:
        shorter, longer = fragment1, fragment0
        long_queue = fragment0_queue

    output.append(shorter)
    if shorter.length != longer.length:
        longer = replace(
            longer,
            content=longer.content[shorter.length :],
            length=longer.length - shorter.length,
        )
        long_queue.append(longer)
    return


def copy_skip(
    copy_fragment, skip_fragment, copy_fragment_queue, skip_fragment_queue, output
):
    smaller_length = min(copy_fragment.length, skip_fragment.length)

    skip_head, skip_tail = split_fragment(skip_fragment, smaller_length)
    __ignored__, copy_tail = split_fragment(copy_fragment, smaller_length)

    output.append(skip_head)

    if skip_tail.length > 0:
        skip_fragment_queue.append(skip_tail)
    if copy_tail.length > 0:
        copy_fragment_queue.append(copy_tail)


def insert_other(insert_fragment, other_fragment, other_fragment_queue, output):
    output.append(insert_fragment)
    other_fragment_queue.append(other_fragment)


# This is the primary place that collisions occur.
# This is really just a stub to be replaced with a more extensive function.


def insert_insert(fragment0, fragment1, output):
    output.append(fragment0)
    output.append(fragment1)


def split_fragment(fragment, length):
    head = replace(fragment, content=fragment.content[:length], length=length)
    tail = replace(
        fragment, content=fragment.content[length:], length=fragment.length - length
    )
    return head, tail
