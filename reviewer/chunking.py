# reviewer/chunking.py
"""Split a unified diff into pieces small enough for one model call.

Large files are split at hunk boundaries. A hunk larger than the limit is split
between lines, with a corrected @@ header for each piece. Nothing is truncated,
so no added line is dropped and line numbers stay right."""
import re

HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
MARGIN = 200  # room for a rewritten @@ header


def split_files(diff_text: str) -> list[str]:
    """One string per file, each starting with its 'diff --git' line."""
    files, current = [], []
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("diff --git") and current:
            files.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        files.append("".join(current))
    return files


def _split_hunk(header: str, body: list[str], budget: int) -> list[str]:
    """Split one hunk into several hunks of at most ~budget characters."""
    m = HUNK_HEADER.match(header.rstrip("\r\n"))
    old_start, new_start, tail = int(m.group(1)), int(m.group(3)), m.group(5)
    units: list[list[str]] = []
    for line in body:
        if line.startswith("\\") and units:
            units[-1].append(line)  # "\ No newline at end of file" stays with its line
        else:
            units.append([line])
    groups, cur, size = [], [], 0
    for unit in units:
        length = sum(len(x) for x in unit)
        if cur and size + length > budget:
            groups.append(cur)
            cur, size = [], 0
        cur.append(unit)
        size += length
    if cur:
        groups.append(cur)
    pieces, old_done, new_done = [], 0, 0
    for group in groups:
        old_n = new_n = 0
        for unit in group:
            tag = unit[0][:1]
            if tag != "+":
                old_n += 1
            if tag != "-":
                new_n += 1
        pieces.append(
            f"@@ -{old_start + old_done},{old_n} +{new_start + new_done},{new_n} @@{tail}\n"
            + "".join(x for unit in group for x in unit)
        )
        old_done += old_n
        new_done += new_n
    return pieces


def split_file(file_text: str, max_chars: int) -> list[str]:
    """Split one file's diff into chunks of at most ~max_chars, each with the file header."""
    if len(file_text) <= max_chars:
        return [file_text]
    lines = file_text.splitlines(keepends=True)
    first = next((i for i, l in enumerate(lines) if l.startswith("@@")), None)
    if first is None:
        return [file_text]  # rename, mode change or binary file: no hunks to split
    file_header = "".join(lines[:first])
    hunks, cur = [], []
    for line in lines[first:]:
        if line.startswith("@@") and cur:
            hunks.append(cur)
            cur = [line]
        else:
            cur.append(line)
    hunks.append(cur)
    budget = max(max_chars - len(file_header) - MARGIN, 500)
    pieces = []
    for hunk in hunks:
        text = "".join(hunk)
        pieces.extend([text] if len(text) <= budget else _split_hunk(hunk[0], hunk[1:], budget))
    out, cur = [], ""
    for piece in pieces:
        if cur and len(file_header) + len(cur) + len(piece) > max_chars:
            out.append(file_header + cur)
            cur = piece
        else:
            cur += piece
    out.append(file_header + cur)
    return out


def pack(pieces: list[str], max_chars: int) -> list[str]:
    """Group consecutive pieces into calls of at most ~max_chars, never splitting a piece."""
    packed, cur = [], ""
    for piece in pieces:
        if cur and len(cur) + len(piece) > max_chars:
            packed.append(cur)
            cur = piece
        else:
            cur += piece
    if cur:
        packed.append(cur)
    return packed


def chunk_diff(diff_text: str, max_chars: int = 6000) -> list[str]:
    pieces = []
    for file_text in split_files(diff_text):
        pieces.extend(split_file(file_text, max_chars))
    return pack(pieces, max_chars)