# pr-reviewer-bot

An automated GitHub PR reviewer powered by an LLM, guided by a team-specific playbook (`AGENTS.md`) instead of generic prompting. The bot reads a pull request's diff, applies the target repo's own review rules, and posts a single structured review — it never approves a PR or auto-merges anything.

## How it works

```
PR opens → fetch diff → fetch target repo's AGENTS.md → send to LLM → parse JSON findings → filter out anything outside the diff → post one GitHub review (type: COMMENT)
```

The bot is installed as a GitHub App on the **target repository** (the repo being reviewed) and reads that repo's `AGENTS.md` file — the playbook lives with the project it applies to, not with the bot itself.

## Project structure

```
reviewer/
├── __main__.py       # CLI entry point: python -m reviewer review ...
├── github_auth.py     # GitHub App JWT + installation token auth
├── diff.py            # Diff parsing: maps added lines to commentable line numbers
├── llm.py             # Model call (Groq) + Langfuse tracing
├── poster.py           # Fetches PR diff, posts the review
evals/
├── sentry_prs.json    # Benchmark PRs used for the Week 1 baseline
├── run_baseline.py    # Runs the bot (no posting) on benchmark PRs
└── RESULTS.md          # Baseline precision/recall results
tests/
├── test_diff.py
└── test_poster.py
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/benmedikram/pr-reviewer-bot.git
cd pr-reviewer-bot
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Create a GitHub App

1. Go to **GitHub Settings → Developer settings → GitHub Apps → New GitHub App**
2. Permissions: **Pull requests** (Read & write), **Contents** (Read-only)
3. Subscribe to the **Pull request** event
4. Generate and download a private key (`.pem`)
5. Note the **App ID**
6. Install the App on the repository you want it to review

### 3. Get a free Groq API key

Create a key at [console.groq.com](https://console.groq.com) (no credit card required for the free tier).

### 4. Set up Langfuse (optional, for tracing cost/tokens)

Create a free account at [cloud.langfuse.com](https://cloud.langfuse.com) and generate a public/secret API key pair.

### 5. Create your `.env` file

```env
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=any-random-string
GROQ_API_KEY=gsk_...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

`.env` and `*.pem` are git-ignored — never commit them.

## Usage

### Review a PR (dry run — prints findings, posts nothing)

```bash
python -m reviewer review --repo owner/repo --pr 42 --dry-run
```

### Review a PR for real (posts a review on GitHub)

```bash
python -m reviewer review --repo owner/repo --pr 42
```

### Smoke test — confirm the bot is connected

```bash
python -m reviewer hello --repo owner/repo --pr 1
```

Posts a simple "Hello!" comment to confirm authentication and connectivity are working, without needing a full review.

### Run the tests

```bash
python -m pytest tests/ -q
```

## Running automatically via GitHub Actions

Add a workflow (see `.github/workflows/review.yml` in the target repo, e.g. our sandbox at [benmedikram/click](https://github.com/benmedikram/click)) that checks out this repo and runs the CLI on `pull_request` events — **never** on `pull_request_target`, to avoid leaking secrets to PRs from forks. The target repo needs these secrets configured:

| Secret | Value |
|---|---|
| `GH_APP_ID` | Your GitHub App ID |
| `GH_PRIVATE_KEY_B64` | Your private key, base64-encoded |
| `GROQ_API_KEY` | Your Groq API key |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | Your Langfuse credentials |

## The target repo needs its own `AGENTS.md`

The bot fetches `AGENTS.md` from the root of the **repo being reviewed**, not from this repo. See [benmedikram/click/AGENTS.md](https://github.com/benmedikram/click/blob/main/AGENTS.md) for an example playbook with 27 rules (Always / Never / Ask), each traced to a real source (the project's own conventions or Google's code review guide).

## Baseline evaluation

`evals/run_baseline.py` runs the bot (without posting) against a fixed set of real PRs with known human-reviewer findings ("golden comments"), to measure precision and recall. Results are recorded in `evals/RESULTS.md`.

```bash
python evals/run_baseline.py
```

## License

MIT