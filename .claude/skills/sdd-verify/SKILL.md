---
name: sdd-verify
description: Spec-Driven Development, Stage 3. The CI subagent that runs on the feature branch after apply is green. Verifies the change to the depth set by the proposal's `propose_tier` (lint → unit → integration → e2e → live-service e2e). Three judges, strongest first — deterministic CI (typecheck + tests, no LLM), then LLM-designed gap-filling tests, then a coverage-rubric judgment. Runs in a CLEAN session in the apply feature branch's worktree (`sdd/<ticket>`), never the developer's main tree. On green, bumps `proposal.md` status `verifying → reviewing` and hands off to `sdd-review`. Triggers: "verify this SDD", "run CI", "sdd verify", "跑 CI / 驗這張票", `/sdd-verify`; `--list` = show changes ready to verify.
argument-hint: "[<project>] [<ticket>] [--list]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, TodoWrite
model: inherit
---

# sdd-verify

**This is a task command, not reference material. Once you've read it, start executing from Step 0.**

The Stage 3 CI gate: prove the applied change actually works, to the depth the whole-ticket difficulty (`propose_tier`) demands. Deterministic checks are the strongest judge and run first; the LLM only fills gaps and judges coverage against a rubric — it never overrides a red deterministic result.

> [!important] Red lines (violate → stop)
>
> 1. **Deterministic first, LLM never overrides red.** If typecheck/tests fail, the change is red — no amount of LLM reasoning turns that green.
> 2. **Clean session, feature branch only.** Run in the apply feature branch's worktree (`sdd/<ticket>`), never the developer's main working tree. This skill does not carry apply's implementation context.
> 3. **Never weaken a check to pass.** No `--no-verify`, no skipped/xfail'd tests, no lowered coverage threshold to force green. Red is diagnosed, not silenced.
> 4. **Depth = `propose_tier`.** Don't run shallower than the tier demands; don't gold-plate past it either.
> 5. **Zero extra footprint.** Gap-filling tests are the only new files, and they live in the target repo's own test tree — nothing in the vault, nothing outside the repo's conventions.

## Triggers

- `/sdd-verify <project> <ticket>` — explicit
- `/sdd-verify` (no args) — infer from conversation / cwd; if ambiguous, `--list` and ask
- `/sdd-verify --list` — list changes with `status: verifying` (apply done, green), then stop
- Natural language: "verify this SDD", "run CI", "sdd verify", "跑 CI", "驗這張票"

---

## Flow

Let `VAULT_ROOT = {base_url}` — resolve `{base_url}` via `rules/00-machine-paths.md` before passing any path to a tool.

### Step 0 — Locate the change, repo, and feature branch

