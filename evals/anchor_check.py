# evals/anchor_check.py
# Shows, for each finding, the code on the line the bot anchored it to.
# Used to spot line-mapping problems (finding anchored on an unrelated line).
# Usage: python evals/anchor_check.py <labeled csv> <output txt>
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from reviewer.diff import HUNK_RE
from evals.run_baseline import fetch_public_diff


def added_line_texts(diff: str) -> dict:
    """Map (file, new-file line number) -> text of each added line."""
    texts, current = {}, None
    old_left = new_left = new_no = 0
    for line in diff.splitlines():
        if old_left > 0 or new_left > 0:  # inside a hunk
            if line.startswith("\\"):
                continue
            tag = line[:1]
            if tag == "+":
                texts[(current, new_no)] = line[1:]
                new_no += 1
                new_left -= 1
            elif tag == "-":
                old_left -= 1
            else:
                new_no += 1
                old_left -= 1
                new_left -= 1
            continue
        if line.startswith("+++ "):
            p = line[4:].strip()
            current = None if p == "/dev/null" else (p[2:] if p.startswith("b/") else p)
            continue
        m = HUNK_RE.match(line)
        if m:
            old_left = int(m.group(2) or 1)
            new_left = int(m.group(4) or 1)
            new_no = int(m.group(3))
    return texts


rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
out_path = Path(sys.argv[2])
cache = {}
lines = []
for r in rows:
    pr = int(r["pr"])
    if pr not in cache:
        cache[pr] = added_line_texts(fetch_public_diff("getsentry/sentry", pr))
    text = cache[pr].get((r["file"], int(r["line"])), "<line not found>")
    lines.append(f"#{r['id']} [{r['category']}] {r['file'].split('/')[-1]}:{r['line']}")
    lines.append(f"    code   : {text.strip()[:90]}")
    lines.append(f"    finding: {r['finding'][:90]}")
    lines.append("")
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"{len(rows)} findings -> {out_path}")