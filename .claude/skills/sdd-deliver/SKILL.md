---
name: sdd-deliver
description: >-
  Deliver a verified SDD change through a draft PR, reusing an existing open PR after rework. Check review freshness, preserve durable PR identity, and run the human learning checkpoint. --finalize confirms merge, synchronizes canonical specs only for opted-in projects, and cleans up safely. Triggers: sdd deliver, ship it, open the PR, 交付這張票. Never merges a PR.
argument-hint: "[<project>] [<ticket>] [--finalize] [--list]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, TodoWrite, Agent
model: inherit
---

# sdd-deliver

**This is a task command, not reference material. Once you've read it, start executing from Step 0.**

The Stages 5–6 orchestrator: take a review-verified change to a draft PR + Jira, hold the ownership loop (`/brief-back`), capture what was learned (write-back), and — only after the human merges the PR — finalize the local tree. Merging the PR is the human's button; this skill never presses it.

> [!important] Red lines (violate → stop)
>
> 1. **Draft PR only, never merge, never push `main`.** The agent pushes `sdd/<ticket>` and opens a _draft_ PR. Turning it ready-for-review and merging is the human's action.
> 2. **`main` is touched only in FINALIZE, only after the remote PR is MERGED.** Confirm merged status first (fail-closed); if it can't be confirmed, refuse to finalize.
> 3. **`jira-automation` delivery route only.** Use it for the PR link + Jira transition; never its `implement-ticket` route (that duplicates M2–M5).
> 4. **Write-back is human-in-loop.** No learning is persisted without a preview → approval (same contract as `cook-progress`). The agent never silently writes to `keypoint/`, `Coding Conventions.md`, or the wiki.
> 5. **`/brief-back` is a ritual, not a gate.** It never blocks delivery or status; it only records `briefback.md`.
> 6. **decision-log is human-authored.** The agent may append _challenges_ to `decision-log.md`, never the decisions themselves.

## The delivery marker

`~/.claude/sdd-delivered-<ticket>` — machine-local, key=value, armed at the end of DELIVER, disarmed on clean FINALIZE. Lets the `sdd-pr-status` backstop hook block an accidental manual merge of `sdd/<ticket>` into the base branch while a delivery is pending, across sessions.

**Keyed by ticket, not by session** — deliberately, because FINALIZE runs in a different session once the human has merged, so the marker must outlive the delivering session. The ticket suffix is what keeps two concurrent deliveries from overwriting each other; the backstop hook scans every `sdd-delivered-*`.

```
ticket=<ticket>
repo_path=<abs path to the target repo>
base_branch=<the branch the PR targets, e.g. main>
feature_branch=sdd/<ticket>
pr=<PR number or URL>
```

No marker → the hook no-ops. Manual disarm: `rm ~/.claude/sdd-delivered-<ticket>`.

## Triggers

- `/sdd-deliver <project> <ticket>` — run DELIVER
- `/sdd-deliver <project> <ticket> --finalize` — run FINALIZE (after the human merged the PR)
- `/sdd-deliver --list` — list changes with `status: verified` (or `delivered`, awaiting finalize), then stop
- Natural language: "deliver this SDD", "ship it", "open the PR", "交付這張票"; "PR merged, finalize <ticket>" → FINALIZE

---

## Flow

Let `VAULT_ROOT = {base_url}` — resolve `{base_url}` via `rules/00-machine-paths.md` before passing any path to a tool.

Read `.claude/skills/sdd-propose/references/planning-contract.md` on entry for artifact applicability, shared validation/task parsing, review freshness, and durable PR identity. Its `skip_specs` exception applies wherever this skill says four-pack/specs. Read-only list/status modes do not advance work. For backward transitions or plan edits, use that reference's `update-flow.md`; do not bypass phase ownership.

### Step 0 — Locate the change, repo, and feature branch

