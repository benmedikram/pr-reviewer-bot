# evals/build_pr_set.py
# Builds the scored PR set from the official Martian sentry.json, so the
# data is never hand-copied. Usage:
#   python evals/build_pr_set.py <path to sentry.json>
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(__file__).parent / "sentry_prs.json"
EXCLUDED_OUT = Path(__file__).parent / "excluded_prs.json"
EXCLUDED_PRS = {92393: "Reference comments describe OptimizedCursorPaginator, absent from the PR diff (see EXCLUSIONS.md)"}

kept, excluded = [], []
for e in json.loads(SRC.read_text(encoding="utf-8")):
    url = e.get("original_url") or e["url"]
    m = re.fullmatch(r"https://github\.com/getsentry/sentry/pull/(\d+)", url)
    if not m:
        excluded.append({"pr_title": e["pr_title"], "url": e["url"],
                         "reason": e.get("az_comment", "no real PR"), "comments": e["comments"]})
        continue
    pr = int(m.group(1))
    item = {"pr_title": e["pr_title"], "repo": "getsentry/sentry", "pr": pr, "comments": e["comments"]}
    if pr in EXCLUDED_PRS:
        item["reason"] = EXCLUDED_PRS[pr]
        excluded.append(item)
    else:
        kept.append(item)

OUT.write_text(json.dumps(kept, indent=2, ensure_ascii=False), encoding="utf-8")
EXCLUDED_OUT.write_text(json.dumps(excluded, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Scored: {len(kept)} PRs, {sum(len(k['comments']) for k in kept)} reference issues")
print(f"Excluded: {len(excluded)} entries")