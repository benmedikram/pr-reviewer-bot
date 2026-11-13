# Scoring rules (frozen before scoring experiments 1 and 2)

## Benchmark match (bot finding vs. reference issue)
- strict: both identify the same underlying defect (same root cause in the same code), so fixing one would resolve the other. Pointing at the same line, function or code change is not enough.
- ambiguous: related, but the two describe different problems, or you cannot agree. Reported only in the lenient figure.
- none: no corresponding reference issue.
- Same function or code region as a reference issue, but a different defect, is none, not ambiguous.

A finding matches at most one reference issue. A reference issue matched by several findings counts once for recall.

Precision = matched findings / emitted findings
Recall    = matched reference issues / reference issues
Emitted findings = findings kept after the diff-line filter. Findings on lines outside the diff are dropped before scoring and reported separately (none among the scored PRs in experiment 0).
Headline figures use strict matches. Lenient (strict + ambiguous) is
reported as a sensitivity check.

## Manual verdict (independent of the benchmark)
- actionable: true, and a maintainer could act on it from the comment alone
- low-value: true but trivial, or a question with no concrete problem
- incorrect: false claim about the code, or a project rule that does not apply to this repository
- unsure: could not verify in about 10 minutes; discuss with the supervisor

An unmatched finding is not automatically incorrect.

## Labeling procedure
- Match and verdict are decided from the PR's real diff (cached in evals/diffs/, hashes in evals/diff_hashes.txt), read next to the reference issues.
- Facts about repository conventions (e.g. whether a changelog entry is required) are checked in the target repository and recorded in the justification.
- A verdict that cannot be settled in about 10 minutes is marked unsure and reviewed with the supervisor.
- Record who labeled, whether independently, and the date, in each run's record.

## Repeated runs
If a condition is run more than once, report each run separately (and the range), not only an average.

## Change log
(Record the date and reason of any rule change here.)

2026-11-10: clarified that location alone never makes a finding ambiguous (made after labeling the first 5 rows, before any results were computed).
2026-11-13: added the definition of emitted findings, the labeling procedure and the rule for repeated runs. These document how experiment 0 was scored and change no label or result.