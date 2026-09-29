from reviewer.diff import filter_findings, parse_diff


def d(*lines):
    return "\n".join(lines) + "\n"


def test_added_lines_use_new_file_numbers():
    diff = d(
        "diff --git a/src/app.py b/src/app.py",
        "--- a/src/app.py",
        "+++ b/src/app.py",
        "@@ -1,4 +1,5 @@",
        " import os",
        "+import sys",
        " ",
        " def f(x):",
        "-    return x",
        "+    return x + 1",
    )
    assert parse_diff(diff) == {"src/app.py": {2, 5}}


def test_multiple_hunks():
    diff = d(
        "--- a/m.py",
        "+++ b/m.py",
        "@@ -1,3 +1,4 @@",
        " a",
        "+b",
        " c",
        " d",
        "@@ -10,3 +11,4 @@",
        " x",
        " y",
        "+z",
        " w",
    )
    assert parse_diff(diff) == {"m.py": {2, 13}}


def test_new_file():
    diff = d(
        "diff --git a/new.py b/new.py",
        "new file mode 100644",
        "--- /dev/null",
        "+++ b/new.py",
        "@@ -0,0 +1,3 @@",
        "+one",
        "+two",
        "+three",
    )
    assert parse_diff(diff) == {"new.py": {1, 2, 3}}


def test_deleted_file_has_no_commentable_lines():
    diff = d(
        "diff --git a/old.py b/old.py",
        "deleted file mode 100644",
        "--- a/old.py",
        "+++ /dev/null",
        "@@ -1,2 +0,0 @@",
        "-one",
        "-two",
    )
    assert parse_diff(diff) == {}


def test_content_that_looks_like_a_header():
    diff = d(
        "--- a/q.sql",
        "+++ b/q.sql",
        "@@ -1,2 +1,2 @@",
        "--- sql comment",
        "+++ new comment",
        " SELECT 1;",
    )
    assert parse_diff(diff) == {"q.sql": {1}}


def test_no_newline_marker_is_ignored():
    diff = d(
        "--- a/n.txt",
        "+++ b/n.txt",
        "@@ -1 +1 @@",
        "-old",
        "\\ No newline at end of file",
        "+new",
        "\\ No newline at end of file",
    )
    assert parse_diff(diff) == {"n.txt": {1}}


def test_filter_findings_drops_lines_outside_the_diff():
    added = {"m.py": {2, 13}}
    findings = [
        {"file": "m.py", "line": 2, "message": "in the diff"},
        {"file": "m.py", "line": 7, "message": "outside the diff"},
        {"file": "other.py", "line": 2, "message": "file not in the diff"},
    ]
    kept, dropped = filter_findings(findings, added)
    assert [f["message"] for f in kept] == ["in the diff"]
    assert len(dropped) == 2