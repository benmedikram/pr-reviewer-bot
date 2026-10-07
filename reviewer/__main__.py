import argparse
import requests

from reviewer.github_auth import get_installation_id_for_repo, get_installation_token
from reviewer.diff import parse_diff, filter_findings, annotate_diff
from reviewer.llm import get_findings
from reviewer.poster import fetch_diff, post_review, post_hello


def load_agents_md(installation_id: int, repo_full_name: str) -> str:
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full_name}/contents/AGENTS.md"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.raw"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text

def run_hello(repo: str, pr: int):
    installation_id = get_installation_id_for_repo(repo)
    post_hello(installation_id, repo, pr)
    print(f"Posted hello on {repo}#{pr}")

def run_review(repo: str, pr: int, dry_run: bool):
    installation_id = get_installation_id_for_repo(repo)
    diff = fetch_diff(installation_id, repo, pr)
    agents_md = load_agents_md(installation_id, repo)

    annotated = annotate_diff(diff)
    findings = get_findings(agents_md, annotated, repo=repo, pr=pr)
    added_lines = parse_diff(diff)
    kept, dropped = filter_findings(findings, added_lines)

    if dropped:
        print(f"Dropped {len(dropped)} finding(s) outside the diff.")

    post_review(installation_id, repo, pr, kept, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(prog="reviewer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser("review")
    review.add_argument("--repo", required=True, help="owner/name, e.g. you/sandbox")
    review.add_argument("--pr", required=True, type=int)
    review.add_argument("--dry-run", action="store_true")

    hello = subparsers.add_parser("hello")
    hello.add_argument("--repo", required=True)
    hello.add_argument("--pr", required=True, type=int)    

    args = parser.parse_args()
    if args.command == "review":
        run_review(args.repo, args.pr, args.dry_run)
    elif args.command == "hello":
        run_hello(args.repo, args.pr)


if __name__ == "__main__":
    main()