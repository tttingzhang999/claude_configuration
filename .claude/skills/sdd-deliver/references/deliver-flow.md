# Deliver / finalize flow (two-phase)

Delivery is deliberately split because **merging the PR is an async human action**.
The agent does everything up to the merge, stops, and only comes back — when the
user triggers `--finalize` — to mirror the merged result locally.

```
DELIVER (agent)                          human            FINALIZE (agent, --finalize)
──────────────                           ─────            ────────────────────────────
push sdd/<ticket>                                          confirm remote PR == MERGED  (fail-closed)
open DRAFT PR (never merge)   ──▶  review, mark ready,      checkout base_branch + pull  (mirror remote)
Jira transition (jira-automation)      merge the PR             worktree remove <wt_feat>
status verified → delivered                                branch -d sdd/<ticket>
arm sdd-delivered-<ticket>                                 disarm sdd-delivered-<ticket>
/brief-back  (non-blocking)
write-back   (human-in-loop)
STOP ──────────────────────────▶
```

## Why draft PR (not ready-for-review)

Opening as draft makes the "human's button" explicit: the agent delivers a candidate,
the human promotes it to ready + merges. The agent physically cannot skip that step —
it never runs `gh pr merge`, never `--ready`, never pushes the base branch.

## The base branch moves exactly once, safely

`main` / the base branch is never merged into locally. The only write to it is
FINALIZE Step F2's `checkout base + pull`, which fast-forwards to the _already-merged_
remote. So the local base only ever mirrors what the remote already accepted — there is
no local merge of `sdd/<ticket>` into the base at any point.

## The marker + the backstop hook

`DELIVER` arms `~/.claude/sdd-delivered-<ticket>` (ticket / repo_path / base_branch /
feature_branch / pr). While it is armed, `sdd-pr-status.sh` (a PreToolUse backstop,
fail-open) blocks any manual `git merge sdd/<ticket>` / base-branch push in **any**
session unless the remote PR is already MERGED. `FINALIZE` disarms it on clean cleanup.
The hook scans every `sdd-delivered-*` marker, so concurrent deliveries each keep their
own guard instead of clobbering one shared file.

- Backstop hook (ambient, fail-open): never wrecks ordinary sessions; only acts when the marker is armed and the command targets the base branch.
- Finalize check (in this skill, fail-closed): must positively see `MERGED` to proceed. Two layers, opposite failure modes — each correct for its role.

## What DELIVER must never do

- `gh pr merge`, `gh pr ready`, or any push to the base branch.
- A local `git merge sdd/<ticket>` into `main`/base.
- `jira-automation`'s `implement-ticket` route (that re-does M2–M5).
- Persist any learning without the user approving the preview.
