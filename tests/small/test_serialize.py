import pytest

from gaspra.serialize import (
    serialize_changeset,
    deserialize_changeset,
    vserialize_int,
    vdeserialize_int,
)

INPUT_AND_OUTPUT_CASES = [
    (
        (b"abc", slice(1, 2), b"xyz"),
        b"\003abc\001\002\003xyz",
    ),
    (
        (slice(1, 2), b"abc", slice(3, 4)),
        b"\000\001\002\003abc\003\004",
    ),
]

ROUND_TRIP_CASES = [
    (b"abc", slice(1, 2), b"xyz"),
    (slice(1, 2), b"abc", slice(3, 4)),
    (b"abc", slice(1, 2), slice(3, 4), b"xyz"),
    (b"abc", slice(1, 2), slice(3, 4), b"xyz"),
    (slice(1, 2), slice(3, 4), b"xyz"),
]


@pytest.mark.parametrize("changeset,serialization", INPUT_AND_OUTPUT_CASES)
def test_serialize(changeset, serialization):
    assert serialize_changeset(changeset) == serialization


@pytest.mark.parametrize("changeset", ROUND_TRIP_CASES)
def test_round_trip(changeset):
    serialization = serialize_changeset(changeset)
    deserialization = tuple(deserialize_changeset(serialization))
    assert deserialization == changeset


ROUND_TRIP_INT_CASES = [
    0,
    1,
    239,
    240,
    241,
    2286,
    2287,
    2288,
    67822,
    67823,
    67824,
    16777214,
    16777215,
    16776216,
    4294967294,
    4294967295,
    4294967296,
    1099511627774,
    1099511627775,
    18446744073709551615,
]


@pytest.mark.parametrize("value", ROUND_TRIP_INT_CASES)
def test_round_trip_vserialize_int(value):
    serialized = vserialize_int(value)
    round_trip_value, tail = vdeserialize_int(serialized)
    assert round_trip_value == value
    assert len(tail) == 0


def test_large_values_fail_to_serialize():
    with pytest.raises(OverflowError):
        vserialize_int(18446744073709551616)
