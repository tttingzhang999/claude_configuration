---
name: sdd-review
description: Spec-Driven Development, Stage 4. The review subagent that checks the CI-green change against the spec, read-only. Runs a self-built verify pass (Completeness / Correctness / Coherence, ported from OpenSpec verify → CRITICAL/WARNING/SUGGESTION) plus a read-only `code-reviewer`, then re-checks every acceptance criterion in `specs/<capability>.md` one by one. Any unchecked criterion blocks "done" (skill-internal, not a gate hook). Findings never block the flow — they go into a PR-description draft for a human to read before merge. Runs in a CLEAN session on the feature branch (`sdd/<ticket>`), edits nothing in the target repo. On a clean pass, bumps `proposal.md` status `reviewing → verified` and hands off to delivery (M6). Triggers: "review this SDD", "spec review", "sdd review", "複驗這張票", `/sdd-review`; `--list` = show changes ready to review.
argument-hint: "[<project>] [<ticket>] [--list]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, TodoWrite, Agent
model: inherit
---

# sdd-review

**This is a task command, not reference material. Once you've read it, start executing from Step 0.**

The Stage 4 gate: does the CI-green change actually satisfy the spec it was built from? Review is **read-only on target code** — it judges and reports, it does not edit application code. Its job is to close the loop between `specs/` and the implementation, and to surface anything a human should see before merging the PR.

> [!important] Red lines (violate → stop)
>
> 1. **Read-only on target code.** Review never edits application code. It may only write the review artifact (a PR-description draft) — in the vault SDD folder, not the repo.
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

### Step 0 — Locate the change, repo, and feature branch

1. **PROJECT + ticket**: from `$ARGUMENTS` / conversation / cwd; if unsure → `AskUserQuestion`.
2. **SDD folder** = `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`. Read the four-pack.
3. **Gate on status**: proceed only if `status: reviewing` (CI passed). Otherwise say what's still pending (`verifying` → CI not done) and stop.
4. **repo_path** via `repo-router`; **feature branch** = `sdd/<ticket>`, find/attach its worktree (same as `sdd-verify` Step 0). Review reads code here.
5. `--list`: Glob proposals with `status: reviewing`, print them, then **stop**.

### Step 1 — Self-built verify pass (spec ↔ change)

Compare the diff on `sdd/<ticket>` against `specs/<capability>.md` on the three axes (see `references/verify-rubric.md`):

- **Completeness** — every requirement / scenario in the spec has corresponding implemented behavior. Nothing promised is missing.
- **Correctness** — the implementation does what each scenario's WHEN/THEN says; no behavior contradicts a SHALL/MUST.
- **Coherence** — the change is internally consistent and consistent with the design (`design.md`) and the repo's conventions; no contradictory or dead paths.

Record findings as `CRITICAL` (spec violated / requirement unmet), `WARNING` (risky or ambiguous), `SUGGESTION` (improvement, non-blocking).

### Step 2 — Read-only code review

Invoke the `code-reviewer` skill (report-only; it size-gates the diff itself) scoped to the diff on `sdd/<ticket>`. Fold its findings into the same CRITICAL/WARNING/SUGGESTION buckets. This is quality/security/maintainability review, complementary to the spec check in Step 1.

### Step 3 — Re-check acceptance criteria, one by one

The spec's `#### Scenario:` blocks are the acceptance criteria. Walk **each one** with TodoWrite:

- For every scenario, confirm a test exercises it (from `sdd-verify`) **and** the behavior matches → check it.
- A scenario with no covering behavior/test, or behavior that contradicts it → leave unchecked and log a CRITICAL.

**Any unchecked criterion blocks status `verified`** (Step 5). This is the load-bearing rule of Stage 4, enforced in-skill.

### Step 4 — Write the PR-description draft

Write `review.md` in the SDD folder (vault, not the repo) — the basis for the delivery PR body (M6). Include:

- One-line outcome + the criteria checklist (checked / unchecked).
- CRITICAL / WARNING / SUGGESTION findings, each with file:line and why.
- A "before merge, a human should look at" list (the WARNINGs + any judgment calls).

Follow the vault PR template shape (`~/.claude/rules/common/git-workflow.md`): Background / What's Changed / Reference / Test Plan.

### Step 5 — Handoff

- **All criteria checked and no open CRITICAL** → bump `proposal.md` `status`: `reviewing → verified`; report "ready for delivery (M6)"; point to `review.md`.
- **Any unchecked criterion or open CRITICAL** → keep `status: reviewing`; report exactly which criteria are unmet and why; do **not** advance. (Fixing them means going back to `sdd-apply` / `sdd-verify`, not editing from here.)
- WARNINGs/SUGGESTIONs never block; they ride along in `review.md` for the human at merge time.

---

## Guardrails

- Read-only on target code; the only write is the vault review artifact.
- Clean session, feature-branch worktree; never the main tree.
- Every acceptance criterion checked individually; unchecked → blocks `verified`.
- Findings inform the human via the PR draft; they don't halt the pipeline (except an unmet criterion, which blocks `verified` by rule).
- Don't rubber-stamp; a real spec/code disagreement is a CRITICAL.
- English content in artifacts; converse in the user's language.

## Edge cases

| Situation                                                          | Handling                                                                                                              |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `status` not `reviewing`                                           | Refuse; tell the user CI (`sdd-verify`) hasn't passed yet                                                             |
| A criterion has a test but behavior still contradicts the spec     | Unchecked + CRITICAL; blocks `verified`                                                                               |
| The `code-reviewer` skill flags a CRITICAL not tied to a criterion | Log it; if it means a SHALL is violated it's a Completeness/Correctness CRITICAL (blocks); else WARNING for the human |
| Spec itself looks wrong                                            | Pause; suggest updating the SDD via `sdd-propose`; don't check a criterion you don't believe                          |
| Reviewer wants to fix code                                         | Not allowed here; report the fix as a finding, hand back to apply/verify                                              |
| No `specs/` scenarios to check against                             | Refuse; the four-pack is incomplete — back to `sdd-propose`                                                           |

## Further Reading

- `references/verify-rubric.md` — the Completeness / Correctness / Coherence rubric + severity mapping
- `.claude/skills/sdd-verify/SKILL.md` — Stage 3 CI, the prerequisite (must be green first)
- `.claude/scripts/validate_sdd.py` — status validation
- [[Agentic Coding Harness 實作計劃]] — where M5 sits in the overall pipeline
- [[Coding Conventions]] — the standards the code review applies
