# app/github_auth.py
import time, jwt, os, requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("GH_APP_ID") or os.getenv("GITHUB_APP_ID")
PRIVATE_KEY_PATH = os.getenv("GH_PRIVATE_KEY_B64") or os.getenv("GITHUB_PRIVATE_KEY_PATH")

def generate_jwt():
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 500, "iss": APP_ID}
    return jwt.encode(payload, private_key, algorithm="RS256")

def get_installation_token(installation_id: int) -> str:
    jwt_token = generate_jwt()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    resp = requests.post(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["token"]

def get_installation_id_for_repo(repo_full_name: str) -> int:
    """Ask GitHub which installation of our App covers this repo."""
    jwt_token = generate_jwt()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/repos/{repo_full_name}/installation"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["id"]