1. **PROJECT + ticket**: from `$ARGUMENTS` / conversation / cwd; if unsure → `AskUserQuestion`.
2. **SDD folder** = `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`. Confirm the four-pack is complete and read `proposal.md` frontmatter.
3. **Gate on status**: proceed only if `status: verifying` (apply finished green). Otherwise tell the user what's still pending (`applying` → apply not done; `proposed`/`approved` → not applied yet) and stop.
4. **repo_path**: resolve via `repo-router`'s `repos.yaml` (`vault_project == <PROJECT>`). No mapping → pause and ask.
5. **Feature branch + worktree**: derive the branch as `sdd/<ticket>` (apply's convention — this skill does NOT depend on the session marker). Find its worktree with `git -C "<repo_path>" worktree list`. If none exists, add one: `git -C "<repo_path>" worktree add "<wt_feat>" sdd/<ticket>`. **All CI runs happen inside this worktree.**
6. `--list`: Glob `01 Work/projects/*/SDD/*/proposal.md`, print those with `status: verifying`, then **stop**.

### Step 1 — Read the depth (`propose_tier`)

Read `propose_tier` from `proposal.md`. It picks the CI ladder depth (see `references/ci-ladder.md`):

| `propose_tier` | Ladder depth                                             |
| -------------- | -------------------------------------------------------- |
| `lint`         | lint / format / typecheck only                           |
| `unit`         | + unit tests                                             |
| `integration`  | + integration tests (DB, cross-module)                   |
| `e2e`          | + end-to-end (headless)                                  |
| `e2e-live`     | + spin up the service locally, LLM-driven e2e against it |

Each rung **includes all rungs below it**. Track the rungs as a TodoWrite checklist.

### Step 2 — Detect the stack (from the target repo, never assume)

Same detection as apply (`sdd-apply/references/apply-loop.md`): read the target repo's `CLAUDE.md` / `AGENTS.md` for the test + typecheck + lint commands; fall back to the manifest (Python → `uv run mypy` + `uv run pytest`; Node/TS → the `package.json` scripts; Go → `go vet` + `go test ./...`; Rust → `cargo clippy` + `cargo test`). Undetectable → pause and ask.

### Step 3 — Deterministic CI (strongest judge, no LLM)

Run each ladder rung the tier demands, **in the feature worktree**, bottom-up:

1. **lint / format / typecheck** — must pass clean.
2. **unit** → **integration** → **e2e** as the tier requires.
3. **e2e-live** (only for `e2e-live`): start the service locally (per the repo's run command, in tmux for log access), then drive LLM e2e against it; tear it down after.

Any rung red → **stop and report** (max 3 focused retries per the global rule, then hand back). Do not proceed to Step 4 on red.

### Step 4 — LLM gap-filling tests

With the deterministic suite green, look for **behavior the existing tests don't cover** but the specs require:

- Re-read each `specs/<capability>.md` scenario (WHEN/THEN) and check a test exercises it.
- Add tests only for genuinely uncovered scenarios / edge cases (empty, null, boundary, failure path), in the repo's own framework and test tree.
- Run them; they must pass. A new test that fails reveals either a real bug (→ report, this is a red result) or a spec gap (→ pause, suggest updating the SDD via `sdd-propose` — don't patch around it).

### Step 5 — Coverage judgment (rubric, not a bare yes/no)

Judge coverage against the rubric in `references/ci-ladder.md` (are the spec's critical paths, error paths, and boundaries all exercised?), and against the numeric threshold — the repo's `CLAUDE.md` value, else the global `~/.claude/rules/common/testing.md` default (**80%**). Below threshold → add tests for the uncovered branches (back to Step 4) or, if truly untestable, report why.

### Step 6 — Handoff

When the tier's full ladder is green and coverage passes:

- Bump `proposal.md` `status`: `verifying → reviewing`.
- Report: rungs run (with the tier that set them), gap-filling tests added, coverage figure, and "ready for review (`sdd-review`)".
- Offer to commit the gap-filling tests **on the feature branch** (`sdd/<ticket>`), add only the test files this run touched (**never `git add -A`**, **never merge to `main`**):
  ```
  CI green for <ticket> at tier <propose_tier>. Commit the added tests on sdd/<ticket>?
  Suggested: `test(<project-slug>): CI gap-filling tests for <ticket>`
  ```

---

## Guardrails

- Deterministic checks are the authority; the LLM fills gaps and judges the rubric, never overturns a red run.
- Run exactly to `propose_tier` depth — no shallower, no gold-plating.
- Clean session, feature-branch worktree only; never the main tree; never merge to main.
- Never weaken a check to force green. Max 3 consecutive failures on the same rung → stop and report (global max-retries-3).
- Gap-filling tests live in the target repo's test tree; no vault or out-of-repo footprint.
- English content in artifacts; converse in the user's language.

## Edge cases

| Situation                         | Handling                                                                                                |
| --------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `status` not `verifying`          | Refuse; tell the user which stage is still pending                                                      |
| Feature branch/worktree missing   | Recreate the worktree from `sdd/<ticket>`; if the branch itself is gone, apply never completed → refuse |
| Deterministic rung red            | Stop, report the failing rung + output; don't run higher rungs, don't proceed to review                 |
| Gap-filling test fails = real bug | Report as a red result; back to apply, don't mask it                                                    |
| Gap-filling test fails = spec gap | Pause; suggest updating the SDD via `sdd-propose`; don't patch around the spec                          |
| Coverage below threshold          | Add tests for uncovered branches; if untestable, report why, don't lower the threshold                  |
| Stack undetectable                | Pause and ask (never assume a framework)                                                                |
| `e2e-live` service won't start    | Report the startup failure; that is a red result                                                        |

## Further Reading

- `references/ci-ladder.md` — the CI ladder per tier + the coverage rubric + stack detection
- `.claude/skills/sdd-apply/references/apply-loop.md` — shared stack-detection logic
- `.claude/skills/sdd-review/SKILL.md` — Stage 4, the next step after CI is green
- `.claude/scripts/validate_sdd.py` — status/tier validation
- [[Agentic Coding Harness 實作計劃]] — where M5 sits in the overall pipeline
