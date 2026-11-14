# evals/make_scoring_sheet.py
# Usage: python evals/make_scoring_sheet.py evals/results/raw_findings.json exp0_click_playbook
import csv
import json
import sys
from pathlib import Path

EVALS = Path(__file__).parent
raw_path, name = Path(sys.argv[1]), sys.argv[2]
OUT = EVALS / "scoring"
OUT.mkdir(exist_ok=True)

scored = {e["pr"]: e for e in json.loads((EVALS / "sentry_prs.json").read_text(encoding="utf-8"))}
raw = json.loads(raw_path.read_text(encoding="utf-8"))


def tag(msg: str) -> str:
    m = msg.lower()
    if "changes.md" in m:
        return "changelog"
    if "compatib" in m or "signature" in m or "callers" in m:
        return "signature-compat"
    if "documentation" in m or "docs/" in m:
        return "docs"
    if "type hint" in m:
        return "type-hint"
    if "bare except" in m or "broad exception" in m:
        return "bare-except"
    if "secret" in m:
        return "secret"
    if "syntax error" in m:
        return "syntax-error"
    return "other"


rows = []
for r in raw:
    if r.get("pr") not in scored:
        continue
    for f in r.get("kept", []):
        rows.append({
            "id": len(rows) + 1, "pr": r["pr"], "file": f["file"], "line": f["line"],
            "severity": f["severity"], "confidence": f["confidence"],
            "category": tag(f["message"]), "finding": f["message"],
            "match": "", "reference_id": "", "verdict": "", "justification": "",
        })

with (OUT / f"{name}.csv").open("w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

with (OUT / f"{name}_review_pack.md").open("w", encoding="utf-8") as fh:
    for pr, e in scored.items():
        fh.write(f"## PR {pr}: {e['pr_title']}\n\n### Reference issues\n")
        for i, c in enumerate(e["comments"], 1):
            fh.write(f"- **{pr}-R{i}** [{c['severity']} / {c['category']}] {c['comment']}\n")
        fh.write("\n### Bot findings\n")
        for row in (x for x in rows if x["pr"] == pr):
            fh.write(f"- **#{row['id']}** `{row['file']}:{row['line']}` [{row['category']}] {row['finding']}\n")
        fh.write("\n")

print(f"{len(rows)} findings across {len(scored)} scored PRs -> {OUT}")