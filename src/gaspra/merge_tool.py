import argparse
import os

from rich.console import Console

from gaspra.merge import merge
from gaspra.changesets import escape, diff

TEST_CASE_DIRECTORY = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "test-cases",
    )
)

PROGRAM_NAME = os.path.basename(__file__)


def get_test_case():
    parser = argparse.ArgumentParser(usage=get_usage())
    parser.add_argument("test_case")
    args = parser.parse_args()
    return args.test_case


def get_usage():
    return (
        f"{PROGRAM_NAME} test_case\nValid test cases are:\n\t"
        + "\n\t".join(TEST_CASES)
        + "\n"
    )


def show_changes(console, fragment_sequence, name=""):
    console.print(f"\n[blue]<<<{escape(name)}>>>[/blue]")
    for fragment in fragment_sequence:
        if isinstance(fragment, str):
            console.print(fragment, end="")

        if isinstance(fragment, tuple):
            console.print(f"[green]{escape(fragment[0])}[/]", end="")
            console.print(f"[red]{escape(fragment[1])}[/]", end="")


def show_changes_line_oriented(console, fragment_sequence, name=""):
    console.print(f"\n[blue]<<<{escape(name)}>>>[/blue]")

    in_conflict = False
    partial_line_0 = partial_line_1 = ""
    any_line_0 = any_line_1 = False
    for fragment in fragment_sequence:
        if isinstance(fragment, str):
            lines = fragment.split("\n")
            if in_conflict:
                partial_line_0 = partial_line_0 + lines[0]
                partial_line_1 = partial_line_1 + lines[0]
                if len(lines) > 1:
                    if any_line_0:
                        console.print(f"[green]{escape(partial_line_0)}[/]")
                    if any_line_1:
                        console.print(f"[red]{escape(partial_line_1)}[/]")
                    partial_line_0 = partial_line_1 = ""
                    any_line_0 = any_line_1 = in_conflict = False
                    console.print(escape("\n".join(lines[1:-1])))
                    partial_line_0 = lines[-1]
                    partial_line_1 = lines[-1]
            else:
                console.print(escape(partial_line_0))
                # If not in a conflict, partial_line_0 should be
                # exactly the same as partial_line_1.
                console.print(escape("\n".join(lines[:-1])))
                partial_line_0 = lines[-1]
                partial_line_1 = lines[-1]

        if isinstance(fragment, tuple):
            in_conflict = True
            if fragment[0]:
                partial_line_0 = partial_line_0 + fragment[0]
                any_line_0 = True
            if fragment[1]:
                partial_line_1 = partial_line_1 + fragment[1]
                any_line_1 = True


TEST_CASES = [
    "About.java",
    "ErrorMsg.java",
    "FlownetController.cpp",
    "Misc.java",
    "RearViewMirror.java",
    "ServerWin_2005.vcproj",  # This is the "real world" anchor moves example.
    "ServerWin_2005.vcproj.Reduced",
    "getCLIArgs.java",
    "chunks",
    "ReleaseNotes",
    "Bug_ReporterApp",
]


# 0 - Perfect.  No issues at all.
# 1 - Conflicts that are handled correctly.
# 2 - Conflicts that are handled correctly.
# 3 - Conflicts that are handled correctly.
# 4 - Technically correct, but SureMerge says they would have flagged it.
# 5 - Too long to tell. (This is the "real world" moves test.)
# 6 - Perfect (Shorter version of real world).
# 7 - Duplicated some code but it's arguably correct.
# 8 - Perfect but it had a weird split.
# 9 - Perfect, but it easily have gone otherwise.


def get_specific_test_case():
    return TEST_CASES[6]


display_function = show_changes_line_oriented

EXCEPTIONS = {
    "chunks": ("chunks_1_0.c", "chunks_1_1.c", "chunks_1_2.c"),
    "ReleaseNotes": (
        "ReleaseNotes 9_4.html",
        "ReleaseNotes 9_4_1.html",
        "ReleaseNotes 9_4_2.html",
    ),
    "Bug_ReporterApp": (
        "Bug_ReporterApp_Parent.h",
        "Bug_ReporterApp_BranchA.h",
        "Bug_ReporterApp_BranchB.h",
    ),
}


def get_file_versions(test_case):
    if test_case in EXCEPTIONS:
        return EXCEPTIONS[test_case]

    parent = f"{test_case}.parent"
    branch0 = f"{test_case}.1st"
    branch1 = f"{test_case}.2nd"
    return parent, branch0, branch1


if __name__ == "__main__":
    console = Console(force_terminal=True, highlight=False)

    test_case = get_specific_test_case()

    parent, branch0, branch1 = get_file_versions(test_case)

    def get_text(filename):
        with open(os.path.join(TEST_CASE_DIRECTORY, filename), "rb") as f:
            data = f.read()
            return data.decode("ISO-8859-1")

    parent_text = get_text(parent)
    branch0_text = get_text(branch0)
    branch1_text = get_text(branch1)

    display_function(console, [parent_text], "Original")

    changes0 = diff(parent_text, branch0_text)
    changes1 = diff(parent_text, branch1_text)
    display_function(console, changes0, "Branch 0 Changes")
    display_function(console, changes1, "Branch 1 Changes")

    merged = merge(parent_text, branch0_text, branch1_text)
    display_function(console, merged, "Merged")
