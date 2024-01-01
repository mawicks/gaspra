import io
from gaspra.suffix_automaton import build, Node
from gaspra.revision_tree import Tree


def dump(node: Node, f: io.TextIOWrapper):
    queue = [node]
    processed = set()

    while queue:
        current = queue.pop()

        if current.id not in processed:
            if current.is_terminal:
                f.write(f" {current.id}[color=red]\n")

            for token, child in current.transitions.items():
                f.write(f' {current.id} -> {child.id} [label="{token}"]\n')
                queue.append(child)

        processed.add(current.id)

    return


def dot_dump(s: str, filename: str):
    root = build(s)

    with open(filename, "w") as f:
        f.write("digraph G {\n")
        f.write("  rankdir=LR\n")
        dump(root, f)
        f.write("}\n")


def revision_dot_dump(tree: Tree, filename: str):
    with open(filename, "wt") as f:
        f.write("digraph G {\n")
        f.write("  rankdir=LR\n")
        for edge in tree.edges():
            v1, v2 = sorted(edge)
            f.write(f" {v2} -> {v1}\n")
        f.write("}\n")


def test_dot_dump():
    dot_dump("abc", "abc.dot")
    dot_dump("ababab", "ababab.dot")
    dot_dump("abc0cdabchi1abcabcxyz", "multiple.dot")


def test_revision_dot_dump():
    tree = Tree()
    for node_id in range(100):
        tree.insert(node_id)

    revision_dot_dump(tree, "revision.dot")


if __name__ == "__main__":
    test_revision_dot_dump()
