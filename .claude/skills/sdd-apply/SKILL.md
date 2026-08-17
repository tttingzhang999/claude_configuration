---
name: sdd-apply
description: Spec-Driven Development, Stage 2. The apply orchestrator that turns a design-approved SDD four-pack into implemented, test-first code. Reads `tasks.md` from `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`, and runs each task as its own subagent using that task's task tier (`sonnet|opus`) as the model. Each task is test-first (RED → GREEN → refactor → coverage), following `references/apply-loop.md` with the test stack taken from the target repo's CLAUDE.md (language-agnostic). Groups run in parallel, each isolated in its own git worktree, then merged onto a feature branch `sdd/<ticket>` (never `main` — that waits for the remote PR merge). Arms a per-session marker `~/.claude/sdd-active-<session_id>` so the gate hooks enforce "no stopping on red" (and a backstop "no main-tree code before design sign-off"). Only runs when the proposal's `design_approved: true`. Triggers: "apply this SDD", "implement the tasks", "run apply", "sdd apply", "開始實作 / 跑 apply", `/sdd-apply`; `--list` = show applyable changes.
argument-hint: "[<project>] [<ticket>] [--list]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, TodoWrite, Agent
model: inherit
---

# sdd-apply

**This is a task command, not reference material. Once you've read it, start executing from Step 0.**

The Stage 2 orchestrator: implement a design-approved SDD four-pack, one task at a time, test-first, with each task run by a subagent on its own task tier. Hand off to M5 (CI/Review) when green.

> [!important] Red lines (violate → stop)
>
> 1. **Only run when `design_approved: true`.** If the proposal isn't signed off, arm the gate and refuse (Step 1). Getting sign-off is a human action.
> 2. **Subagents edit only the target repo (`repo_path`).** They never write vault SDD artifacts or other vault files. The orchestrator owns the vault (checkboxes, status).
> 3. **Never bypass to force green.** No `--no-verify`, no skipping/weakening tests. Red is diagnosed, not silenced (max 3 consecutive failures → stop and report).
> 4. **Zero extra footprint.** No file is created in the target repo beyond the code the tasks require. The session marker lives in `~/.claude/` (machine-local), never in the repo or vault git.

## Triggers

- `/sdd-apply <project> <ticket>` — explicit
- `/sdd-apply` (no args) — infer from conversation / cwd; if ambiguous, `--list` and ask
- `/sdd-apply --list` — list applyable changes (four-pack complete, `design_approved: true`), then stop
- Natural language: "apply this SDD", "implement the tasks", "run apply", "開始實作", "跑 apply", "sdd apply"

## The session marker (gate contract)

`~/.claude/sdd-active-$CLAUDE_CODE_SESSION_ID` — machine-local, **key=value** (bash-parseable, no JSON). The two gate hooks (`sdd-gate-pretooluse.sh`, `sdd-gate-stop.sh`) read the marker belonging to the session they fire in; **no marker → hooks no-op**, so ordinary sessions are never affected. This skill **owns its whole lifecycle**:

```
sdd_path=<abs path to the SDD folder>
ticket=<ticket>
design_approved=<true|false>
repo_path=<abs path to the target repo>
feature_branch=<sdd/<ticket>, the branch apply integrates onto — never main>
tests_green=<true|false|empty>
```

`feature_branch` is an informational handoff field (not read by the gate hooks — the gate stays on `tests_green` only). M5 (`sdd-verify` / `sdd-review`) runs in a **clean session** and re-derives the branch as `sdd/<ticket>` from the SDD folder, so it never depends on this marker.

**The path is per session — always suffix it with `$CLAUDE_CODE_SESSION_ID`** (the env var is set in every Bash call; apply subagents inherit the parent session id, so their tool calls hit the same marker). Never write the bare `~/.claude/sdd-active`: several SDD sessions run concurrently on this machine, and a shared path means one run silently overwrites another's gate — or `sed`s `tests_green` onto a different ticket's marker.

- **Arm** on entry (Step 1/3), **update** `tests_green` after each task's test run (Step 4), **disarm** (`rm`) on clean completion (Step 5).
- Write it with a plain heredoc (`cat > ~/.claude/sdd-active-$CLAUDE_CODE_SESSION_ID <<EOF … EOF`). Update a single field with `sed`/rewrite. Manual disarm for the user: `rm ~/.claude/sdd-active-<session_id>` (the gate messages print the exact path).

---

## Flow

Let `VAULT_ROOT = {base_url}` — resolve `{base_url}` via `rules/00-machine-paths.md` before passing any path to a tool.

### Step 0 — Locate the change + the repo

