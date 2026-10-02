---
name: sdd-orch
description: >-
  Drive an SDD ticket through propose, apply, verify, review, deliver and finalize by dispatching the owning skills. Read current proposal state on every entry, honor artifact applicability, and route explicit repair returns with bounded retries. Stop for design sign-off, PR merge, or unresolved blockers. Triggers: sdd orch, run the whole SDD pipeline, 跑完整流程, 接續這張票. --list and --status are read-only.
argument-hint: "[<project>] [<ticket|description>] [--status <ticket>] [--list]"
allowed-tools: Read, Bash, Glob, Grep, AskUserQuestion, TodoWrite, Agent, Skill
model: inherit
---

# sdd-orch

**This is a task command, not reference material. Once you've read it, start executing from Step 0.**

The pipeline driver: read where the ticket is in the SDD state machine, run the right next phase, re-read, repeat — stopping only at a genuine human gate. It guarantees the machine phases run **in order, with no skipping and no ad-hoc free-handing**, by always entering each phase through its own skill.

> [!important] Red lines (violate → stop)
>
> 1. **Never do a phase's work yourself.** The driver only _dispatches_ the phase skill (`sdd-propose` / `sdd-apply` / `sdd-verify` / `sdd-review` / `sdd-deliver`). It never writes application code, never writes SDD artifacts directly, never bumps `status` on its own — each phase skill owns that. If you catch yourself editing the target repo, STOP: that is a phase skill's job.
> 2. **`status` + `design_approved` in `proposal.md` are the only source of truth.** Decide the phase by reading them; never track progress in your head or in a script. This makes the driver idempotent and resumable — re-entering always recomputes from the files.
> 3. **Stop at the two human gates; never cross them.** Design sign-off (`design_approved: false → true`) and PR merge are human actions. At a gate, report exactly what the human must do and stop. Do not fake approval, do not merge.
> 4. **Change no phase skill.** This is a superstructure. If a phase behaves wrong, fix that phase's skill separately — don't work around it here.

## Triggers

- `/sdd-orch <project> <ticket>` — drive that ticket from wherever it is
- `/sdd-orch <project> <description>` — no SDD yet → dispatch `sdd-propose` first
- `/sdd-orch` (no args) — infer from conversation / cwd; if ambiguous → `--list` and ask
- `/sdd-orch --status <ticket>` — report the ticket's phase + next step, then stop
- `/sdd-orch --list` — scan every project's SDD, print each one's phase + next step, then stop
- Natural language: "run the whole SDD pipeline", "drive this ticket to done", "接續這張票", "一路跑到底", "sdd orch"

---

## The state machine (the whole model)

`proposal.md` frontmatter drives everything. Read `status` and `design_approved`, then dispatch:

| `status`                           | `design_approved` | Phase to run                                                        | How to run it                           | Bumps status to         |
| ---------------------------------- | ----------------- | ------------------------------------------------------------------- | --------------------------------------- | ----------------------- |
| (no folder / four-pack incomplete) | —                 | `sdd-propose`                                                       | 🤝 inline via Skill (interactive)       | (ends at sign-off gate) |
| `proposed`                         | `false`           | 🔴 **HUMAN: sign off**                                              | stop + instruct                         | (human edits proposal)  |
| `proposed` / `approved`            | `true`            | `sdd-apply`                                                         | inline via Skill                        | `verifying`             |
| `applying`                         | `true`            | `sdd-apply` (resume)                                                | inline via Skill                        | `verifying`             |
| `verifying`                        | —                 | `sdd-verify`                                                        | 🧹 independent subagent (clean session) | `reviewing`             |
| `reviewing`                        | —                 | `sdd-review`                                                        | 🧹 independent subagent (clean session) | `verified`              |
| `verified`                         | —                 | `sdd-deliver` (DELIVER)                                             | inline via Skill                        | `delivered`             |
| `delivered`                        | —                 | PR MERGED? → `sdd-deliver --finalize` ; else 🔴 **HUMAN: merge PR** | inline via Skill / stop + instruct      | `archived`              |
| `archived`                         | —                 | ✅ terminal — report complete                                       | —                                       | —                       |

