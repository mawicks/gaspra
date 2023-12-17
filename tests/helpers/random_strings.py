import random

def random_string(alphabet: str, length):
    return "".join(random.choices(alphabet, k=length))
