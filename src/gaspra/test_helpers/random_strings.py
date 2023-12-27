from collections.abc import Sequence
import random


def random_string(alphabet: str, length, seed=42):
    rng = random.Random(seed)
    return "".join(rng.choices(alphabet, k=length))


def random_tokens(alphabet: Sequence[int], length, seed=42):
    rng = random.Random(seed)
    return tuple(rng.choices(alphabet, k=length))
