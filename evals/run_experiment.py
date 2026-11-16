# evals/run_experiment.py
# Usage: python evals/run_experiment.py --condition generic|click|sentry --label exp1_generic_run1
#        [--only 77754,80168]
# Writes evals/results/<label>.json (same shape as raw_findings.json, so
# make_scoring_sheet.py works unchanged) and evals/runs/<label>.json (run record).
# Re-running with the same label skips PRs that already succeeded.
import argparse
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from reviewer import llm
from reviewer.chunking import chunk_diff
from reviewer.diff import annotate_diff, filter_findings, parse_diff
from evals.run_baseline import fetch_public_diff

EVALS = Path(__file__).parent
PLAYBOOKS = {
    "generic": None,
    "click": EVALS / "playbooks" / "click_AGENTS.md",
    "sentry": EVALS / "playbooks" / "sentry_AGENTS.md",
}
MAX_CHARS = 6000
PAUSE = 30  # seconds between calls: Groq free tier allows 8000 tokens per minute


def git(*args):
    return subprocess.check_output(["git", *args], text=True, cwd=EVALS.parent).strip()


def run_pr(entry, playbook, label, pause):
    repo, pr = entry["repo"], entry["pr"]
    diff = fetch_public_diff(repo, pr)
    added = parse_diff(diff)
    chunks = chunk_diff(diff, MAX_CHARS)
    kept, dropped = [], []
    for i, chunk in enumerate(chunks, 1):
        print(f"  call {i}/{len(chunks)} ({len(chunk)} chars)")
        findings = llm.get_findings(playbook, annotate_diff(chunk), repo=repo, pr=pr, label=label)
        k, d = filter_findings(findings, added)
        kept += k
        dropped += d
        time.sleep(pause)
    return {"repo": repo, "pr": pr, "pr_title": entry["pr_title"], "kept": kept,
            "dropped": dropped, "calls": len(chunks), "chunk_sizes": [len(c) for c in chunks],
            "diff_chars": len(diff), "diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=list(PLAYBOOKS))
    ap.add_argument("--label", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--pause", type=int, default=PAUSE, help="seconds between model calls")
    args = ap.parse_args()

    path = PLAYBOOKS[args.condition]
    playbook_bytes = path.read_bytes() if path else None
    playbook = playbook_bytes.decode("utf-8") if path else None
    template = llm.GENERIC_TEMPLATE if playbook is None else llm.PLAYBOOK_TEMPLATE

    entries = json.loads((EVALS / "sentry_prs.json").read_text(encoding="utf-8"))
    if args.only:
        wanted = {int(x) for x in args.only.split(",")}
        entries = [e for e in entries if e["pr"] in wanted]

    out_path = EVALS / "results" / f"{args.label}.json"
    meta_path = EVALS / "runs" / f"{args.label}.json"
    out_path.parent.mkdir(exist_ok=True)
    meta_path.parent.mkdir(exist_ok=True)
    results = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else []
    done = {r["pr"] for r in results if "error" not in r}
    previous = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    usage = Counter(previous.get("usage", {}))
    llm.USAGE.clear()

    try:
        for entry in entries:
            if entry["pr"] in done:
                print(f"PR {entry['pr']} already done, skipping")
                continue
            print(f"PR {entry['pr']}: {entry['pr_title']}")
            try:
                res = run_pr(entry, playbook, args.label, args.pause)
            except Exception as e:
                print(f"  FAILED: {e}")
                res = {"repo": entry["repo"], "pr": entry["pr"], "pr_title": entry["pr_title"], "error": str(e)}
                results = [r for r in results if r.get("pr") != entry["pr"]] + [res]
                out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
                if "tokens per day" in str(e):
                    print("Daily token quota used: stop here and run the same command tomorrow.")
                    break
                continue
            results = [r for r in results if r.get("pr") != entry["pr"]] + [res]
            out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    finally:
        usage.update(llm.USAGE)
        cost = (usage["input_tokens"] / 1e6 * llm.PRICE_PER_MILLION_INPUT
                + usage["output_tokens"] / 1e6 * llm.PRICE_PER_MILLION_OUTPUT)
        meta = {
            "label": args.label, "condition": args.condition,
            "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": llm.MODEL_NAME, "temperature": llm.TEMPERATURE,
            "prompt_version": llm.GENERIC_VERSION if playbook is None else llm.PLAYBOOK_VERSION,
            "prompt_template_sha256": hashlib.sha256(template.encode("utf-8")).hexdigest(),
            "playbook_file": str(path.relative_to(EVALS.parent)) if path else None,
            "playbook_sha256": hashlib.sha256(playbook_bytes).hexdigest() if path else None,
            "max_chars": MAX_CHARS, "pause_s": args.pause,
            "bot_commit": git("rev-parse", "--short", "HEAD"),
            "code_uncommitted_changes": bool(git("status", "--porcelain", "--", "reviewer",
                                                 "evals/run_experiment.py", "evals/run_baseline.py",
                                                 "evals/playbooks")),
            "usage": dict(usage), "cost_usd": round(cost, 6),
            "pricing": "$0.15 / $0.60 per million input / output tokens, no caching discount",
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"\nResults: {out_path}\nRun record: {meta_path}\nTokens: {dict(usage)}  cost: ${cost:.4f}")


if __name__ == "__main__":
    main()