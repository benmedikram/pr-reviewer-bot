import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT_TEMPLATE = """You are an automated code reviewer. Follow this team's \
playbook exactly. Only report what the playbook tells you to report.

The diff below has each line prefixed with its exact line number in the new
file. When reporting a finding, COPY the number shown at the start of that
line — do not count or calculate it yourself.

Respond with a JSON object: {{"findings": [...]}}. Each item has:
- file (string)
- line (integer — copied exactly from the line number prefix)
- severity (one of: "low", "medium", "high")
- message (string)
- confidence (a NUMBER between 0.0 and 1.0)

Return {{"findings": []}} if there is nothing to report.

# Playbook (AGENTS.md)
{agents_md}

# Pull request diff (numbered)
{diff}
"""


def get_findings(agents_md: str, diff: str, retries: int = 3, delay: int = 5) -> list[dict]:
    prompt = PROMPT_TEMPLATE.format(agents_md=agents_md, diff=diff)

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            findings = data.get("findings", [])
            for f in findings:
                f["confidence"] = _coerce_confidence(f.get("confidence"))
            return findings
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"Model call failed ({e}), retrying in {delay}s...")
            time.sleep(delay)
    return []


def _coerce_confidence(value) -> float:
    """Some models return words instead of numbers; normalize defensively."""
    if isinstance(value, (int, float)):
        return float(value)
    mapping = {"low": 0.4, "medium": 0.65, "high": 0.85}
    return mapping.get(str(value).lower(), 0.5)