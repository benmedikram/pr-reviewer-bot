# Evaluation results

## Summary

| Exp. | Context | Findings | Precision (strict) | Recall (strict) | Precision (lenient) | Recall (lenient) | Cost per PR |
|---|---|---|---|---|---|---|---|
| 0 | Click playbook applied to Sentry (initial experiment) | 28 | 0/28 = 0.0% | 0/22 = 0.0% | 1/28 = 3.6% | 1/22 = 4.5% | $0.0051 |
| 1 | Generic prompt, no playbook | not run yet | | | | | |
| 2 | Sentry-specific playbook | not run yet | | | | | |

Experiments 1 and 2 will use the same model, PRs, chunking, cached diffs and code commit as experiment 0, and the scoring rules in `SCORING.md`.

## Experiment 0: Click playbook applied to Sentry

Setup: model openai/gpt-oss-120b (Groq free tier, temperature not set), playbook = AGENTS.md of benmedikram/click (27 rules), 7 scored Sentry PRs from the Martian Code Review Bench (MIT), 22 reference issues, 28 findings. Run date: 2026-10-05; assembled from several partial runs because of rate limits. Run record: `runs/exp0_click_playbook.md`. Labeled sheet: `scoring/exp0_click_playbook.csv`. All 28 rows: `scoring/exp0_click_playbook_table.md`.

### Scored set and exclusions
The official Sentry file has 10 entries; 7 are scored. Full record: `EXCLUSIONS.md`.

| Entry | Reason excluded |
|---|---|
| #1 "Enhanced Pagination Performance for High-Volume Audit Logs" | No real PR behind it (mirror repo, no `original_url`, reviewed commit not in the repo). |
| #5 "Replays Self-Serve Bulk Delete System" | Dataset note: no such PR, a mix of many PRs. |
| getsentry/sentry#92393 "Evict spans during insert" | Reference comments are about `OptimizedCursorPaginator`. The diff touches only spans code (Lua script, `spans/buffer.py`, consumers, span tests) and does not contain "Paginator". The comments repeat those of entry #1, so they appear mis-attributed. |

Effect: PRs 8 to 7, reference issues 26 to 22, findings 32 to 28. A heuristic check (`evals/check_labels.py`) and manual confirmation of the four flagged comments found no other PR whose reference comments describe different code.

### Benchmark scores (against the reference issues)

| Matching | Precision | Recall |
|---|---|---|
| Strict (same underlying defect) | 0/28 = 0.0% | 0/22 = 0.0% |
| Lenient (strict + ambiguous) | 1/28 = 3.6% | 1/22 = 4.5% |

The only ambiguous pair is the finding on PR 80168 about the changed return type of `process_detectors` (a compatibility question) and reference 80168-R2 (the docstring says it returns a list, but it returns a dict). Both start from the same code change but describe different issues, so it is not a strict match.

### Manual assessment of each finding (independent of the benchmark)

| Verdict | Findings |
|---|---|
| actionable | 0 |
| low-value (true but trivial, or a question without a concrete problem) | 13 |
| incorrect (false claim, or a rule that does not apply to Sentry) | 15 |
| unsure | 0 |

| Category | incorrect | low-value | actionable |
|---|---|---|---|
| changelog | 9 | 0 | 0 |
| signature-compat | 0 | 8 | 0 |
| bare-except | 1 | 2 | 0 |
| docs | 1 | 1 | 0 |
| type-hint | 0 | 2 | 0 |
| other | 2 | 0 | 0 |
| secret | 1 | 0 | 0 |
| syntax-error | 1 | 0 | 0 |
| **Total** | **15** | **13** | **0** |

An unmatched finding is not automatically wrong: the reference set is partial.

### Observations (preliminary; the full failure analysis follows separately)
- 17 of 28 findings (61%) come from two Click-specific rules: a CHANGES.md entry per change (9) and a compatibility question on signature changes (8). Sentry has no CHANGES.md; its root CHANGES file appears to be generated from PR titles. A third Click rule (documentation updates) produced 2 more.
- Seven of the eight signature findings ask the same question about newly added parameters; none raised a concrete problem.
- In PR 94376 the bot flagged two `except Exception: pass` blocks (rows 4 and 5, judged low-value, test setup code) in the same code block as the `if client_sample_rate:` check described by reference 94376-R1, and did not report that defect.
- Some incorrect findings are reasoning errors despite available context: the claimed ZeroDivisionError in PR 93824 (row 8) ignores `max_processes or len(buffer.assigned_shards)`, defined a few lines above in the same diff; the "hard-coded secret" in PR 67876 (row 7) is a placeholder value in a mocked response.
- The "syntax error" on PR 95633 (row 26) is incorrect; a chunking artifact is suspected (files were truncated at 6000 characters) and is to be confirmed.

### Cases to review with the supervisor