1. **PROJECT + ticket**: from `$ARGUMENTS` / conversation / cwd; if unsure → `AskUserQuestion`.
2. **SDD folder** = `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`. Read the four-pack + `review.md`.
3. **Phase**: `--finalize` → jump to FINALIZE. Otherwise DELIVER, which requires `status: verified` (review passed). Any other status → say what's pending and stop.
4. **repo_path** via `repo-router`; **feature branch** = `sdd/<ticket>`, find its worktree; **base_branch** = the branch it was cut from (default `main`; confirm from git).
5. If status=archived, report completion read-only; never replay old deltas.
6. `--list`: Glob proposals with `status: verified` or `delivered`, print them, then **stop**.

---

## DELIVER (agent runs, then stops for the human to merge)

### Step 1 — Validate freshness, then push + draft PR + Jira

- Run ready validation and shared task progress; require all tasks complete. Require a clean feature worktree and review.md with reviewed_commit equal to HEAD and plan_fingerprint equal to the current fingerprint. Missing/stale evidence goes back to verify/review or --update per planning-contract.md; do not silently refresh fields. For a pre-upgrade review without these fields, re-review once.
- Resolve proposal.pr first. If an existing PR is open for this repo/branch, reuse it; if merged, stop re-delivery and reconcile finalize/follow-up work; closed-unmerged requires an explicit decision. Re-read remote PR state before any write.

- Push the feature branch: `git -C "<repo_path>" push -u origin sdd/<ticket>`.
- If no PR exists, open a **draft** PR against `base_branch`, body built from `review.md` following the vault PR template (`~/.claude/rules/common/git-workflow.md`): `gh -R <repo> pr create --draft --base <base_branch> --head sdd/<ticket> --title "<type>: <ticket> <title>" --body-file <draft>`. (Or `jira-automation` `backfill-pr` route if it produces the same draft PR.)
- For an existing open PR, update its description from the new review using a body file; keep its identity and ready/draft state. Persist the returned URL as proposal `pr` BEFORE setting delivered. Do not create duplicate PRs on retry; if a prior creation succeeded before persistence, look up the exact repo/head/base PR first.
- **Jira** via `jira-automation` (delivery route): transition the ticket to the in-review state and attach the PR link. Never its implement route.
- Bump `proposal.md` `status`: `verified → delivered`.
- **Arm the marker** `~/.claude/sdd-delivered-<ticket>` (ticket / repo_path / base_branch / feature_branch / pr).

### Step 2 — `/brief-back` (immediately, non-blocking)

