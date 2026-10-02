---
name: sdd-verify
description: >-
  Run the applicable CI ladder and gap-filling tests for an implemented SDD change in its feature worktree. Record evidence, distinguish Not verified from N/A, and hand passing work to sdd-review. Checks removals and renames according to their delta semantics; skip_specs still requires task and regression evidence. Triggers: sdd verify, run CI, 跑 CI, 驗這張票.
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
> 5. **Zero extra footprint.** New code files are only gap-filling tests in the target repo's test tree; the vault receives verification.md and phase/task metadata only.

## Triggers

- `/sdd-verify <project> <ticket>` — explicit
- `/sdd-verify` (no args) — infer from conversation / cwd; if ambiguous, `--list` and ask
- `/sdd-verify --list` — list changes with `status: verifying` (apply done, green), then stop
- Natural language: "verify this SDD", "run CI", "sdd verify", "跑 CI", "驗這張票"

---

## Flow

Let `VAULT_ROOT = {base_url}` — resolve `{base_url}` via `rules/00-machine-paths.md` before passing any path to a tool.

Read `.claude/skills/sdd-propose/references/planning-contract.md` on entry for artifact applicability, shared validation/task parsing, review freshness, and durable PR identity. Its `skip_specs` exception applies wherever this skill says four-pack/specs. Read-only list/status modes do not advance work. For backward transitions or plan edits, use that reference's `update-flow.md`; do not bypass phase ownership.

### Step 0 — Locate the change, repo, and feature branch

1. **PROJECT + ticket**: from `$ARGUMENTS` / conversation / cwd; if unsure → `AskUserQuestion`.
2. **SDD folder** = `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`. Run `validate_sdd.py <folder> --mode ready`, read applicable artifacts and proposal frontmatter.
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

For genuinely non-code tasks with explicit document/link/config validation, use those commands without requiring a language manifest or test framework. Mark inapplicable code checks N/A with reasons. Missing tools for an applicable check still block; a refactor is code work and needs regression tests.

Same detection as apply (`sdd-apply/references/apply-loop.md`): read the target repo's `CLAUDE.md` / `AGENTS.md` for the test + typecheck + lint commands; fall back to the manifest (Python → `uv run mypy` + `uv run pytest`; Node/TS → the `package.json` scripts; Go → `go vet` + `go test ./...`; Rust → `cargo clippy` + `cargo test`). Undetectable → pause and ask.

### Step 3 — Deterministic CI (strongest judge, no LLM)

Run each ladder rung the tier demands, **in the feature worktree**, bottom-up:

1. **lint / format / typecheck** — must pass clean.
2. **unit** → **integration** → **e2e** as the tier requires.
3. **e2e-live** (only for `e2e-live`): start the service locally (per the repo's run command, in tmux for log access), then drive LLM e2e against it; tear it down after.

Any rung red → **stop and report** (max 3 focused retries per the global rule, then hand back). Do not proceed to Step 4 on red.

### Step 4 — LLM gap-filling tests

With the deterministic suite green, look for **behavior the existing tests don't cover** but the specs require:

- Use `sdd-review/references/verify-rubric.md`: test ADDED/MODIFIED scenarios, prove REMOVED behavior is gone and RENAMED behavior preserved. Do not recreate tests expecting removed behavior. With skip_specs, check task outcomes and regression evidence for unchanged behavior.
- Add tests only for genuinely uncovered scenarios / edge cases (empty, null, boundary, failure path), in the repo's own framework and test tree.
- Run them; they must pass. A new test that fails reveals either a real bug (→ report, this is a red result) or a spec gap (→ `/sdd-propose --update`; do not patch around it). For a code bug against the unchanged plan, record status=applying and reopen the affected task, then hand off to `/sdd-apply` using update-flow.md.

### Step 5 — Coverage judgment (rubric, not a bare yes/no)

Record Passed / Failed / Not verified / N/A for checks, with reasons and commands. N/A is only for genuinely inapplicable checks (e.g. code coverage for docs-only work); missing tools/evidence is Not verified. Judge applicable coverage against the rubric in `references/ci-ladder.md` (are the spec's critical paths, error paths, and boundaries all exercised?), and against the numeric threshold — the repo's `CLAUDE.md` value, else the global `~/.claude/rules/common/testing.md` default (**80%**). Below threshold → add tests for the uncovered branches (back to Step 4) or, if truly untestable, report why.

### Step 6 — Handoff

When the tier's full ladder is green and coverage passes:

- Write `verification.md` in the change folder with commands/results, applicable rung outcomes, coverage or justified N/A, and unresolved evidence. This report is an evidence companion, not a planning prerequisite. Only then bump status `verifying → reviewing` if every required check passed; missing evidence does not advance.
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
- Gap-filling tests live in the target repo's test tree; verification evidence lives in the change's verification.md.
- **Every subagent this skill spawns gets an explicit `model` — never inherit.** Default `sonnet`; `haiku` for purely mechanical steps (running a command, collecting output); `opus` only for the coverage-rubric judgement if it is delegated at all. The parent session may be on a premium tier; the phase work must not ride on it.
- English content in artifacts; converse in the user's language.

## Edge cases

| Situation                         | Handling                                                                                                |
| --------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `status` not `verifying`          | Refuse; tell the user which stage is still pending                                                      |
| Feature branch/worktree missing   | Recreate the worktree from `sdd/<ticket>`; if the branch itself is gone, apply never completed → refuse |
| Deterministic rung red            | Stop, report the failing rung + output; don't run higher rungs, don't proceed to review                 |
| Gap-filling test fails = real bug | Record red, set applying, reopen affected task and hand back to apply; don't mask it                                                    |
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
