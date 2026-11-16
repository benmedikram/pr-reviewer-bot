# tests/test_chunking.py
from reviewer.chunking import chunk_diff, split_files
from reviewer.diff import parse_diff


def new_file(path, n, marker=False):
    lines = [f"diff --git a/{path} b/{path}", "new file mode 100644", "--- /dev/null",
             f"+++ b/{path}", f"@@ -0,0 +1,{n} @@"]
    lines += [f"+line {i} " + "x" * 30 for i in range(1, n + 1)]
    if marker:
        lines.append("\\ No newline at end of file")
    return "\n".join(lines) + "\n"


def modified_file(path):
    lines = [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}"]
    for old_start, new_start in ((1, 1), (101, 102), (201, 203)):
        lines.append(f"@@ -{old_start},40 +{new_start},41 @@")
        lines += [f" ctx {i}" for i in range(40)] + ["+added"]
    return "\n".join(lines) + "\n"


def test_small_diff_is_one_chunk():
    text = new_file("a.py", 3)
    assert chunk_diff(text, 6000) == [text]


def test_big_new_file_is_split_without_losing_lines():
    text = new_file("big.py", 400)
    chunks = chunk_diff(text, 2000)
    assert len(chunks) > 1
    assert all(len(c) <= 2000 for c in chunks)
    assert all(c.startswith("diff --git") for c in chunks)
    assert parse_diff("".join(chunks)) == parse_diff(text) == {"big.py": set(range(1, 401))}


def test_modified_file_is_split_at_hunk_boundaries():
    text = modified_file("m.py")
    chunks = chunk_diff(text, 900)
    assert len(chunks) >= 2
    assert parse_diff("".join(chunks)) == parse_diff(text) == {"m.py": {41, 142, 243}}


def test_small_files_are_packed_together():
    text = new_file("a.py", 3) + new_file("b.py", 3)
    assert len(split_files(text)) == 2
    assert chunk_diff(text, 6000) == [text]


def test_no_newline_marker_stays_with_its_line():
    text = new_file("m.py", 300, marker=True)
    chunks = chunk_diff(text, 2000)
    assert parse_diff("".join(chunks)) == parse_diff(text)
    for chunk in chunks:
        lines = chunk.splitlines()
        assert not any(a.startswith("@@") and b.startswith("\\") for a, b in zip(lines, lines[1:]))


def test_rename_without_hunks_is_kept_whole():
    text = "diff --git a/old.py b/new.py\nsimilarity index 100%\nrename from old.py\nrename to new.py\n"
    assert chunk_diff(text, 50) == [text]