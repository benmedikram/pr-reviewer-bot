# evals/seen_detail.py
# For each reference issue of the two truncated PRs: where does each named identifier
# sit, and was that position inside the first 6000 characters kept for its file?
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.run_baseline import fetch_public_diff, split_diff_by_file

LIMIT = 6000
ID_RE = re.compile(r"\b(?:[a-z]+_[a-z0-9_]+|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b")
PRS = {e["pr"]: e for e in json.loads((Path(__file__).parent / "sentry_prs.json").read_text(encoding="utf-8"))}

for pr in (95633, 80168):
    e = PRS[pr]
    chunks = split_diff_by_file(fetch_public_diff(e["repo"], pr))
    print(f"\nPR {pr}")
    for i, c in enumerate(e["comments"], 1):
        for ident in sorted(set(ID_RE.findall(c["comment"]))):
            for ch in chunks:
                pos = ch.find(ident)
                if pos >= 0:
                    name = ch.splitlines()[0].split(" b/")[-1]
                    status = "seen" if (len(ch) <= LIMIT or pos < LIMIT) else "NOT SEEN (cut)"
                    print(f"  {pr}-R{i} {ident}: {name} @ {pos}/{len(ch)} -> {status}")