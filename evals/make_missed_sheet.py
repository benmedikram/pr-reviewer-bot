# evals/make_missed_sheet.py
# Usage: python evals/make_missed_sheet.py <labeled csv> <output csv>
import csv
import json
import sys
from pathlib import Path

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
matched = {r["reference_id"].strip() for r in rows
           if r["match"].strip() == "strict" and r["reference_id"].strip()}
prs = json.loads((Path(__file__).parent / "sentry_prs.json").read_text(encoding="utf-8"))
with open(sys.argv[2], "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["reference_id", "pr", "severity", "category", "comment",
                "found_by_bot", "visible_to_model", "cause", "note"])
    for e in prs:
        for i, c in enumerate(e["comments"], 1):
            rid = f"{e['pr']}-R{i}"
            w.writerow([rid, e["pr"], c["severity"], c["category"], c["comment"],
                        "yes" if rid in matched else "no", "", "", ""])
print("saved", sys.argv[2])