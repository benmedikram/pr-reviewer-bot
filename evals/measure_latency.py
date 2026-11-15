# evals/measure_latency.py
# Usage: python evals/measure_latency.py <pr number>
# For each "AI PR Review" run on the PR: trigger -> review posted, run duration,
# conclusion, and number of inline comments. Reads the public GitHub API.
import sys
from datetime import datetime

import requests

REPO = "benmedikram/click"
H = {"User-Agent": "latency-check", "Accept": "application/vnd.github+json"}


def get(path, **params):
    r = requests.get(f"https://api.github.com/repos/{REPO}/{path}",
                     headers=H, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


pr = int(sys.argv[1])
reviews = get(f"pulls/{pr}/reviews", per_page=100)
runs = get("actions/runs", event="pull_request", per_page=50)["workflow_runs"]
shas = {rv["commit_id"] for rv in reviews}
runs = [r for r in runs if r["name"] == "AI PR Review" and r["head_sha"] in shas]
for run in sorted(runs, key=lambda r: r["created_at"]):
    rv = next(x for x in reviews if x["commit_id"] == run["head_sha"])
    n = len(get(f"pulls/{pr}/reviews/{rv['id']}/comments", per_page=100))
    lat = (t(rv["submitted_at"]) - t(run["created_at"])).total_seconds()
    dur = (t(run["updated_at"]) - t(run["run_started_at"])).total_seconds()
    print(f"run {run['id']} {run['event']} {run['conclusion']}: "
          f"trigger->review {lat:.0f}s, run duration {dur:.0f}s, "
          f"{n} inline comments, review state {rv['state']}")
    print(f"   {run['html_url']}")