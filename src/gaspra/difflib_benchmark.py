import random
import difflib
import time

from tabulate import tabulate
from gaspra.suffix_automaton import build, find_lcs


def random_string(alphabet, length):
    return "".join(random.choices(alphabet, k=length))


def difflib_lcs(s1, s2):
    sm = difflib.SequenceMatcher(
        a=s1,
        b=s2,
        autojunk=False,
    )
    return sm.find_longest_match()


def string_matching_lcs(s1, s2):
    return find_lcs(build(s1), s2)


def timeit(method, method_name, s1, s2, index=False):
    start = time.perf_counter_ns()

    p1, p2, length = method(s1, s2)
    print((p1, p2, length))
    duration_ms = round((time.perf_counter_ns() - start) / 1e6, 0)

    row = {}
    if index:
        row = {"Length": f"{(len(s1) + len(s2)) // 1024}k", "Match Length": length}
    the_rest = {f"{method_name} (ms)": duration_ms}
    row.update(the_rest)
    return row


difflib_results = []
string_matching_results = []


def make_string_pairs():
    results = []
    for n in range(0, 3, 1):
        length = 1_024 * 2**n
        results.append(tuple(random_string("abc", length) for _ in range(2)))
    return results


def make_table(method, method_name, string_list, index=True):
    results = []

    for strings in string_list:
        results.append(timeit(method, method_name, *strings, index=index))

    return results


def render_table(table):
    return tabulate(
        table, headers="keys", tablefmt="github", intfmt=",d", floatfmt=",.0f"
    )


def render_tables():
    string_list = make_string_pairs()
    combined = []
    for r1, r2 in zip(
        make_table(difflib_lcs, "Difflib", string_list, True),
        make_table(string_matching_lcs, "Gaspra", string_list, False),
    ):
        full_row = r1.copy()
        full_row.update(r2)
        combined.append(full_row)

    return render_table(combined)


if __name__ == "__main__":
    print(render_tables())
