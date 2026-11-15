# Week 1 evidence

Sandbox: benmedikram/click, PR #7 (https://github.com/benmedikram/click/pull/7). Not merged. It contains planted defects in src/click/utils.py (a hard-coded password, a mutable default argument, an off-by-one condition and a broad `except Exception`), chosen because the playbook covers them. This shows that the pipeline works (inline comments, delay, no rejection), not review quality.

Measured on 15-11-2026 with evals/measure_latency.py.

| Run | Trigger | Workflow run | Conclusion | Trigger to review (s) | Run duration (s) | Inline comments |
|---|---|---|---|---|---|---|
| 1 | PR opened | https://github.com/benmedikram/click/actions/runs/43712873425 | success | 25 | 29 | 4 |
| 2 | push | https://github.com/benmedikram/click/actions/runs/43715652289 | success | 28 | 35 | 4 |
| 3 | push | https://github.com/benmedikram/click/actions/runs/43716162235 | success | 29 | 33 | 4 |
| 4 | push | https://github.com/benmedikram/click/actions/runs/43716302559 | success | 28 | 34 | 4 |
| 5 | push | https://github.com/benmedikram/click/actions/runs/43716447362 | success | 24 | 28 | 4 |

Langfuse trace (run 1): https://cloud.langfuse.com/project/cmuto6yfa00alad0ca44e33qb/traces?traceTab=attributes&peek=d5530c8655894b9c&observation=d5530c8655894b9c&traceId=7aa3103e01eb2ddb679576963af2e129&timestamp=2026-11-15T12%3A15%3A28.473Z 
Public copy for the supervisor: https://cloud.langfuse.com/project/cmuto6yfa00alad0ca44e33qb/traces/7aa3103e01eb2ddb679576963af2e129?observation=d5530c8655894b9c
Tokens: 1,925 input + 1,117 output = 3,042. Cost: $0.000959 (at $0.15 / $0.60 per million input / output tokens). Model call duration: 2.6 s.

Latency: median 28 s, maximum 29 s (target: under 180 s). "Trigger to review" is the time between the creation of the workflow run and the submission of the review. It does not include any delay before GitHub created the run.

Five consecutive runs with a review posted and no comment rejected by GitHub: all five runs succeeded, and each review has state COMMENTED with 4 inline comments. The bot never approves or requests changes.

## Observations

- The same 4 findings were posted on the same lines in all 5 runs. The bot reviews the whole PR diff on every push and does not check its earlier comments, so on a real PR comments would be duplicated after each push. A fix (skip findings already posted on the same line, or review only new commits) is not implemented yet and belongs with the Week 2 guardrails (comment limit, deduplication).
- `temperature` was not set, so identical results across runs do not show determinism.
- The failing checks `pre-commit` and `Tests / typing` on this PR are Click's own checks, caused by the planted code. They are unrelated to the bot.

## Limits

One small diff (one model call per run), one PR, free-tier model. The delay reported here does not predict the delay on large PRs, which need several model calls and hit rate limits.