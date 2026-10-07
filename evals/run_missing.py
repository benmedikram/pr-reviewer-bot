# evals/run_missing.py
#
# Retry helper for evals/run_baseline.py: automatically finds PRs that
# failed in raw_findings.json (missing-quota errors, rate limits, etc.)
# and retries only those, with incremental saving so a second failure
# doesn't lose progress already made.
#
# Usage: python evals/run_missing.py
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.run_baseline import run_on_pr, fetch_agents_md

RAW_PATH = Path(__file__).parent / "results" / "raw_findings.json"


def find_failed_prs(raw_results: list[dict]) -> list[dict]:
    """Repère les entrées en échec (celles qui ont 'error' au lieu de
    'kept') dans raw_findings.json et renvoie leurs infos repo/pr/titre."""
    return [r for r in raw_results if "error" in r]


def main():
    if not RAW_PATH.exists():
        print(f"{RAW_PATH} introuvable — lancez d'abord evals/run_baseline.py")
        return

    raw_results = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    failed = find_failed_prs(raw_results)

    if not failed:
        print("Aucune PR en échec trouvée dans raw_findings.json — rien à refaire.")
        return

    print(f"{len(failed)} PR(s) en échec détectée(s) : "
          f"{[f['pr'] for f in failed]}")

    agents_md = fetch_agents_md("benmedikram/click")

    for entry in failed:
        repo, pr = entry["repo"], entry["pr"]
        print(f"--- Retrying {repo}#{pr} ({entry.get('pr_title', '')}) ---")
        try:
            result = run_on_pr(repo, pr, agents_md)
            result["pr_title"] = entry.get("pr_title", "")
        except Exception as e:
            print(f"  -> toujours en échec: {e}")
            result = {"repo": repo, "pr": pr, "pr_title": entry.get("pr_title", ""), "error": str(e)}

        # Remplace l'entrée en échec par le nouveau résultat, directement
        # dans raw_findings.json — plus besoin de fichier séparé à fusionner
        for i, r in enumerate(raw_results):
            if r.get("pr") == pr and r.get("repo") == repo:
                raw_results[i] = result
                break

        RAW_PATH.write_text(json.dumps(raw_results, indent=2), encoding="utf-8")
        print(f"  -> saved to {RAW_PATH}")
        time.sleep(5)

    still_failed = find_failed_prs(raw_results)
    if still_failed:
        print(f"\n{len(still_failed)} PR(s) toujours en échec: "
              f"{[f['pr'] for f in still_failed]} — relancez le script.")
    else:
        print("\nToutes les PRs ont maintenant un résultat valide.")


if __name__ == "__main__":
    main()