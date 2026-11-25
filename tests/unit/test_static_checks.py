"""Parseurs testés avec les sorties réelles de epiclang et banana-check-repo (image epitest)."""

from vibe_mouli import static_checks

EPICLANG_OUT = """\
a.c:4:1: warning: [Banana] [Minor] tab used for indentation (C-L2)
    4 |         printf("aaaa");
      | ^
a.c:4:113: warning: [Banana] [Minor] trailing space (C-G7)
a.c:1:1: warning: [Banana] [Minor] file not starting with standard Epitech header (C-G1)
a.c:4:78: warning: [Banana] [Major] 116-character line (C-F3)
4 warnings generated.
"""

REPO_OUT = """\
Checking delivery files in /job/src
/job/src/a.o: [Banana] [Major] unwanted file (C-O1)
"""


def test_epiclang_real_output_is_parsed_and_context_ignored():
    items = static_checks.parse_epiclang(EPICLANG_OUT)
    assert [(i.file, i.line, i.col, i.severity, i.code) for i in items] == [
        ("a.c", 4, 1, "MINOR", "C-L2"),
        ("a.c", 4, 113, "MINOR", "C-G7"),
        ("a.c", 1, 1, "MINOR", "C-G1"),
        ("a.c", 4, 78, "MAJOR", "C-F3"),
    ]


def test_epiclang_duplicates_are_merged():
    text = EPICLANG_OUT + EPICLANG_OUT
    assert len(static_checks.parse_epiclang(text)) == 4


def test_epiclang_errors_exclude_banana_warnings():
    text = "a.c:3:10: error: 'foo.h' file not found\n" + EPICLANG_OUT
    assert static_checks.epiclang_errors(text) == ["a.c:3:10: error: 'foo.h' file not found"]


def test_banana_repo_real_output_strips_container_prefix():
    items = static_checks.parse_banana_repo(REPO_OUT)
    assert [(i.file, i.severity, i.code) for i in items] == [("a.o", "MAJOR", "C-O1")]


def test_banana_repo_clean_output_has_no_infraction():
    assert static_checks.parse_banana_repo("Checking delivery files in /job/src\n") == []