1. **PROJECT + ticket**: from `$ARGUMENTS` / conversation / cwd; if unsure → `AskUserQuestion`.
2. **SDD folder** = `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`. Confirm the four-pack is complete (`proposal.md`, `specs/` ≥1, `design.md`, `tasks.md`); if not → tell the user to finish it with `sdd-propose`, stop.
3. **repo_path**: resolve the real target repo via `repo-router`'s `repos.yaml` (`vault_project == <PROJECT>`). No mapping → **pause and ask** for the repo path (apply must edit real code; don't guess).
4. `--list`: Glob `01 Work/projects/*/SDD/*/proposal.md`, Read frontmatter, print those with all four files present + `design_approved: true`, then **stop**.

### Step 1 — Gate check (read `design_approved`)

Read `proposal.md` frontmatter `design_approved`:

- **`true`** → proceed to Step 2.
- **not `true`** → **arm the marker unapproved** and refuse:
  ```bash
  cat > ~/.claude/sdd-active-$CLAUDE_CODE_SESSION_ID <<EOF
  sdd_path=<abs SDD folder>
  ticket=<ticket>
  design_approved=false
  repo_path=<repo_path>
  feature_branch=
  tests_green=
  EOF
  ```
  Tell the user: "Design isn't signed off. The gate now blocks code edits under `<repo_path>` until you set `design_approved: true` in the proposal, then re-run sdd-apply. (Disarm: `rm ~/.claude/sdd-active-<session_id>`.)" **Stop.**

### Step 2 — Load context + parse tasks

- Read the four-pack: `proposal.md`, every `specs/*.md`, `design.md`, `tasks.md`.
- Read the target repo's `CLAUDE.md` (fallback manifests) for the test stack — pass this to every subagent.
- Parse `tasks.md` into an ordered list: each `- [ ] N.M \`[tier]\` <description>`→`{id, tier, text, done}`. Track them with **TodoWrite**.
- If any task lacks a task tier → run `validate_sdd.py` to confirm; fix in the SDD (via sdd-propose) before applying.

### Step 3 — Arm the marker (approved) + bump status

```bash
cat > ~/.claude/sdd-active-$CLAUDE_CODE_SESSION_ID <<EOF
sdd_path=<abs SDD folder>
ticket=<ticket>
design_approved=true
repo_path=<repo_path>
feature_branch=sdd/<ticket>
tests_green=
EOF
```

Bump `proposal.md` `status`: `approved → applying` (if it was `proposed`, note the human just approved it).

### Step 4 — Implement tasks (per-task subagents, worktree per group, parallel across groups)

**Concurrency model:**

- Each `## N` group is one unit; its tasks are **serial within the group** (RED → GREEN → run share state).
- **Groups are independent → run in parallel**, each isolated in **its own git worktree** so concurrent edits never collide.
- Each **task** is one subagent whose model = **that task's task tier**; a group's tasks all operate in that group's worktree. (Verified: the `Agent` tool supports parallel spawning and git-worktree isolation.)
- **Never touch the developer's main working tree.** All integration lands on a dedicated **feature branch `sdd/<ticket>`**, verified there by M5, and only reaches `main` when the **remote PR is merged** (the human's final button, post-M6) — not by this skill.

**Setup (orchestrator, Bash):**

- Confirm `repo_path` is a git repo. If not → fall back to **serial on a feature branch checked out in a scratch worktree** (no per-group worktrees); still never the main tree. If even that is impossible, pause and ask.
- Create the feature branch off the current base **without checking it out in the main tree**: `git -C "<repo_path>" branch sdd/<ticket>` (base = current HEAD).
- Add the **integration worktree** for it: `git -C "<repo_path>" worktree add "<wt_feat>" sdd/<ticket>`.
- For each group N, branch **off the feature branch**: `git -C "<repo_path>" worktree add "<wt_N>" -b sdd/<ticket>-g<N> sdd/<ticket>`. (Use the **sibling** name `sdd/<ticket>-g<N>`, not `sdd/<ticket>/g<N>` — the latter collides with the feature branch ref `sdd/<ticket>` as a git D/F conflict and fails.)

**Run (advance groups concurrently, one task per group at a time):**

