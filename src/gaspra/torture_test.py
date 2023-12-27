import argparse
import os

from rich.console import Console
from gaspra.markup import GIT_MARKUP, SCREEN_MARKUP, markup_changes

from gaspra.merge import merge
from gaspra.changesets import diff
from gaspra.markup import (
    line_oriented_markup_changes,
)

TEST_CASE_DIRECTORY = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "test-cases",
    )
)
PROGRAM_NAME = os.path.basename(__file__)


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


def get_file_versions(test_case: str):
    if test_case in EXCEPTIONS:
        return EXCEPTIONS[test_case]

    parent = f"{test_case}.parent"
    branch0 = f"{test_case}.1st"
    branch1 = f"{test_case}.2nd"
    return parent, branch0, branch1


def get_usage():
    return (
        f"{PROGRAM_NAME} test_case\nValid test cases are:\n\t"
        + "\n\t".join(TEST_CASES)
        + "\n"
    )


def get_arguments():
    parser = argparse.ArgumentParser(usage=get_usage())
    parser.add_argument("test_case")
    parser.add_argument(
        "-l",
        "--line-oriented",
        action="store_true",
        help="Show lines changed rather than fragments changed",
    )
    parser.add_argument(
        "-d", "--diff", action="store_true", help="Show diffs along with merge"
    )
    parser.add_argument(
        "-f",
        "--file-style",
        action="store_true",
        help="Mark up for files (git-style, no color)",
    )
    args = parser.parse_args()
    return args


def get_display_function(arguments):
    if arguments.line_oriented:
        return line_oriented_markup_changes

    return markup_changes


def get_markup_style(arguments):
    if arguments.file_style:
        return GIT_MARKUP
    else:
        return SCREEN_MARKUP


if __name__ == "__main__":
    console = Console(force_terminal=True, highlight=False)

    def console_print_function(s):
        console.print(s, end="")

    print_function = console_print_function

    arguments = get_arguments()
    display_function = get_display_function(arguments)
    markup = get_markup_style(arguments)

    parent, into_branch, from_branch = get_file_versions(arguments.test_case)

    def get_text(filename):
        with open(
            os.path.join(TEST_CASE_DIRECTORY, filename), "rt", encoding="ISO-8859-1"
        ) as f:
            data = f.read()
            return data

    parent_text = get_text(parent)
    into_text = get_text(into_branch)
    from_text = get_text(from_branch)

    into_changes = diff(parent_text, into_text)
    from_changes = diff(parent_text, from_text)

    print_fn = console.print

    if arguments.diff:
        display_function(
            print_function,
            into_changes,
            into_branch,
            parent,
            markup=markup,
            header=into_branch,
        )
        display_function(
            print_function,
            from_changes,
            from_branch,
            parent,
            markup=markup,
            header=from_branch,
        )

    merged = merge(parent_text, into_text, from_text)
    display_function(
        print_function,
        merged,
        into_branch,
        from_branch,
        markup=markup,
        header="Merged" if arguments.diff else None,
    )