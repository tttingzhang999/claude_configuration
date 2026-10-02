# Shared planning contract

Adapted from OpenSpec v1.13.2 (`db230978`), `schemas/spec-driven/schema.yaml`
and `workflows/update-change.ts`. Vault paths, approval gates, review freshness,
and post-merge spec sync are local adaptations, not upstream CLI guarantees.
All six SDD skills read this contract on entry; mode-specific details stay in
the linked references. No OpenSpec CLI/store installation is required.

## Artifacts and applicability

The ordinary four-pack is proposal.md, specs/<capability>.md, design.md, tasks.md.
Use the exact capability path (including existing nested segments); never mix the
flat `<capability>.md` convention with OpenSpec's `<capability>/spec.md` convention.
Build order is proposal → specs → design → tasks. Existence alone is not semantic
completeness: every capability declared in proposal needs its spec and vice versa.

For a change with no externally observable behavior change, proposal may declare:

```yaml
skip_specs: true
skip_specs_reason: "Internal refactor; external behavior is unchanged."
```

Missing skip_specs means false for old tickets. With true, New/Modified
Capabilities explicitly say None; there must be no delta specs. Still write
proposal, a concise design, and tasks with verification. File type does not decide
applicability: security/config/deployment changes can alter behavior. Refactoring
requires regression evidence even when no new requirement is needed. Switching
an existing plan to skip_specs goes through --update and explicitly resolves old
specs; never silently ignores them. No retroactive bulk conversion of old tickets.

Apply/verify/review/deliver respect this same applicability decision. Spec checks
and spec sync are N/A for skip_specs; task outcomes, applicable CI, code review,
and evidence for unchanged behavior remain required. For docs-only work, numeric
code coverage can be N/A with a reason. Required checks cannot become N/A simply
because the tool or evidence is unavailable. Human design approval still applies.

## Shared read-only validator

Resolve the vault root before running:

```bash
uv run .claude/scripts/validate_sdd.py "<change-folder>" --mode draft
uv run .claude/scripts/validate_sdd.py "<change-folder>" --mode ready
uv run .claude/scripts/validate_sdd.py "<change-folder>" --tasks-json
uv run .claude/scripts/validate_sdd.py "<change-folder>" --mode ready --fingerprint
```

- Draft: partial plans are allowed; malformed existing metadata/tasks still fail.
- Ready: required artifacts, capabilities/spec correspondence, delta structure,
  scenarios, task tiers, and skip contradictions must pass before apply. This does
  not establish approval, semantic completeness, or correct implementation.
- Task JSON: `{tasks: [{line, done, text}], total, completed}`. Only x/X with optional
  spaces is done. Other single-character or empty boxes stay pending. Alternate
  CommonMark list markers and nested tasks count; Markdown links do not. Generate
  canonical `- [ ] N.M [tier] ...` (tier in backticks). Multi-character pseudo-boxes
  such as `[WIP]` are unsupported: correct/report them rather than assume complete.
- Fingerprint: hashes proposal/design/tasks/specs and any baseline snapshots, excluding lifecycle metadata
  (status, design_approved, pr, spec_sync) and task checkmarks. It is conservative:
  prose/format changes may alter it; never pretend it proves semantic equivalence.

Keep status/next-step orchestration in the skills. The validator only reports
facts; PostToolUse remains informational and uses draft mode.

## Re-entry and evidence

Before dispatching or resuming, read current proposal and run ready validation
where implementation/verification requires it. Do not invoke apply on missing
artifacts, stale approval, or a merged change. Archived changes are immutable
history for behavior changes: create a new ticket. Read-only --list/--status must
not reset state, create markers, or start work.

Review records `reviewed_commit` and `plan_fingerprint` in review.md. Certify only
a clean feature worktree (including relevant untracked files); capture both before
review and confirm both still match afterward. Deliver compares both again and
requires complete task progress. The detecting phase owns the return: commit/dirty-code change sets status=verifying; a non-semantic plan-only fingerprint change or missing legacy review metadata sets status=reviewing; a semantic plan change must go through --update and revoke approval. Report the reason before handing off; never recertify by merely editing the
stored hash/SHA. Formatting-only plan edits may be rechecked by review without
revoking human design approval, but old review evidence must be refreshed.

Persist `pr: <url>` in proposal at delivery. It is durable identity across update,
re-review, and finalize; session markers are only local backstops. Reuse the same
open PR after revalidation, never reopen a merged or closed-unmerged PR blindly.

Read `update-flow.md` for edits to existing plans and failure returns. For projects
that opted into canonical specs, read `../../sdd-deliver/references/spec-sync.md`
before proposal authoring so the baseline is captured before changing code.
