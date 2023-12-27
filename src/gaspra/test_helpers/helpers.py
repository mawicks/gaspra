from collections.abc import Sequence
import random


def random_string(alphabet: str, length, seed=42):
    rng = random.Random(seed)
    return "".join(rng.choices(alphabet, k=length))


def random_tokens(alphabet: Sequence[int], length, seed=42):
    rng = random.Random(seed)
    return tuple(rng.choices(alphabet, k=length))


def tokenize(string_or_fragment_list):
    if isinstance(string_or_fragment_list, str):
        return tuple(ord(character) for character in string_or_fragment_list)

    elif isinstance(string_or_fragment_list, tuple | list):
        return tuple(tokenize(fragment) for fragment in string_or_fragment_list)
    else:
        raise TypeError(f"Unsupported fragment type: {type(string_or_fragment_list)}")
