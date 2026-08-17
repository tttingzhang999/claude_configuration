#!/usr/bin/env bash
# sdd-pr-status.sh — M6 delivery gate around the remote PR's merged status.
#
# TWO MODES, opposite failure modes on purpose:
#
# 1. --check <ticket>  (invoked by sdd-deliver FINALIZE): FAIL-CLOSED.
#    Exit 0 only if that ticket's remote PR is positively MERGED; exit 1 otherwise
#    (no ticket arg / open / closed-unmerged / cannot determine). Never let
#    finalize sync the base branch without proof the PR merged.
#
# 2. (no arg) PreToolUse Bash backstop: FAIL-OPEN.
#    Reads EVERY ~/.claude/sdd-delivered-<ticket> marker. No marker => exit 0
#    (ordinary sessions untouched). Any marker whose feature/base branch the
#    command would advance while its PR is NOT merged => exit 2 (block).
#    Anything unparseable / no gh / no jq => exit 0 (never wreck a session).
#
# The marker is per TICKET, not per session: DELIVER arms it, the human merges the
# PR later, and FINALIZE runs in a whole different session — so it must survive
# across sessions, while staying isolated between concurrent deliveries.
# Contents (key=value): ticket / repo_path / base_branch / feature_branch / pr

marker_for() { echo "$HOME/.claude/sdd-delivered-$1"; }

# --- helper: echo the remote PR state (MERGED/OPEN/CLOSED) or empty on failure
pr_state() {
  local repo_path="$1" pr="$2"
  command -v gh >/dev/null 2>&1 || return 1
  [ -n "$repo_path" ] && [ -n "$pr" ] || return 1
  ( cd "$repo_path" 2>/dev/null && gh pr view "$pr" --json state -q .state 2>/dev/null )
}

# --- helper: does $2 (a Bash command) advance the base branch of marker $1?
#     Sources the marker, so ALWAYS call it in a subshell: ( check_marker … ) || block
#     Returns 1 = block, 0 = allow.
check_marker() {
  local m="$1" cmd="$2" probe state
  # shellcheck disable=SC1090
  . "$m" 2>/dev/null || return 0
  [ -n "$feature_branch" ] && [ -n "$base_branch" ] || return 0

  # Merging a REMOTE-qualified feature ref (origin/<feature>) is the fast-forward you run
  # inside the feature worktree to sync the feature branch to its own remote — the opposite
  # direction from what this gate guards. Strip those occurrences so only the LOCAL feature
  # branch counts. Accepted residual hole: `git checkout <base> && git merge origin/<feature>`
  # slips through; this is a fail-open backstop, not a lock (see the header).
  probe="${cmd//origin\/$feature_branch/}"

  case "$probe" in
    *"git"*"merge"*"$feature_branch"* | *"git"*"push"*"origin"*"$base_branch"* ) ;;
    *) return 0 ;;
  esac

  state="$(pr_state "$repo_path" "$pr")"
  [ "$state" = "MERGED" ] && return 0   # already merged upstream — allow local sync

  echo "[sdd-pr-status] BLOCKED: PR '$pr' for $feature_branch is '${state:-unknown}', not MERGED." >&2
  echo "[sdd-pr-status] Merge the PR first, then: /sdd-deliver <project> $ticket --finalize (disarm: rm $m)" >&2
  return 1
}

# ---------------------------------------------------------------- --check mode
if [ "$1" = "--check" ]; then
  [ -n "$2" ] || { echo "sdd-pr-status: --check needs a ticket (e.g. --check ExampleClient-116)." >&2; exit 1; }
  MARKER="$(marker_for "$2")"
  [ -f "$MARKER" ] || { echo "sdd-pr-status: no delivery marker for '$2'; nothing to finalize." >&2; exit 1; }
  # shellcheck disable=SC1090
  . "$MARKER" 2>/dev/null || { echo "sdd-pr-status: unreadable marker $MARKER." >&2; exit 1; }
  state="$(pr_state "$repo_path" "$pr")"
  if [ "$state" = "MERGED" ]; then
    exit 0
  fi
  echo "sdd-pr-status: remote PR '$pr' is '${state:-unknown}', not MERGED — refuse to finalize." >&2
  exit 1
fi

# ------------------------------------------------------- PreToolUse backstop
# Fail-open at every missing precondition.
command -v jq >/dev/null 2>&1 || exit 0

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)"
[ -n "$cmd" ] || exit 0

# Only care about commands that could advance a base branch with its feature branch.
# `git merge-base` / `git merge --abort` advance nothing — they only read or clean up.
case "$cmd" in
  *"git"*merge-base* | *"git"*"merge"*--abort* ) exit 0 ;;
esac

shopt -s nullglob
for m in "$HOME"/.claude/sdd-delivered-*; do
  ( check_marker "$m" "$cmd" ) || exit 2
done
exit 0
