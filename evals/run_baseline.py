import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from reviewer.diff import annotate_diff, parse_diff, filter_findings
from reviewer.llm import get_findings

PRS_PATH = Path(__file__).parent / "sentry_prs.json"
OUT_PATH = Path(__file__).parent / "results" / "raw_findings.json"

# Groq free tier caps each call at 8000 tokens/min (input+output combined).
# AGENTS.md alone costs ~800-1000 tokens, so keep the diff itself well under
# that ceiling; above this, split the diff into one chunk per file.
MAX_DIFF_CHARS = 16000  # ~4000 tokens, rough 4-chars-per-token estimate


def fetch_public_diff(repo: str, pr: int) -> str:
    url = f"https://github.com/{repo}/pull/{pr}.diff"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.text

def fetch_agents_md(repo: str) -> str:
    """Récupère le AGENTS.md du repo cible (le vrai playbook de ce projet),
    pas un fichier local — le bot doit suivre les règles du repo qu'il review."""
    url = f"https://raw.githubusercontent.com/{repo}/main/AGENTS.md"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.text

def split_diff_by_file(diff_text: str) -> list[str]:
    """Split a multi-file diff into one chunk per file, each a valid
    standalone diff starting with its own 'diff --git' line."""
    chunks = []
    current: list[str] = []
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("diff --git") and current:
            chunks.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("".join(current))
    return chunks

def pack_chunks(file_chunks: list[str], max_chars: int = 6000) -> list[str]:
    """Regroupe les chunks sous la limite, et TRONQUE tout chunk individuel
    qui dépasse déjà la limite à lui seul (fichier trop gros). La troncature
    coupe potentiellement un hunk en plein milieu — les lignes manquantes ne
    seront simplement pas analysées sur ce fichier, limitation acceptable
    pour une baseline."""
    packed, current = [], ""
    for chunk in file_chunks:
        if len(chunk) > max_chars:
            if current:
                packed.append(current)
                current = ""
            packed.append(chunk[:max_chars])
            continue
        if current and len(current) + len(chunk) > max_chars:
            packed.append(current)
            current = chunk
        else:
            current += chunk
    if current:
        packed.append(current)
    return packed



def review_chunk(repo: str, pr: int, agents_md: str, diff_chunk: str) -> tuple[list, list]:
    annotated = annotate_diff(diff_chunk)
    findings = get_findings(agents_md, annotated, repo=repo, pr=pr)
    added_lines = parse_diff(diff_chunk)
    return filter_findings(findings, added_lines)


def run_on_pr(repo: str, pr: int, agents_md: str) -> dict:
    diff = fetch_public_diff(repo, pr)

    if len(diff) <= MAX_DIFF_CHARS:
        kept, dropped = review_chunk(repo, pr, agents_md, diff)
        return {"repo": repo, "pr": pr, "kept": kept, "dropped": dropped, "split": False}

    file_chunks = split_diff_by_file(diff)
    packed = pack_chunks(file_chunks)
    print(f"  diff is {len(diff)} chars, {len(file_chunks)} files -> {len(packed)} packed call(s)")

    all_kept, all_dropped = [], []
    for i, chunk in enumerate(packed):
        if not chunk.strip():
            continue
        print(f"  reviewing packed chunk {i + 1}/{len(packed)} ({len(chunk)} chars)...")
        kept, dropped = review_chunk(repo, pr, agents_md, chunk)
        all_kept.extend(kept)
        all_dropped.extend(dropped)
        time.sleep(3)

    return {"repo": repo, "pr": pr, "kept": all_kept, "dropped": all_dropped, "split": True}


def main():
    prs = json.loads(PRS_PATH.read_text(encoding="utf-8"))
    # Toutes les PRs testées ici sont sur getsentry/sentry, donc même repo
    # pour toutes — si vous testez un jour un mélange de repos, il faudrait
    # récupérer le AGENTS.md par PR plutôt qu'une seule fois ici.
    agents_md = fetch_agents_md("benmedikram/click")
    print(f"Using playbook from benmedikram/click ({len(agents_md)} chars)")
    results = []
    for entry in prs:
        repo, pr = entry["repo"], entry["pr"]
        print(f"Running on {repo}#{pr} ({entry['pr_title']})...")
        try:
            result = run_on_pr(repo, pr, agents_md)
            result["pr_title"] = entry["pr_title"]
            results.append(result)
            print(f"  -> {len(result['kept'])} findings kept, {len(result['dropped'])} dropped")
        except Exception as e:
            print(f"  -> FAILED: {e}")
            results.append({"repo": repo, "pr": pr, "pr_title": entry["pr_title"], "error": str(e)})
        time.sleep(3)

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()