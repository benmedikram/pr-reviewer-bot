# evals/score.py  Usage: python evals/score.py evals/scoring/exp0_click_playbook.csv
import csv
import json
import sys
from collections import Counter
from pathlib import Path

EVALS = Path(__file__).parent
rows = list(csv.DictReader(Path(sys.argv[1]).open(encoding="utf-8-sig")))
scored = json.loads((EVALS / "sentry_prs.json").read_text(encoding="utf-8"))
total_refs = sum(len(e["comments"]) for e in scored)
n = len(rows)

for label, levels in (("strict", {"strict"}), ("lenient (strict + ambiguous)", {"strict", "ambiguous"})):
    matched = [r for r in rows if r["match"].strip().lower() in levels]
    refs = {r["reference_id"].strip() for r in matched if r["reference_id"].strip()}
    print(f"{label}: precision {len(matched)}/{n} = {len(matched)/n:.1%}, "
          f"recall {len(refs)}/{total_refs} = {len(refs)/total_refs:.1%}")

print("\nManual verdicts:")
for k, v in Counter(r["verdict"].strip().lower() or "(empty)" for r in rows).most_common():
    print(f"  {k}: {v}")

print("\nCategory x verdict:")
for (c, v), k in sorted(Counter((r["category"], r["verdict"].strip().lower() or "(empty)") for r in rows).items()):
    print(f"  {c} / {v}: {k}")