import gaspra


def merge_example():
    original = "The quick brown fox jumps over the lazy dog near the riverbank."
    branch1 = "The quick brown fox leaps over the lazy dogs near the river."
    branch2 = "The quick, clever fox jumps across the lazy dogs by the riverbank."
    conflicts_with_1 = (
        "The swift, agile fox leaps over the sleepy dog near the riverside."
    )

    print(f"Original:\n   {original}")
    print(f"Editor1:\n   {branch1}")
    print(f"Changes:\n   {list(gaspra.changes(original, branch1))}\n")

    print(f"Editor2:\n   {branch2}")
    print(f"Changes:\n   {list(gaspra.changes(original, branch2))}")
    print(f"Merge:   {list(gaspra.merge(original, branch1, branch2))}\n")

    print(f"Editor2 (alt):\n   {conflicts_with_1}")
    print(f"Changes:\n   {list(gaspra.changes(original, conflicts_with_1))}")
    print(f"Merge:   {list(gaspra.merge(original, branch1, conflicts_with_1))}\n")


if __name__ == "__main__":
    merge_example()