1. Launch the current task of every still-running group as **parallel `Agent` calls in a single message** — each with `model` = that task's tier, prompt = the task text + the relevant spec scenario(s) + **its group's worktree path** + the detected test stack + "follow `references/apply-loop.md`; edit only within this worktree." Each returns a compact result (files touched, RED-then-GREEN confirmed, final **green/red**, coverage, any pause reason).
2. After the batch, the orchestrator runs each group's test command **in that group's worktree** to confirm:
   - **green** → mark that task `- [ ]` → `- [x]` in `tasks.md`; reset that group's failure counter; advance the group to its next task.
   - **red / paused** → set marker `tests_green=false`; don't mark done; retry the task once, else surface the pause reason. Increment the group's consecutive-failure counter — **≥ 3 → STOP**: leave `tests_green=false` (the Stop gate blocks a red finish), report each attempt + the blocker, and ask. Do not thrash. (A separate `build-error-resolver` is intentionally shelved — the task subagent already diagnoses and fixes within its own loop.)
3. Show progress per group: "g<N> task N.M ✓ (tier)".

**Integrate onto the feature branch (never main):**

- When a group is fully green, merge its branch into the **feature branch** from inside the integration worktree: `git -C "<wt_feat>" merge --no-ff sdd/<ticket>-g<N>`; on conflict, resolve serially (or report and pause). Then `git -C "<repo_path>" worktree remove "<wt_N>"`.
- After all groups merge, run the **full suite** inside `<wt_feat>` (the feature branch) → set marker `tests_green` accordingly.
- **Do not merge `sdd/<ticket>` into `main`.** The integration worktree `<wt_feat>` stays alive and is handed to M5 (`sdd-verify` / `sdd-review`), which run there. `main` is untouched until the remote PR merges.

### Step 5 — Completion + handoff

When every task is `- [x]` and the full suite is green on the feature branch:

- Update marker `tests_green=true`, then **disarm**: `rm ~/.claude/sdd-active-$CLAUDE_CODE_SESSION_ID`.
- Bump `proposal.md` `status`: `applying → verifying` (handoff to M5 CI/Review).
- **Leave the integration worktree `<wt_feat>` (branch `sdd/<ticket>`) in place** — M5 runs there. `main` stays untouched.
- Report: tasks completed, files touched, the feature branch `sdd/<ticket>` + its worktree path, the propose tier (which sets M5's CI depth), and "ready for verify (M5)".
- Offer to commit **on the feature branch** per the vault CLAUDE.md policy (add only the files this run touched; **never `git add -A`**; **never merge to `main` — that waits for the remote PR**):
  ```
  Apply complete for <ticket> on branch sdd/<ticket>. Commit there?
  Suggested: `feat(<project-slug>): implement <ticket> <title>`
  ```

---

## Guardrails

- Run only on `design_approved: true`; otherwise arm the gate and refuse.
- Subagents edit only inside `repo_path`; the orchestrator owns all vault writes (checkboxes, status, marker).
- Test-first every task; never edit a test to fit the code; never bypass a red light. Max 3 consecutive failures → stop and report (global max-retries-3).
- Keep the marker truthful at all times (`tests_green` reflects the last run); disarm on clean exit so the gate doesn't linger.
- No file added to the target repo beyond what the tasks require. Marker stays in `~/.claude/`.
- English content in artifacts; converse in the user's language.

## Edge cases

| Situation                                                   | Handling                                                                                                       |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Four-pack incomplete                                        | Refuse; point to `sdd-propose` to finish the chain                                                             |
| `design_approved` not true                                  | Arm the gate (unapproved) + refuse; tell user how to sign off                                                  |
| Repo not in repos.yaml                                      | Pause and ask for the repo path; don't guess                                                                   |
| `repo_path` is not a git repo                               | Pause and ask; apply needs a branch to integrate onto (never edits the main tree in place)                     |
| Merge conflict when merging a group onto the feature branch | Resolve serially in `<wt_feat>`, or pause and report; never force, never fall back to main                     |
| A stale marker already exists                               | Overwrite it for this change (this skill owns the marker); if it points elsewhere, warn the user first         |
| Subagent edits outside `repo_path`                          | Reject that result; the gate + this rule keep edits scoped                                                     |
| Test stack undetectable                                     | Pause and ask (never assume a framework)                                                                       |
| Task reveals a design flaw                                  | Stop, suggest updating the SDD via sdd-propose; don't patch around the spec                                    |
| Session ends mid-run with red tests                         | The Stop gate blocks it; either drive to green or `rm ~/.claude/sdd-active-$CLAUDE_CODE_SESSION_ID` to abandon |

## Further Reading

- `references/apply-loop.md` — the per-task language-agnostic TDD cycle + pause conditions
- `.claude/hooks/sdd-gate-pretooluse.sh` / `sdd-gate-stop.sh` — the gate hooks this skill arms
- `.claude/scripts/validate_sdd.py` — task-tier validation
- [[Agentic Coding Harness 實作計劃]] — where M4 sits in the overall pipeline
- [[Coding Conventions]] — Simplicity First / Surgical Changes the subagents follow
