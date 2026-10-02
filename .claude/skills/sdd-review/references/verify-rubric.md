# Verify rubric — Completeness / Correctness / Coherence

Adapted from OpenSpec v1.13.2 (`db230978`),
`src/core/templates/workflows/verify-change.ts`. Upstream verification is advisory;
blocking required `Not verified` checks is this SDD pipeline's own policy.

## Evidence states

For each applicable check report **Passed**, **Failed**, or **Not verified
(reason)**. Use **Not applicable (reason)** only for intentionally inapplicable
checks, never for missing/unreadable evidence. A required Failed/Not verified
check or an open CRITICAL prevents `verified`. N/A is excluded, not counted as a
pass. A parser returning no requirements is not proof of a removal-only change.

## Completeness — check the delta operation first

| Operation | Required evidence |
| --- | --- |
| ADDED | The new requirement is implemented and its scenarios are covered. |
| MODIFIED | The full updated behavior and scenarios in the delta are implemented; compare the baseline for accidental scenario loss. |
| REMOVED | The old behavior is gone. Absence is success, not a missing implementation. A reachable path still providing it is CRITICAL. |
| RENAMED | The TO requirement preserves the baseline FROM behavior and scenarios. Do not require code symbols/files to be renamed or report FROM as missing. |

For REMOVED, a name appearing in docs, artifacts, or migration-only code does not
alone prove the behavior remains. A shared code path that still delivers the old
behavior does count, even if it also supports an ADDED requirement. Follow the
migration contract; do not try to make removed scenarios pass again.

For RENAMED, read the baseline FROM requirement (or TO if the canonical spec is
already synced). If TO also has a MODIFIED block, check that block instead. Missing
baseline evidence is Not verified, not automatic success. Use canonical project
specs when available; otherwise establish a baseline from merged changes and the
pre-change code/tests, recording uncertainty rather than treating an active delta
as current truth.

All tasks must be complete according to `validate_sdd.py --tasks-json`. Repo
instructions/context constrain the work; they are not completion evidence.

## Correctness — operation-aware acceptance criteria

- Only scenarios under ADDED/MODIFIED enter the new-behavior scenario checklist.
- Each requires a matching implementation and a test exercising its WHEN/THEN.
- Check error paths and boundaries actually required by the spec.
- REMOVED/RENAMED receive explicit operation checks from Completeness, with
  evidence references, instead of being dropped from acceptance entirely.
- For a readable removal/rename-only delta, new-behavior mapping and scenario
  coverage are N/A; operation checks must still pass.
- With `skip_specs: true`, spec checks are N/A. Check every task's stated outcome
  and the evidence that externally observable behavior is unchanged. Missing
  applicable evidence is Not verified. No invented scenarios.

## Coherence

Check the chosen design, repo conventions, contradictory/dead paths, and whether
each changed line traces to a task/requirement. Report conflicts among repo
instructions, the approved plan, and explicit user choices; never quietly replace
one with another. Missing applicable design/code evidence is Not verified.

## Findings and readiness

| Severity | Meaning | Effect |
| --- | --- | --- |
| CRITICAL | Unmet contract, incorrect behavior, or blocking correctness/security finding | Blocks `verified` |
| WARNING | Non-blocking risk, ambiguity, or convention concern | Include for human review |
| SUGGESTION | Optional improvement | Informational |

Keep evidence state separate from severity: missing evidence need not be a proven
bug, but still prevents a required check passing. Preserve blocking findings from
code review even when unrelated to a scenario; do not downgrade security findings
to make the checklist pass.

`review.md` records each criterion/check, evidence state, reason, and code/test
locations; counts ADDED/MODIFIED separately from confirmed removals/renames. It
also records the reviewed commit and plan fingerprint (see the skill). Report
readiness only when all required checks passed and no blocking finding remains.

Review writes only vault evidence and the explicit status/task repair handoff; it never edits application code. Hand fixes to `/sdd-apply` and plan revisions
to `/sdd-propose --update`; evidence-only follow-up goes to `/sdd-verify`.
