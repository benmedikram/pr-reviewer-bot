import hmac, hashlib, os, json
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from app.github_auth import get_installation_token
from github import Github

load_dotenv()
app = FastAPI()
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET").encode()

def verify_signature(payload_body: bytes, signature_header: str):
    if not signature_header:
        raise HTTPException(status_code=403, detail="Signature manquante")
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET, payload_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=403, detail="Signature invalide")

def post_comment(installation_id, repo_full_name, pr_number, message):
    token = get_installation_token(installation_id)
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(message)

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    verify_signature(body, request.headers.get("X-Hub-Signature-256"))
    payload = json.loads(body)

    event = request.headers.get("X-GitHub-Event")
    print(f"Event reçu: {event}")

    if event == "pull_request" and payload["action"] == "opened":
        installation_id = payload["installation"]["id"]
        repo_full_name = payload["repository"]["full_name"]
        pr_number = payload["pull_request"]["number"]
        print(f"Nouvelle PR #{pr_number} sur {repo_full_name}")
        post_comment(installation_id, repo_full_name, pr_number, "Bot en ligne 👋")

    return {"status": "ok"}