Right after the PR is up, run the ownership ritual (see `references/brief-back.md`): from `decision-log.md` + the diff, generate the 3 questions (why this design / the trade-off / where it's most likely to break). Ask the user; compare their answers to the implementation and give feedback. Write `briefback.md` in the SDD folder. **This never blocks** — if the user skips, note "skipped" and move on.

### Step 3 — Write-back (human-in-loop)

Two separate tracks (see `references/write-back.md`):

1. **Action Items + progress** via `cook-progress` — update `Action Items - WIP/Done.md` and note progress against the roadmap. Respect its rules (personal work items only; mandatory preview → approve).
2. **Learning checkpoint** — extract atomic learning candidates from the 6 sources (`design.md`, `decision-log.md`, `review.md`, the diff, `briefback.md`, CI gotchas), dedup against existing `keypoint/` + `Coding Conventions.md`, **preview → get approval**, then persist approved ones: project → `keypoint/`, global candidate → `00 Self/Coding Conventions.md`, synthesis → `02 Knowledge/`. **Nothing persists without approval.**

### Step 4 — Stop for the human

Report: draft PR URL, Jira transition, brief-back outcome, what was written back. Then **stop** with:

```
Delivered <ticket> as a draft PR: <url>. Review it, mark ready, and merge when you're happy.
After the remote PR is merged, run: /sdd-deliver <project> <ticket> --finalize
```

Do **not** merge, un-draft, or touch `main`.

---

## FINALIZE (`--finalize`, after the human merged the PR)

### Step F1 — Confirm the remote PR is MERGED (fail-closed)

Resolve proposal.pr first (fallback to the ticket marker or unambiguous repo/head lookup), then query `gh -R <repo> pr view <pr> --json state,mergedAt,mergeCommit,baseRefName,headRefName`. Verify repo/base identity and merged state; the marker alone is not durable proof. Proceed **only if `state == MERGED`**. Anything else (open, closed-unmerged, or can't determine) → refuse and tell the user to merge first. Never sync `main` without positive confirmation.

### Step F2 — Synchronize opted-in canonical specs

Read `references/spec-sync.md`. Preserve legacy behavior for projects without the explicit opt-in; skip_specs means N/A. For opted-in projects capture/recover the baseline and apply the three-way operation checks against merged code. If sync fails, leave delivered and preserve recovery resources. Only after successful applicable sync continue.

### Step F3 — Sync base + clean up

- Update the local base branch: `git -C "<repo_path>" checkout <base_branch> && git -C "<repo_path>" pull` (or fetch + fast-forward). This is the _only_ point `main`/`base` moves — and it's just mirroring the already-merged remote, not a local merge of the feature branch.
- Remove the feature worktree: `git -C "<repo_path>" worktree remove "<wt_feat>"`; delete the merged branch: `git -C "<repo_path>" branch -d sdd/<ticket>` (local) and optionally `git -C "<repo_path>" push origin --delete sdd/<ticket>`.
- Remove only confirmed clean/recoverable worktrees and merged branches; preserve dirty or unmerged work and report it. Handle squash-merged branches explicitly instead of force-deleting after `branch -d` fails. Missing resources on a retry are already cleaned, not a failure.
- **Disarm** the marker after cleanup and applicable spec sync succeed: `rm -f ~/.claude/sdd-delivered-<ticket>`.
- Bump `proposal.md` `status`: `delivered → archived` (the terminal value; never write `done` — it is not a legal status).
- Report: base branch synced, worktree/branches cleaned, ticket fully closed.

---

## Guardrails

- Draft PR only; the human un-drafts and merges; the agent never merges or pushes `main`.
- FINALIZE confirms MERGED before any base-branch sync (fail-closed); the sync mirrors the remote, it doesn't merge the feature branch locally.
- Write-back never persists without preview → approval; decision-log stays human-authored (agent only appends challenges).
- brief-back is non-blocking; delivery and status don't depend on it.
- `jira-automation` delivery route only; no `implement-ticket`.
- English content in artifacts; converse in the user's language.

## Edge cases

| Situation                                    | Handling                                                                                                    |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `status` not `verified`                      | Refuse DELIVER; say which stage is pending (`reviewing` → review not done)                                  |
| No `review.md`                               | Refuse; review (`sdd-review`) hasn't produced its artifact                                                  |
| `gh` / remote not available                  | DELIVER: report the push/PR failure, don't fake a PR. FINALIZE: can't confirm MERGED → refuse (fail-closed) |
| User skips brief-back                        | Record "skipped" in `briefback.md`; continue (non-blocking)                                                 |
| No learning worth capturing                  | Say so; write nothing; still do Action Items/progress                                                       |
| User rejects a learning candidate in preview | Drop it; persist only approved ones                                                                         |
| `--finalize` but PR not merged               | Refuse; tell the user to merge the PR first                                                                 |
| Marker missing at `--finalize`               | Fall back to args (project/ticket) + `gh pr view`; still fail-closed on merged status                       |
| decision-log absent                          | Note it; brief-back leans on the diff + design.md; suggest the human keep a decision-log next time          |

## Further Reading

- `references/deliver-flow.md` — the two-phase deliver/finalize sequence in detail
- `references/brief-back.md` — the 3-question ownership ritual + how feedback is given
- `references/write-back.md` — the learning checkpoint (6 sources, schema, scope routing, 5 steps)
- `.claude/hooks/sdd-pr-status.sh` — the merged-status gate/backstop
- `.claude/skills/sdd-review/SKILL.md` — Stage 4, the prerequisite (must be `verified`)
- [[Agentic Coding Harness 實作計劃]] — where M6 sits in the overall pipeline
