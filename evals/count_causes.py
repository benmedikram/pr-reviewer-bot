# evals/count_causes.py
# Prints the two cause tables (findings, missed reference issues) in Markdown.
import collections
import csv
from pathlib import Path

S = Path(__file__).parent / "scoring"
FINDINGS = ["irrelevant-rule", "noise", "incorrect-reasoning", "insufficient-context",
            "chunking-artifact", "line-mapping"]
MISSED = ["not-seen", "needs-surrounding-code", "no-rule-for-it", "seen-but-missed"]


def table(path, col, order):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    c = collections.Counter(r[col].strip() for r in rows)
    n = len(rows)
    out = [f"{n} rows", "| Cause | Count | Share |", "|---|---|---|"]
    out += [f"| {k} | {c.get(k, 0)} | {c.get(k, 0) / n:.0%} |" for k in order]
    unknown = {k: v for k, v in c.items() if k not in order}
    if unknown:
        out.append(f"WARNING, unexpected values: {unknown}")
    return "\n".join(out)


text = ("Findings\n" + table(S / "exp0_click_playbook.csv", "failure_cause", FINDINGS)
        + "\n\nMissed reference issues\n" + table(S / "exp0_missed.csv", "cause", MISSED))
(S / "cause_tables.md").write_text(text, encoding="utf-8")
print(text)