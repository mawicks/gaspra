import os

from gaspra.common import DATA_DIR

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


def get_filenames(test_case: str):
    if test_case in EXCEPTIONS:
        parent, branch0, branch1 = EXCEPTIONS[test_case]
    else:
        parent = f"{test_case}.parent"
        branch0 = f"{test_case}.1st"
        branch1 = f"{test_case}.2nd"

    parent = os.path.join(TEST_CASE_DIRECTORY, parent)
    branch0 = os.path.join(TEST_CASE_DIRECTORY, branch0)
    branch1 = os.path.join(TEST_CASE_DIRECTORY, branch1)
    return parent, branch0, branch1


def get_usage():
    return (
        f"{PROGRAM_NAME} test_case\nValid test cases are:\n\t"
        + "\n\t".join(TEST_CASES)
        + "\n"
    )
