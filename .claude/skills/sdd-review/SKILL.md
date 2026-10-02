---
name: sdd-review
description: >-
  Review an SDD implementation against its plan without editing application code. Check added, modified, removed and renamed requirements, or task outcomes for skip_specs; combine code review with evidence states. Record reviewed commit and plan fingerprint, and advance only when required checks pass. Triggers: sdd review, review this SDD, spec review, 審這張票.
argument-hint: "[<project>] [<ticket>] [--list]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, TodoWrite, Agent
model: inherit
---

# sdd-review

**This is a task command, not reference material. Once you've read it, start executing from Step 0.**

The Stage 4 gate: does the CI-green change actually satisfy the spec it was built from? Review is **read-only on target code** — it judges and reports, it does not edit application code. Its job is to close the loop between `specs/` and the implementation, and to surface anything a human should see before merging the PR.

> [!important] Red lines (violate → stop)
>
> 1. **Read-only on target code.** Review never edits application code. It may write the review artifact and phase/task metadata for an explicit repair return — in the vault SDD folder, not the repo.
> 2. **Clean session, feature branch only.** Run on `sdd/<ticket>`; never the developer's main tree; carry no apply/CI implementation context.
> 3. **Every acceptance criterion is checked one by one.** An unchecked criterion blocks status `verified` (skill-internal logic — the gate hooks are not extended for this).
> 4. **Findings inform, they don't block the flow.** No synchronous human step; CRITICAL/WARNING/SUGGESTION go into the PR draft for a human to weigh before merge. (A CRITICAL that means a criterion is unmet does block `verified` — via rule 3, not by halting.)
> 5. **Don't rubber-stamp.** If the spec and code disagree, the finding is real; say so.

## Triggers

- `/sdd-review <project> <ticket>` — explicit
- `/sdd-review` (no args) — infer from conversation / cwd; if ambiguous, `--list` and ask
- `/sdd-review --list` — list changes with `status: reviewing` (CI green), then stop
- Natural language: "review this SDD", "spec review", "sdd review", "複驗這張票"

---

## Flow

Let `VAULT_ROOT = {base_url}` — resolve `{base_url}` via `rules/00-machine-paths.md` before passing any path to a tool.

Read `.claude/skills/sdd-propose/references/planning-contract.md` on entry for artifact applicability, shared validation/task parsing, review freshness, and durable PR identity. Its `skip_specs` exception applies wherever this skill says four-pack/specs. Read-only list/status modes do not advance work. For backward transitions or plan edits, use that reference's `update-flow.md`; do not bypass phase ownership.

### Step 0 — Locate the change, repo, and feature branch

1. **PROJECT + ticket**: from `$ARGUMENTS` / conversation / cwd; if unsure → `AskUserQuestion`.
2. **SDD folder** = `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`. Run ready validation and read all applicable planning inputs plus verification.md when available. Old tickets without that report need equivalent command/test evidence; its absence alone is not permission to assume CI passed.
3. **Gate on status**: proceed only if `status: reviewing` (CI passed). Otherwise say what's still pending (`verifying` → CI not done) and stop.
4. **repo_path** via `repo-router`; **feature branch** = `sdd/<ticket>`, find/attach its worktree (same as `sdd-verify` Step 0). Review reads code here.
5. `--list`: Glob proposals with `status: reviewing`, print them, then **stop**.

### Step 1 — Self-built verify pass (spec ↔ change)

Compare the diff on `sdd/<ticket>` against `specs/<capability>.md` on the three axes (see `references/verify-rubric.md`):

- **Completeness** — inspect each delta operation using `references/verify-rubric.md`: added/modified behavior exists, removed behavior is gone, renamed behavior is preserved. With `skip_specs: true`, use task outcomes instead.
- **Correctness** — ADDED/MODIFIED scenarios match implementation and tests. Removal/rename-only changes use operation checks; they do not require new-behavior scenarios.
- **Coherence** — the change is internally consistent and consistent with the design (`design.md`) and the repo's conventions; no contradictory or dead paths.

Record findings as `CRITICAL` (spec violated / requirement unmet), `WARNING` (risky or ambiguous), `SUGGESTION` (improvement, non-blocking).

### Step 2 — Read-only code review

Invoke the `code-reviewer` skill (report-only; it size-gates the diff itself) scoped to the diff on `sdd/<ticket>`. Its workflow pins its own per-agent models (scout/lenses on `sonnet`, refute-verify on `opus`); do not override them upward. Fold its findings into the same CRITICAL/WARNING/SUGGESTION buckets. This is quality/security/maintainability review, complementary to the spec check in Step 1.

