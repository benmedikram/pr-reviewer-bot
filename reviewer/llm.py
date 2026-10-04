import json
import os
import time
from groq import Groq
from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
langfuse = get_client()

# Prix Groq pour openai/gpt-oss-120b, en dollars par million de tokens.
# Vérifier sur console.groq.com/docs/pricing si Groq change ses tarifs.
PRICE_PER_MILLION_INPUT = 0.15
PRICE_PER_MILLION_OUTPUT = 0.60

MODEL_NAME = "openai/gpt-oss-120b"

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


def _coerce_confidence(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    mapping = {"low": 0.4, "medium": 0.65, "high": 0.85}
    return mapping.get(str(value).lower(), 0.5)


def get_findings(agents_md: str, diff: str, repo: str = "", pr: int = 0,
                  retries: int = 3, delay: int = 5) -> list[dict]:
    prompt = PROMPT_TEMPLATE.format(agents_md=agents_md, diff=diff)

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="pr-review",
        model=MODEL_NAME,
        input=prompt,
        metadata={"repo": repo, "pr": pr},
    ) as generation:

        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                raw_text = response.choices[0].message.content
                usage = response.usage
                cost = (
                    usage.prompt_tokens / 1_000_000 * PRICE_PER_MILLION_INPUT
                    + usage.completion_tokens / 1_000_000 * PRICE_PER_MILLION_OUTPUT
                )

                input_cost = usage.prompt_tokens / 1_000_000 * PRICE_PER_MILLION_INPUT
                output_cost = usage.completion_tokens / 1_000_000 * PRICE_PER_MILLION_OUTPUT

                generation.update(
                    output=raw_text,
                    usage_details={
                        "input": usage.prompt_tokens,
                        "output": usage.completion_tokens,
                        "total": usage.total_tokens,
                    },
                    cost_details={
                        "input": round(input_cost, 6),
                        "output": round(output_cost, 6),
                        "total": round(input_cost + output_cost, 6),
                    },
                    metadata={"attempt": attempt + 1},
                )
                langfuse.flush()

                data = json.loads(raw_text)
                findings = data.get("findings", [])
                for f in findings:
                    f["confidence"] = _coerce_confidence(f.get("confidence"))
                return findings

            except Exception as e:
                if attempt == retries - 1:
                    generation.update(output=f"FAILED: {e}")
                    langfuse.flush()
                    raise
                print(f"Model call failed ({e}), retrying in {delay}s...")
                time.sleep(delay)
    return []