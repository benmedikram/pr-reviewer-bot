# evals/run_missing.py — relance ponctuelle des PRs qui ont échoué par quota
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.run_baseline import run_on_pr, fetch_agents_md

MISSING_PRS = [93824, 77754, 80528, 95633, 80168]
OUT_PATH = Path(__file__).parent / "results" / "missing_findings.json"


def main():
    agents_md = fetch_agents_md("benmedikram/click")
    results = []
    if OUT_PATH.exists():
        results = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    done_prs = {r["pr"] for r in results if "pr" in r}

    for pr in MISSING_PRS:
        if pr in done_prs:
            print(f"--- getsentry/sentry#{pr} already done, skipping ---")
            continue
        print(f"--- getsentry/sentry#{pr} ---")
        result = run_on_pr("getsentry/sentry", pr, agents_md)
        results.append(result)
        OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")  # sauvegarde immédiate
        time.sleep(5)

    print(f"Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()