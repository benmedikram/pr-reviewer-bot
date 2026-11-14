# evals/where_seen.py
# Usage: python evals/where_seen.py <pr> "<term>"
# For each file of the diff that contains <term>: size, whether it was truncated
# in experiment 0 (6000-character limit) and how many hits were in the seen part.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.run_baseline import fetch_public_diff, split_diff_by_file

pr, term = int(sys.argv[1]), sys.argv[2]
LIMIT = 6000
for c in split_diff_by_file(fetch_public_diff("getsentry/sentry", pr)):
    name = c.splitlines()[0].split(" b/")[-1]
    pos = [m.start() for m in re.finditer(re.escape(term), c)]
    if pos:
        truncated = len(c) > LIMIT
        seen = [p for p in pos if p < LIMIT] if truncated else pos
        print(f"{name}: {len(c)} chars{' (truncated)' if truncated else ''}; "
              f"{len(pos)} hits, {len(seen)} seen; positions {pos}")