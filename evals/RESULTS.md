# Baseline — Week 1

| Date | Commit | PRs tested | Precision | Recall | Avg. cost/PR |
|---|---|---|---|---|---|
| 2026-10-05 | fdef871 | 8/10 | 3.1% | 3.8% | $0.006956 |

## Methodology
- Dataset: Martian Code Review Bench (MIT), Sentry subset
- 8 usable PRs out of 10 (see `evals/sentry_prs.json`)
- Playbook: AGENTS.md from benmedikram/click (27 rules), fetched dynamically
- Large diffs split by file (Groq free-tier limit: 8000 tokens/min)
- Matching done manually by description (golden comments have no line number)

## Cost breakdown per PR
| PR | Cost |
|---|---|
| 92393 | $0.003178 |
| 94376 | $0.008148 |
| 67876 | $0.004089 |
| 93824 | $0.010999 |
| 77754 | $0.005019 |
| 80528 | $0.004996 |
| 95633 | $0.013032 |
| 80168 | $0.006188 |
| **Average** | **$0.006956** |

Note: PRs 93824, 95633 and 80168 cost noticeably more because they required multiple retries to work around Groq's free-tier rate limits (TPM/TPD caps) — these figures reflect real operational cost, including retries, not an idealized single-call cost.

## Result: 1 match out of 32 findings emitted / 26 golden comments
Precision 3.1%, recall 3.8%.

Only match: PR 80168 — both the bot and the golden comment flag the same change to `process_detectors`'s return type (line 49), worded differently (the bot asks for a compatibility confirmation, the golden comment flags a stale docstring) but describing the same code change.

## Data anomaly identified
The golden comments attributed to PR 92393 (via `original_url`) are entirely about `OptimizedCursorPaginator` and cursor-based pagination — a topic absent from the actual diff of this PR (which is about the span buffer and Redis).
This suggests a mislabeling in the Martian dataset between this entry and the invalid entry #1 of the original file. Excluding this PR as unreliable would leave 7 usable PRs out of 10.

## Analysis
31 of the 32 findings come from two AGENTS.md rules written for Click's conventions (missing CHANGES.md entry, backwards-compatibility confirmation on a signature change) — rules that fire mechanically but rarely align with Sentry's actual bugs (race conditions, slicing errors, broken deserialization). The one real match came from exactly one of these "generic" rules, which happened to overlap with a real issue a human reviewer had also flagged.

## Known limitations
- Dataset: at least 1 of 8 PRs likely has mislabeled golden comments
- Golden comments have no line number → matching is semantic, based on human judgment
- File-level splitting for large diffs; one finding ("Syntax error" on PR 95633, conf. 0.98) is possibly a splitting artifact that should be verified manually
- Playbook not tailored to the Sentry domain (written for Click)