| id | PR | Bot finding | Reference issue | Match | Verdict | Justification |
|---|---|---|---|---|---|---|
| 4 | 94376 | `factories.py:351` Bare except Exception hides errors; consider catching specific exceptions. | - | none | low-value | Test factory wraps a chained dict lookup in except Exception: pass; any lookup error silently yields None. True but harmless in test setup code; narrowing to AttributeError would be a nit. |
| 5 | 94376 | `factories.py:356` Bare except Exception hides errors; consider catching specific exceptions. | - | none | low-value | Test factory ignores any error from float(client_sample_rate), so an invalid test value is silently skipped. True, and could hide a test mistake, but limited to test setup code. |
| 8 | 93824 | `flusher.py:65` Potential division by zero: if max_processes is falsy, self.num_processes can be zero, causing i % self.num_processes to raise ZeroDivisionError. | - | none | incorrect | max_processes falls back to len(buffer.assigned_shards) when falsy (`self.max_processes = max_processes or len(buffer.assigned_shards)`), and the modulo only runs inside a loop over assigned_shards, so the claimed ZeroDivisionError cannot occur. |
| 10 | 93824 | `__init__.py:433` Documentation not updated for the new "--flusher-processes" option, which changes user-facing behavior. | - | none | incorrect | The option is documented only by its own help text, which this PR adds in the same code change; no separate documentation page for it exists in this repository (searched the repo for the option name), so the claim that documentation was not updated is false. |
| 23 | 95633 | `__init__.py:121` The addition of the 'thread-queue-parallel' mode changes the CLI's user-facing behavior but no documentation under docs/ appears to be updated. Add or update documentation accordingly. | - | none | low-value | No documentation page describing the consumer modes exists in this repository (searched for the existing mode 'batched-parallel': all 9 matching files are Python source); the PR adds the new choice value without describing it, and the existing help text is unchanged. True but minor, since consumer modes are not documented outside the code. |
| 26 | 95633 | `test_results_consumer.py:1780` Syntax error: function definition missing return type after '->' | - | none | incorrect | The real code has a return annotation after '->' in the PR diff, so the reported syntax error does not exist; possibly caused by a chunk truncated mid-line (to be confirmed in the failure analysis). |
| 27 | 80168 | `detector.py:49` Changed return type of public function process_detectors; confirm backward compatibility is handled and deprecation is documented. | 80168-R2 | ambiguous | low-value | Same code change as 80168-R2 (stale docstring) but the finding only asks to confirm compatibility; the PR already updates the callers, so the comment raises no concrete problem. |


### Cost and reproducibility
Model calls for the 7 scored PRs: 42 attempts (33 succeeded, 9 failed on rate limits); 107,539 input and 33,140 output tokens. Costs are computed from token counts at $0.15 / $0.60 per million input / output tokens, without a caching discount; the free tier was used, so nothing was billed. Failed attempts carry no cost.

| PR | Cost |
|---|---|
| 94376 | $0.005783 |
| 67876 | $0.002318 |
| 93824 | $0.008988 |
| 77754 | $0.002570 |
| 80528 | $0.003157 |
| 95633 | $0.009204 |
| 80168 | $0.003993 |
| **Total** | **$0.036013** |
| **Average** | **$0.005145** |

PRs 93824 and 95633 cost more because they needed retries and several calls (large diffs split by file).

Diffs are cached byte-for-byte (`evals/diffs/`, not committed) with SHA-256 hashes in `evals/diff_hashes.txt`. Latency per model call (successful calls): median 14.1 s, mean 17.8 s, max 58.2 s.

### Superseded initial reading
The first report counted 1 match out of 32 findings and 26 reference issues (3.1% precision, 3.8% recall) on 8 PRs, at $0.006956 per PR. It was revised because: PR 92393 was excluded; the match on PR 80168 is no longer counted as strict; and the match definition was made stricter. The earlier cost figure also included the 39 traces of a first run with the wrong playbook (superseded) and PR 92393. That first report also stated that 31 of 32 findings came from two rules; the labeled data gives 17 of 28.

## Known limitations
- Small set: 7 PRs and 22 reference issues. The reference comments are partial and have no line numbers, so matching is semantic.
- Labeling: done by Ikram, with a draft proposed by an AI assistant (Claude) for the match column and for wording; each verdict that depends on the code was checked by the labeler in the PR diff, and the checks are recorded in the justification column. There was no independent second labeler. Verdicts rely on the diff and on the current state of the Sentry repository for conventions.
- One run per condition so far; outputs vary between runs.
- Experiment 0 was assembled from several partial runs, and the code changed between them (JSON handling in `llm.py`, chunk packing). It is a documented starting point, not a clean control.
- In experiment 0 the model saw only part of two large diffs: PR 95633 (24,290 of 55,464 characters, 44%) and PR 80168 (13,469 of 29,004, 46%), because files were truncated at 6000 characters to fit the free-tier token limit. The other five PRs were reviewed in full (chunk sizes from the run logs).
- Splitting by file can also hide dependencies between files, and a cut in the middle of a line can create artifacts.
- The playbook was written for Click; this experiment measures a mismatched context.