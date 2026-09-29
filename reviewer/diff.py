import re

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_diff(diff_text: str) -> dict[str, set[int]]:
    """Map each changed file to the new-file line numbers of its added lines."""
    added: dict[str, set[int]] = {}
    current = None
    old_left = new_left = 0  # lines still expected in the current hunk
    new_no = 0

    for line in diff_text.splitlines():
        if old_left > 0 or new_left > 0:  # inside a hunk
            if line.startswith("\\"):  # "\ No newline at end of file"
                continue
            tag = line[:1]
            if tag == "+":
                if current is not None:
                    added[current].add(new_no)
                new_no += 1
                new_left -= 1
            elif tag == "-":
                old_left -= 1
            else:  # context line
                new_no += 1
                old_left -= 1
                new_left -= 1
            continue

        if line.startswith("+++ "):  # file header (only outside hunks)
            path = line[4:].strip()
            if path == "/dev/null":  # deleted file
                current = None
            else:
                current = path[2:] if path.startswith("b/") else path
                added.setdefault(current, set())
            continue

        match = HUNK_RE.match(line)
        if match:
            old_left = int(match.group(2) or 1)
            new_left = int(match.group(4) or 1)
            new_no = int(match.group(3))

    return added


def filter_findings(findings: list[dict], added: dict[str, set[int]]):
    """Split findings into (kept, dropped) by whether GitHub can accept them."""
    kept, dropped = [], []
    for finding in findings:
        if finding["line"] in added.get(finding["file"], set()):
            kept.append(finding)
        else:
            dropped.append(finding)
    return kept, dropped