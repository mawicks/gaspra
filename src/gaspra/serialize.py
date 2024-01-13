from gaspra.types import StrippedChangeIterable


def vserialize_int(value: int):
    """Variable length integer serialization used by SQLite"""
    if value <= 240:
        return value.to_bytes(1, "big")
    if value <= 2287:
        excess = value - 240
        return int(241 + excess / 256).to_bytes(1, "big") + int(excess % 256).to_bytes(
            1, "big"
        )
    if value <= 67823:
        excess = value - 2288
        return (
            int(249).to_bytes(1, "big")
            + int(excess / 256).to_bytes(1, "big")
            + int(excess % 256).to_bytes(1, "big")
        )
    if value <= 16777215:
        code, length = 250, 3
        return int(250).to_bytes(1, "big") + value.to_bytes(3, "big")
    elif value <= 4294967295:
        code, length = 251, 4
        return int(251).to_bytes(1, "big") + value.to_bytes(4, "big")
    elif value <= 1099511627775:
        code, length = 252, 5
        return int(252).to_bytes(1, "big") + value.to_bytes(5, "big")
    elif value <= 281474976710655:
        code, length = 253, 6
        return int(253).to_bytes(1, "big") + value.to_bytes(6, "big")
    elif value <= 72057594037927935:
        code, length = 254, 7
        return int(254).to_bytes(1, "big") + value.to_bytes(7, "big")
    else:
        code, length = 255, 8
    return int(code).to_bytes(1, "big") + value.to_bytes(length, "big")


def vdeserialize_int(stream: bytes):
    """Variable length integer deserialization used by SQLite"""
    if len(stream) < 1:
        raise RuntimeError("Premature end of stream")

    a0 = int.from_bytes(stream[:1], "big")
    if 0 <= a0 <= 240:
        return a0, stream[1:]
    if 241 <= a0 <= 248:
        a1 = int.from_bytes(stream[1:2], "big")
        if len(stream) < 2:
            raise RuntimeError("Premature end of stream")
        return 240 + 256 * (a0 - 241) + a1, stream[2:]
    if a0 == 249:
        if len(stream) < 3:
            raise RuntimeError("Premature end of stream")
        return 2288 + int.from_bytes(stream[1:3], "big"), stream[3:]
    end = a0 - 246
    if len(stream) < end:
        raise RuntimeError("Premature end of stream")
    return int.from_bytes(stream[1:end], "big"), stream[end:]


def serialize_int(value: int):
    return value.to_bytes(4, "big")


def deserialize_int(stream: bytes):
    if len(stream) < 4:
        raise RuntimeError("Stream ended prematurely")

    value = int.from_bytes(stream[:4], "big")
    return value, stream[4:]


def serialize_changeset(changeset: StrippedChangeIterable):
    serialized = b""

    # First fragment in serialization must come from bytes object.
    # If first object is slice, insert an empty bytes object.
    next_is_bytes = True
    for change in changeset:
        # If expecting bytes and got slice, insert
        # an empty bytes object to sync up.
        if next_is_bytes and type(change) == slice:
            serialized += vserialize_int(0)
        # If expecting slice and got bytes, insert
        # an empty slice object to sync up.
        elif not next_is_bytes and type(change) == bytes:
            serialized += vserialize_int(0)
            serialized += vserialize_int(0)

        if type(change) is bytes:
            serialized += vserialize_int(len(change))
            serialized += change
            next_is_bytes = False
        elif type(change) is slice:
            serialized += vserialize_int(change.start)
            serialized += vserialize_int(change.stop)
            next_is_bytes = True
        else:
            raise RuntimeError(f"Unexpected type: {type(change)}")

    return serialized


def deserialize_changeset(stream: bytes) -> StrippedChangeIterable:
    next_is_bytes = True

    while len(stream):
        if next_is_bytes:
            length, stream = vdeserialize_int(stream)
            if length:
                if len(stream) < length:
                    raise RuntimeError("Stream ended prematurely")
                yield stream[:length]
            stream = stream[length:]
            next_is_bytes = False
        else:
            start, stream = vdeserialize_int(stream)
            stop, stream = vdeserialize_int(stream)
            if start != stop:
                yield slice(start, stop)
            next_is_bytes = True
