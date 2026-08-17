#!/usr/bin/env bash
# sdd-gate-pretooluse.sh — Stage 2 gate (M4).
#
# Block code edits inside the TARGET REPO while the active SDD is NOT design-approved.
# Armed by the sdd-apply skill via the session marker
# ~/.claude/sdd-active-<session_id> (key=value) — per session, so concurrent SDD
# sessions never read or clobber each other's marker. Apply subagents inherit the
# parent session_id, so their tool calls hit the same marker.
#
# FAIL-OPEN by design: no jq / no session id / no marker / unparseable input /
# no repo scope => allow (exit 0). Only an unambiguous "unapproved SDD + edit
# under repo_path" blocks (exit 2), so ordinary sessions are never affected.

# Need jq to read the session id + edited path out of the tool-call JSON on stdin.
command -v jq >/dev/null 2>&1 || exit 0
input="$(cat)"

sid="$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null)"
[ -n "$sid" ] || sid="$CLAUDE_CODE_SESSION_ID"
[ -n "$sid" ] || exit 0

MARKER="$HOME/.claude/sdd-active-$sid"
[ -f "$MARKER" ] || exit 0

design_approved="$(grep -E '^design_approved=' "$MARKER" 2>/dev/null | head -1 | cut -d= -f2-)"
repo_path="$(grep -E '^repo_path=' "$MARKER" 2>/dev/null | head -1 | cut -d= -f2-)"
ticket="$(grep -E '^ticket=' "$MARKER" 2>/dev/null | head -1 | cut -d= -f2-)"

# Approved => the gate is open.
[ "$design_approved" = "true" ] && exit 0
# Without a repo scope we cannot safely target only code edits => fail open.
[ -n "$repo_path" ] || exit 0

fp="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)"
[ -n "$fp" ] || exit 0

case "$fp" in
  "$repo_path"/*|"$repo_path")
    echo "[sdd-gate] BLOCKED: '$fp' is target-repo code, but the active SDD ($ticket) has design_approved: false." >&2
    echo "[sdd-gate] Get design sign-off (flip 'design_approved: true' in the proposal), then re-run sdd-apply." >&2
    echo "[sdd-gate] Stage 0-1 only edit vault SDD artifacts, not repo code. To disarm: rm $MARKER" >&2
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
