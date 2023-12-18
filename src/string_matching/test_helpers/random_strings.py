import random


def random_string(alphabet: str, length, seed=42):
    rng = random.Random(seed)
    return "".join(rng.choices(alphabet, k=length))
