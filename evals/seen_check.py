# evals/seen_check.py
# Which reference issues name code that the model saw in experiment 0?
# Uses the experiment 0 chunking (pack_chunks truncating at 6000 chars).
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.run_baseline import fetch_public_diff, split_diff_by_file, pack_chunks

ID_RE = re.compile(r"\b(?:[a-z]+_[a-z0-9_]+|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b")
PRS = {e["pr"]: e for e in json.loads(
    (Path(__file__).parent / "sentry_prs.json").read_text(encoding="utf-8"))}

for pr in (95633, 80168):
    e = PRS[pr]
    diff = fetch_public_diff(e["repo"], pr)
    seen = "".join(pack_chunks(split_diff_by_file(diff), max_chars=6000))
    print(f"\nPR {pr}: diff {len(diff)} chars, reviewed {len(seen)} ({len(seen)/len(diff):.0%})")
    for i, c in enumerate(e["comments"], 1):
        ids = set(ID_RE.findall(c["comment"]))
        print(f"  {pr}-R{i}: in diff {sum(x in diff for x in ids)}/{len(ids)}, "
              f"in reviewed part {sum(x in seen for x in ids)}/{len(ids)} | {c['comment'][:60]}")