- **Machine phases** (apply, verify, review, deliver DELIVER, finalize) run **automatically, back to back**.
- **Human gates** (🔴): sign-off and PR-merge. Stop there. Re-invoking `/sdd-orch` after the human clears the gate resumes automatically — that is the "self-prompt the next step" property, delivered by re-reading `status` rather than any hook.

---

## Flow

Let `VAULT_ROOT = {base_url}` — resolve `{base_url}` via `rules/00-machine-paths.md` before passing any path to a tool.

Read `.claude/skills/sdd-propose/references/planning-contract.md` on entry for artifact applicability, shared validation/task parsing, review freshness, and durable PR identity. Its `skip_specs` exception applies wherever this skill says four-pack/specs. Read-only list/status modes do not advance work. For backward transitions or plan edits, use that reference's `update-flow.md`; do not bypass phase ownership.

### Step 0 — Locate + read the state

1. **PROJECT + ticket**: from `$ARGUMENTS` / conversation / cwd; if unsure → `AskUserQuestion` (list subdirs under `01 Work/projects/`, excluding `_template`).
2. **SDD folder** = `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`. Glob it:
   - Missing or applicable planning artifacts incomplete → phase = propose. Use the shared ready validator; skip_specs intentionally omits specs, and every declared capability otherwise needs a spec. Do not route a valid removal/rename-only change back to propose for lacking new-behavior scenarios.
   - Complete → Read `proposal.md` frontmatter: `status`, `design_approved`.
3. **Compute the phase** from the state-machine table.
4. `--status <ticket>`: report the phase + the single next step, then **stop**.
5. `--list`: Glob `01 Work/projects/*/SDD/*/proposal.md`, Read each frontmatter, print a table (ticket / title / status / design_approved / phase / next step), then **stop**.

### Step 1 — Announce the plan

State, in one short block: current phase, the remaining phases to the next human gate, and where it will stop. Track the phases with **TodoWrite** (one todo per remaining phase). Then enter the loop.

### Step 2 — The dispatch loop

Repeat until a human gate or the terminal state:

1. **Recompute the phase** by reading `proposal.md` (never trust a cached value — the last phase just bumped it).
2. **If the phase is a human gate** → report exactly what to do and **stop** (see Step 3).
3. **Else dispatch the phase skill** by its run-mode:
   - **propose / apply / deliver → inline** via the `Skill` tool (`sdd-propose` / `sdd-apply` / `sdd-deliver`). They own their own subagents, worktrees, and markers; let them run to completion.
   - **verify / review → independent subagent** via the `Agent` tool, so each gets the clean session it requires. **Always pass `model` explicitly — never let it inherit.** The driver session runs on the most expensive tier; the phases must not: `sdd-verify` → `model: "sonnet"` (deterministic CI plus gap-filling tests), `sdd-review` → `model: "opus"` (spec judgement). Prompt the subagent:
     > Read `~/.claude/skills/sdd-<phase>/SKILL.md` and execute it end-to-end for project `<PROJECT>`, ticket `<ticket>`. Run in the feature-branch worktree for `sdd/<ticket>` (the skill re-derives it). Do only what that skill says; report the final `status` you left in `proposal.md` and any blocker.
4. **After the phase returns, re-read `status`.**
   - **Advanced as expected** → reset the failure counter, loop.
   - **Moved backward for repair under update-flow.md** → report the return phase and dispatch only if the owning phase explicitly handed it back with an actionable repair and no unresolved question. Count repeated same-failure returns toward the max-3 retry limit; a state change alone does not reset it.
   - **Did not advance, or an unresolved blocker / red / open CRITICAL remains** → **STOP**. Report which phase, what it found, and the exact blocker. Do **not** re-dispatch blindly (max 3 consecutive no-progress dispatches of the _same_ phase, per the global max-retries-3; usually stop on the first genuine blocker). Never try to fix it yourself.
