# evals/check_labels.py
# Heuristic sanity check: do identifiers named in the reference comments
# actually appear in the PR's diff? Zero hits on every comment of a PR
# suggests mislabeled reference data. Not proof; confirm by hand.
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.run_baseline import fetch_public_diff

PRS = json.loads((Path(__file__).parent / "sentry_prs.json").read_text(encoding="utf-8"))
ID_RE = re.compile(r"\b(?:[a-z]+_[a-z0-9_]+|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b")

for entry in PRS:
    diff = fetch_public_diff(entry["repo"], entry["pr"])
    print(f"\nPR {entry['pr']}: {entry['pr_title']}")
    total_hits = 0
    for c in entry["comments"]:
        ids = set(ID_RE.findall(c["comment"]))
        found = {i for i in ids if i in diff}
        total_hits += len(found)
        label = f"{len(found)}/{len(ids)} identifiers in diff" if ids else "no identifiers (check by hand)"
        print(f"  - {label} | {c['comment'][:70]}...")
    print(f"  => PR total hits: {total_hits}")