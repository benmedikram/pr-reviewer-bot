# Run record: Experiment 0 (Click playbook applied to Sentry)

| Field | Value |
|---|---|
| Date | 2026-10-05 (UTC): first call 10:46, last call 22:13. Assembled from several partial runs because of rate limits. An earlier run with a wrong playbook (39 traces, 10:25 to 10:33 UTC, $0.017402) is excluded from all figures below. |
| Model | openai/gpt-oss-120b on Groq free tier; temperature not set (provider default) |
| Playbook | benmedikram/click AGENTS.md at commit 7881d0e (2026-09-28, the only commit that changed this file) |
| Bot commit | Last committed state of `reviewer/llm.py` during the series: fdef871 (2026-10-05 11:57 +0100 = 10:57 UTC, "Handle model returning a bare list"). The first calls of the series (10:46 UTC) ran before this commit. `evals/run_baseline.py` is not in fdef871. The chunking code was edited between retries and not every intermediate state was committed (see "What the model saw"). |
| Scored set | 7 PRs, 22 reference issues (see EXCLUSIONS.md) |
| Findings emitted | 28 |
| Model calls | 42 attempts for the 7 PRs: 33 succeeded, 9 failed on rate limits. 22 successful calls produced the findings; the other 11 (PR 93824: 7, PR 95633: 3, PR 80168: 1) came from earlier attempts interrupted by rate limits or redone with a different chunking, and their results were not used. |
| Tokens | 107,539 input, 33,140 output (all 33 successful calls, including the 11 not used; failed attempts carry no usage) |
| Cost | $0.036013 for the 7 scored PRs, including the 11 calls not used = $0.005145 per PR (at $0.15 / $0.60 per million input / output tokens, no caching discount; free tier, nothing billed) |
| Call latency | per model call (not review latency), successful calls: median 14.1 s, mean 17.8 s |
| Diffs | Cached in evals/diffs/ (not committed). SHA-256 in evals/diff_hashes.txt, computed on 10-11-2026 after the run, from diffs downloaded again; their sizes equal those in the run logs. |
| Labeling | - Labeling: done by Ikram, with a draft proposed by an AI assistant (Claude) for the match column and for wording; each verdict that depends on the code was checked by the labeler in the PR diff, and the checks are recorded in the justification column. There was no independent second labeler. Verdicts rely on the diff and on the current state of the Sentry repository for conventions. |
| Reproducibility | Not reproducible with a single command: three different chunking settings were used across the PRs (see below). Experiments 1 and 2 use one fixed chunking for all PRs. |

## What the model saw (chunking)

| PR | Diff size (chars) | Split mode | Model calls used | Characters reviewed | Truncated |
|---|---|---|---|---|---|
| 94376 | 22,375 | one call per file | 7 | 22,375 | no |
| 67876 | 19,655 | one call per file | 3 | 19,655 | no |
| 93824 | 19,221 | files packed, up to 20,000 chars per call | 1 | 19,221 | no |
| 77754 | 16,941 | files packed, up to 20,000 chars per call | 1 | 16,941 | no |
| 80528 | 21,117 | files packed, up to 20,000 chars per call | 2 | 21,117 | no |
| 95633 | 55,464 | files packed, up to 6,000 chars per call | 5 | 24,290 (44%) | yes: three files cut at 6,000 (12,719, 15,852 and 20,603 chars) |
| 80168 | 29,004 | files packed, up to 6,000 chars per call | 3 | 13,469 (46%) | yes: test_detector.py cut at 6,000 of 21,535 chars (28% seen); the three source files seen in full |

Sizes and split modes were reconstructed from the terminal logs of the runs. The rows for 95633 and 80168 were recomputed with evals/seen_check.py using the current code (6,000-character limit) and match the logs.