5. **`delivered` special case**: before treating it as the PR-merge gate, check the PR state — `gh -R <repo> pr view <pr> --json state` (PR identity from proposal.pr first, then marker or unambiguous git/gh lookup). `MERGED` → dispatch `sdd-deliver --finalize` inline; anything else → it's the human gate, stop.

### Step 3 — Stopping at a human gate (self-prompt contract)

Stop cleanly and print the resume instruction. Two gates:

- **Sign-off** (`design_approved: false`):
  > Design awaits your sign-off. Set `design_approved: true` in `proposal.md`, then say "continue" (same session) or re-run `/sdd-orch <project> <ticket>`. I will pick up at apply.
- **PR merge** (`status: delivered`, PR not merged):
  > Draft PR is open (`<url>`). Review and merge it on GitHub, then say "merged" (same session) or re-run `/sdd-orch <project> <ticket> --finalize`. I will finalize (confirm MERGED → opted-in spec sync → sync base and clean up).

Because the phase is always recomputed from `status`, resuming needs no memory of this run — the same command (or a "continue") re-enters the loop exactly where it left off.

### Step 4 — Terminal

When the pipeline reaches done (post-finalize): report the phases run this session, the final commit/PR, the ticket's end state, and that all markers are disarmed. Stop.

---

## Guardrails

- Dispatch only; never do a phase's work. No app code, no SDD artifact writes, no `status` bumps by the driver.
- Phase decided solely by reading `proposal.md` — idempotent, resumable, same logic for first-run / same-session-continue / cross-session re-run.
- verify & review always as independent subagents (clean session) with an explicit `model` (sonnet / opus); apply & deliver inline (they manage their own isolation). Only the driver itself runs on the session's model.
- Stop at human gates; never fake sign-off, never merge a PR. Finalize only on fail-closed MERGED confirmation (delegated to `sdd-deliver --finalize`).
- On any blocker/red/no-progress, STOP and report — don't thrash, don't silence (max-retries-3). The phase skills already own "no bypass to force green".
- Converse in the user's language; the phase skills keep artifact content in English.

## Edge cases

| Situation                                                                                 | Handling                                                                                                                                |
| ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| No SDD folder yet, only a description                                                     | Phase = propose; dispatch `sdd-propose` (it will converge the design and stop at sign-off)                                              |
| Four-pack incomplete                                                                      | Phase = propose; dispatch `sdd-propose` to finish the chain                                                                             |
| `status` present but unknown value                                                        | Stop; report the value and ask — don't guess a phase                                                                                    |
| A phase skill stops at its own blocker (red tests, unmet criteria, missing repo mapping)  | Surface it verbatim and stop; the fix is re-running that phase / going back a phase, not the driver                                     |
| `delivered` but `gh` can't determine PR state                                             | Treat as the human gate (fail-closed); stop and ask the user to confirm/merge                                                           |
| User says "continue" / "merged" mid-session                                               | Re-enter Step 0 (recompute from `status`); no special-casing needed                                                                     |
| A stale `sdd-active-<session_id>` / `sdd-delivered-<ticket>` marker from an abandoned run | The phase skill owns its marker; if one blocks unexpectedly, report it and let the user disarm — the gate message prints the exact path |
| User wants to skip a phase                                                                | Refuse — the point of the driver is no skipping; if a phase is genuinely N/A, that belongs in the phase skill's logic, not here         |

## Further Reading

- `sdd-propose` / `sdd-apply` / `sdd-verify` / `sdd-review` / `sdd-deliver` — the five phase skills this driver sequences (unchanged by it)
- `.claude/scripts/validate_sdd.py` — schema/tier validation used by the phase skills
- [[Agentic Coding Harness 實作計劃]] — the overall M3–M6 pipeline this driver automates
- [[Agentic Coding High Level Process Implement]] — the phase-by-phase order diagram (the canvas)
