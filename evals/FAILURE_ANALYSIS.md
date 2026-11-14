# Failure analysis, experiment 0 (Click playbook applied to Sentry)

Data: scoring/exp0_click_playbook.csv (28 findings) and scoring/exp0_missed.csv (22 reference issues). One run, 7 PRs. Labeling is described in RESULTS.md.

## Emitted findings (28), by cause

| Cause | Count | Share |
|---|---|---|
| irrelevant-rule | 9 | 32% |
| noise | 13 | 46% |
| incorrect-reasoning | 4 | 14% |
| insufficient-context | 1 | 4% |
| chunking-artifact | 1 | 4% |
| line-mapping | 0 | 0% |

- irrelevant-rule: the 9 changelog findings. They apply a Click convention (a CHANGES.md entry) that Sentry does not follow.
- noise: true but of no use, or a question without a concrete problem (7 repeated compatibility questions on parameters that have a default value, two `except Exception: pass` in test setup code, two missing return annotations, and others).
- incorrect-reasoning (findings 7, 8, 10, 24): the information that contradicts the claim was in the part the model saw. Example: finding 8 claims a division by zero, but `max_processes or len(buffer.assigned_shards)` is in the same diff, reviewed in a single call.
- insufficient-context (finding 20): the claim depends on the behavior of `get_text_list`, which is defined outside the diff.
- chunking-artifact (finding 26): see "Chunking case" below.
- line-mapping: checked with `evals/anchor_check.py` (output in scoring/anchors.txt). No finding was anchored on an unrelated line. The weakest anchor is finding 21, a missing-changelog finding placed on a `return` statement.

Line mapping was checked with evals/anchor_check.py (output in scoring/anchors.txt): no finding was anchored on an unrelated line.

## Missed reference issues (22), by cause

| Cause | Count | Share |
|---|---|---|
| not-seen | 2 | 9% |
| needs-surrounding-code | 3 | 14% |
| no-rule-for-it | 11 | 50% |
| seen-but-missed | 6 | 27% |

- not-seen (95633-R2, 80168-R3): the code lies after the 6,000-character cut. Two more issues (95633-R1, 80168-R1) were only partly visible.
- needs-surrounding-code (94376-R3, 77754-R4, 80168-R1): the defect depends on code defined outside the changed lines, or in a file reviewed in a different call.
- no-rule-for-it: no rule in the playbook points to this kind of defect. The prompt also told the model to report only what the playbook asks for, so such defects were excluded by construction.
- seen-but-missed (94376-R1, 67876-R1, 67876-R3, 93824-R5, 77754-R3, 80168-R2): code visible and a rule close to the defect. Some assignments are judgement calls (see the notes in exp0_missed.csv).

## Most frequent causes and planned fixes

| Rank | Cause | Evidence | Planned fix | Tested in |
|---|---|---|---|---|
| 1 | noise | 13 of 28 findings (46%) | Cap the number of comments per rule per PR; ask a compatibility question only when a parameter has no default value; allow an empty result | Cap and compatibility rule: a later, separate experiment. Empty result allowed: experiments 1 and 2 |
| 2 | irrelevant-rule | 9 of 28 findings (32%) | A playbook written for the repository under review, with a documented source for each rule | Experiment 2 against experiment 1 |
| 3 | no-rule-for-it | 11 of 22 reference issues (50%) | Compare a generic prompt (no playbook) with a repository-specific playbook, to see how many of these defects a generic prompt finds | Experiments 1 and 2 |
| 4 | seen-but-missed | 6 of 22 reference issues (27%) | Not explained by one run. First step: run each condition twice and see whether the same defects are missed | Experiments 1 and 2, repeated |
| 5 | needs-surrounding-code, incorrect-reasoning | 3 of 22 reference issues, 4 of 28 findings | PR overview and bounded access to surrounding code | Week 2 (GitHub MCP, bounded code access) |
| 6 | not-seen, chunking-artifact | 2 of 22 reference issues, 1 of 28 findings | Split large files at hunk boundaries instead of truncating; fixed before experiments 1 and 2 | Pipeline change, not an experiment |

Experiments 1 and 2 change only the context (generic prompt versus a repository-specific playbook). The other fixes are tested separately, so each effect can be attributed to one change.

## Chunking case

Finding 26 ("missing return type after '->'") is a chunking artifact. The last call for PR 95633 ends with `def test_thread_queue_parallel_concurrent_subscriptions(self) ->`, cut before `None:` (the definition starts at character 5,936 of the file diff; the real line is `-> None:`). Re-running the current chunking code reproduces the call sizes of the run logs (1,126, 6,000, 5,164, 6,000 and 6,000 characters). This is one case, so it does not show that chunking is a frequent cause.

## Hypotheses, not conclusions

- Context matters: to be tested by experiments 1 and 2.
- Whether the model is interchangeable, or whether context alone determines quality, is not established by these results.
- The share of no-rule-for-it partly reflects how the prompt was written, not only the playbook content.

## Limits of this analysis

One run, 7 PRs, a partial reference set (a defect without a reference comment is not necessarily wrong), and labeling by the team with an AI-drafted proposal (see RESULTS.md). Several cause assignments are judgement calls. Percentages are descriptive and not statistically meaningful at this sample size.