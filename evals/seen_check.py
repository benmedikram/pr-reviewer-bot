# evals/seen_check.py
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.run_baseline import fetch_public_diff, split_diff_by_file, pack_chunks

ID_RE = re.compile(r"\b(?:[a-z]+_[a-z0-9_]+|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b")
PRS = {e["pr"]: e for e in json.loads(
    (Path(__file__).parent / "sentry_prs.json").read_text(encoding="utf-8"))}

lines = []
for pr in (95633, 80168):
    e = PRS[pr]
    diff = fetch_public_diff(e["repo"], pr)
    seen = "".join(pack_chunks(split_diff_by_file(diff), max_chars=6000))
    lines.append(f"PR {pr}: diff {len(diff)} chars, reviewed {len(seen)} ({len(seen)/len(diff):.0%})")
    for i, c in enumerate(e["comments"], 1):
        ids = set(ID_RE.findall(c["comment"]))
        lines.append(f"  {pr}-R{i}: in diff {sum(x in diff for x in ids)}/{len(ids)}, "
                     f"in reviewed part {sum(x in seen for x in ids)}/{len(ids)} | {c['comment'][:60]}")
    lines.append("")
out = Path(__file__).parent / "scoring" / "seen_check.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"saved to {out}")