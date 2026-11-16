# reviewer/llm.py
import json
import os
import time
from collections import Counter

from dotenv import load_dotenv
from groq import Groq
from langfuse import get_client

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
langfuse = get_client()

MODEL_NAME = "openai/gpt-oss-120b"
TEMPERATURE = 0
# Groq prices for openai/gpt-oss-120b, dollars per million tokens (no caching discount).
PRICE_PER_MILLION_INPUT = 0.15
PRICE_PER_MILLION_OUTPUT = 0.60

# Token and call counters, for the experiment runner. Reset by the caller.
USAGE = Counter()

_LINE_NUMBERS = """The diff below has each line prefixed with its exact line number in the new
file. When reporting a finding, COPY the number shown at the start of that
line. Do not count or calculate it yourself.

Respond with a JSON object: {{"findings": [...]}}. Each item has:
- file (string)
- line (integer, copied exactly from the line number prefix)
- severity (one of: "low", "medium", "high")
- message (string)
- confidence (a NUMBER between 0.0 and 1.0)
Return {{"findings": []}} if there is nothing to report. Returning no findings
is a good answer when you cannot support a useful comment.

"""

PLAYBOOK_VERSION = "playbook-v2"
PLAYBOOK_TEMPLATE = (
    "You are an automated code reviewer. Follow this team's playbook exactly. "
    "Only report what the playbook tells you to report.\n\n"
    + _LINE_NUMBERS
    + "# Playbook (AGENTS.md)\n{agents_md}\n\n# Pull request diff (numbered)\n{diff}\n"
)
PROMPT_TEMPLATE = PLAYBOOK_TEMPLATE  # old name

GENERIC_VERSION = "generic-v1"
GENERIC_TEMPLATE = (
    "You are a code reviewer. Review the pull request diff below and report only "
    "real, actionable problems that you can support from the code shown: bugs, "
    "security issues, or missing tests.\n\n"
    + _LINE_NUMBERS
    + "# Pull request diff (numbered)\n{diff}\n"
)


def _coerce_confidence(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    mapping = {"low": 0.4, "medium": 0.65, "high": 0.85}
    return mapping.get(str(value).lower(), 0.5)


def _clean(findings) -> list[dict]:
    """Keep only well-formed findings, so one bad item cannot crash a run."""
    out = []
    for f in findings if isinstance(findings, list) else []:
        if not isinstance(f, dict):
            continue
        try:
            f["file"], f["line"], f["message"] = str(f["file"]), int(f["line"]), str(f["message"])
        except (KeyError, TypeError, ValueError):
            continue
        if f.get("severity") not in ("low", "medium", "high"):
            f["severity"] = "low"
        f["confidence"] = _coerce_confidence(f.get("confidence"))
        out.append(f)
    return out


def get_findings(agents_md, diff: str, repo: str = "", pr: int = 0,
                 retries: int = 4, delay: int = 10, label: str = "") -> list[dict]:
    """agents_md=None selects the generic prompt (no playbook)."""
    if agents_md is None:
        prompt, version = GENERIC_TEMPLATE.format(diff=diff), GENERIC_VERSION
    else:
        prompt, version = PLAYBOOK_TEMPLATE.format(agents_md=agents_md, diff=diff), PLAYBOOK_VERSION
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="pr-review",
        model=MODEL_NAME,
        input=prompt,
        metadata={"repo": repo, "pr": pr, "label": label, "prompt_version": version},
    ) as generation:
        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=TEMPERATURE,
                )
                raw_text = response.choices[0].message.content
                usage = response.usage
                input_cost = usage.prompt_tokens / 1_000_000 * PRICE_PER_MILLION_INPUT
                output_cost = usage.completion_tokens / 1_000_000 * PRICE_PER_MILLION_OUTPUT
                USAGE["calls"] += 1
                USAGE["input_tokens"] += usage.prompt_tokens
                USAGE["output_tokens"] += usage.completion_tokens
                generation.update(
                    output=raw_text,
                    usage_details={"input": usage.prompt_tokens,
                                   "output": usage.completion_tokens,
                                   "total": usage.total_tokens},
                    cost_details={"input": round(input_cost, 6),
                                  "output": round(output_cost, 6),
                                  "total": round(input_cost + output_cost, 6)},
                    metadata={"attempt": attempt + 1},
                )
                langfuse.flush()
                data = json.loads(raw_text)
                findings = data if isinstance(data, list) else data.get("findings", [])
                return _clean(findings)
            except Exception as e:
                USAGE["failed_attempts"] += 1
                # Retrying cannot help if the request is too large or the daily quota is used.
                fatal = getattr(e, "status_code", None) == 413 or "tokens per day" in str(e)
                if fatal or attempt == retries - 1:
                    generation.update(output=f"FAILED: {e}")
                    langfuse.flush()
                    raise
                print(f"Model call failed ({e}), retrying in {delay}s...")
                time.sleep(delay)
    return []