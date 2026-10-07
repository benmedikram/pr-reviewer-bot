import requests
from github import Github
from reviewer.github_auth import get_installation_token


def fetch_diff(installation_id: int, repo_full_name: str, pr_number: int) -> str:
    """Download the raw unified diff of a PR."""
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text


def post_review(installation_id: int, repo_full_name: str, pr_number: int,
                 findings: list[dict], dry_run: bool = False):
    """Post one GitHub review with one inline comment per finding.

    The review type is hard-coded to COMMENT: the bot leaves remarks but
    never approves or requests changes on its own.
    """
    if dry_run:
        for f in findings:
            print(f"[dry-run] {f['file']}:{f['line']} "
                  f"({f['severity']}, conf={f['confidence']:.2f}) {f['message']}")
        return None

    if not findings:
        return None

    token = get_installation_token(installation_id)
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    comments = [
        {
            "path": f["file"],
            "line": f["line"],
            "body": f"**{f['severity'].upper()}** (confidence {f['confidence']:.2f}): {f['message']}",
        }
        for f in findings
    ]

    return pr.create_review(
        body="Automated review by pr-reviewer-bot.",
        event="COMMENT",   # hard-coded on purpose — see docstring above
        comments=comments,
    )

def post_hello(installation_id: int, repo_full_name: str, pr_number: int):
    """Poste un commentaire simple pour confirmer que l'auth et la
    connexion GitHub fonctionnent — utile comme smoke test rapide."""
    token = get_installation_token(installation_id)
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment("Hello!")