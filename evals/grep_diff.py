# evals/grep_diff.py
# Usage: python evals/grep_diff.py <pr> "<term>" [context_lines]
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.run_baseline import fetch_public_diff

pr, term = int(sys.argv[1]), sys.argv[2]
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
lines = fetch_public_diff("getsentry/sentry", pr).splitlines()

file_of, current = [], ""
for line in lines:
    if line.startswith("diff --git"):
        current = line.split(" b/")[-1]
    file_of.append(current)

for i, line in enumerate(lines):
    if term in line and line[:1] in "+- ":
        print(f"--- {file_of[i]} (diff line {i + 1}) ---")
        for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
            print(lines[j])
        print()