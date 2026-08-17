# Verify rubric — Completeness / Correctness / Coherence

The three-axis spec review, ported from OpenSpec `workflows/verify-change.ts`
(the `openspec …` CLI calls removed). It judges the implementation on
`sdd/<ticket>` against `specs/<capability>.md`, and maps every finding to a
severity the delivery PR can carry.

## The three axes

### Completeness — is everything the spec promised actually there?

- Every `### Requirement:` has implemented behavior.
- Every `#### Scenario:` (WHEN/THEN) has a corresponding code path **and** a test that exercises it.
- No requirement silently dropped; no "TODO / not yet" standing in for a promised behavior.
- `## ADDED` requirements exist; `## MODIFIED` reflect the new full content; `## REMOVED` are actually gone (with the migration the delta named).

### Correctness — does it do what the spec says?

- Each scenario's THEN holds for its WHEN — verified by reading the code and its test.
- No behavior contradicts a `SHALL` / `MUST`.
- Error/failure paths behave as specified, not just the happy path.
- Boundaries (empty, null, min/max, first/last) match the spec's intent.

### Coherence — does it hang together?

- Consistent with `design.md` (the chosen approach, not a silently different one).
- Consistent with the target repo's conventions (its `CLAUDE.md`) — naming, layering, error handling.
- No internal contradictions, no dead/unreachable paths introduced, no duplicated source of truth.
- The diff is surgical: every changed line traces to a task/requirement (per Surgical Changes).

## Severity mapping

| Severity       | Meaning                                                                          | Effect                                                                  |
| -------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **CRITICAL**   | A requirement is unmet, a `SHALL` is violated, or a scenario's behavior is wrong | Leaves its criterion **unchecked** → blocks status `verified`           |
| **WARNING**    | Risky, ambiguous, or convention-breaking, but no requirement is violated         | Rides in the PR draft for a human to weigh before merge; does not block |
| **SUGGESTION** | Improvement / cleanup opportunity                                                | Informational only                                                      |

Only CRITICAL blocks — and it blocks **through the acceptance-criteria check**
(an unmet criterion stays unchecked), not by halting the pipeline. WARNING and
SUGGESTION never block; the review's value is putting them in front of the human
at merge time, not stopping the flow.

## How this feeds the criteria check

Each `#### Scenario:` in `specs/<capability>.md` **is** an acceptance criterion.
A scenario is checked only when Completeness (a test exercises it) and Correctness
(the behavior matches) both hold. A Coherence-only concern about that scenario is a
WARNING, not grounds to uncheck a criterion that otherwise passes.

## Read-only discipline

Review reads code and writes only the vault review artifact (`review.md`). It never
edits target application code — a wanted fix is reported as a finding and handed back
to `sdd-apply` / `sdd-verify`, never applied from here.