### Step 3 — Re-check acceptance criteria, one by one

Use the operation-aware criteria in `references/verify-rubric.md`. Walk ADDED/MODIFIED scenarios, REMOVED/RENAMED operation checks, or task outcomes when specs are intentionally skipped. Record Passed / Failed / Not verified (reason) / Not applicable (reason):

- For every applicable criterion, require the evidence specified by the rubric; only Passed is checked. N/A is excluded, not counted as passed.
- Contradictory behavior is Failed + CRITICAL. Missing/unusable evidence is Not verified; do not claim the check passed.

**Any Failed or Not verified required criterion blocks status `verified`** (Step 5). This is the load-bearing rule of Stage 4, enforced in-skill.

### Step 4 — Write the PR-description draft

Capture feature HEAD and plan fingerprint before review; recheck both and worktree cleanliness at the end, restarting affected checks if they changed. Write `review.md` in the SDD folder (vault, not the repo) — the basis for the delivery PR body (M6). Include:

- One-line outcome + the evidence-state checklist (including reasons for Not verified/N/A).
- Frontmatter `reviewed_commit` (feature HEAD), `plan_fingerprint` from `validate_sdd.py <folder> --mode ready --fingerprint`, and `type: review`. Review a clean worktree: if implementation/tests are uncommitted, obtain the necessary commit under the repo policy before certifying a commit. Do not manufacture a reviewed SHA for a dirty tree.
- CRITICAL / WARNING / SUGGESTION findings, each with file:line and why.
- A "before merge, a human should look at" list (the WARNINGs + any judgment calls).

Follow the vault PR template shape (`~/.claude/rules/common/git-workflow.md`): Background / What's Changed / Reference / Test Plan.

### Step 5 — Handoff

- **All required criteria Passed, remaining checks explicitly N/A, and no open CRITICAL** → bump `proposal.md` `status`: `reviewing → verified`; report "ready for delivery (M6)"; point to `review.md`.
- **Any required Failed/Not verified criterion or open CRITICAL** → keep `status: reviewing`; report exactly which criteria are unmet and why; do **not** advance. (Use update-flow.md: code defects set applying and reopen affected tasks; missing test evidence sets verifying; plan defects go through --update. Preserve blockers in review.md; do not edit application code from review.)
- WARNINGs/SUGGESTIONs never block; they ride along in `review.md` for the human at merge time.

---

## Guardrails

- Read-only on target code; writes are limited to vault review evidence and explicit phase/task repair metadata.
- Clean session, feature-branch worktree; never the main tree.
- Every applicable acceptance criterion checked individually; Failed/Not verified → blocks `verified`; N/A does not.
- Findings inform the human via the PR draft; they don't halt the pipeline (except an unmet criterion, which blocks `verified` by rule).
- Don't rubber-stamp; a real spec/code disagreement is a CRITICAL.
- **Every subagent this skill spawns gets an explicit `model` — never inherit.** Default `sonnet` for reading and collecting evidence; `opus` for the per-criterion judgement and the Completeness/Correctness/Coherence pass if delegated. The parent session may be on a premium tier; the phase work must not ride on it.
- English content in artifacts; converse in the user's language.

## Edge cases

| Situation                                                          | Handling                                                                                                              |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `status` not `reviewing`                                           | Refuse; tell the user CI (`sdd-verify`) hasn't passed yet                                                             |
| A criterion has a test but behavior still contradicts the spec     | Unchecked + CRITICAL; blocks `verified`                                                                               |
| The `code-reviewer` skill flags a blocking issue not tied to a criterion | Preserve its blocking effect; do not downgrade it merely because no scenario names it |
| Spec itself looks wrong                                            | Pause; suggest updating the SDD via `sdd-propose`; don't check a criterion you don't believe                          |
| Reviewer wants to fix code                                         | Not allowed here; report the fix as a finding, hand back to apply/verify                                              |
| No ADDED/MODIFIED scenarios | Valid removal/rename-only deltas use operation checks; explicit skip_specs uses task checks. Otherwise missing evidence is Not verified |

## Further Reading

- `references/verify-rubric.md` — the Completeness / Correctness / Coherence rubric + severity mapping
- `.claude/skills/sdd-verify/SKILL.md` — Stage 3 CI, the prerequisite (must be green first)
- `.claude/scripts/validate_sdd.py` — status validation
- [[Agentic Coding Harness 實作計劃]] — where M5 sits in the overall pipeline
- [[Coding Conventions]] — the standards the code review applies
