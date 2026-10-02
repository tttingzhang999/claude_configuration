#!/usr/bin/env bash
# sdd-gate-stop.sh — Stage 2 gate (M4).
#
# Refuse to end a pipeline session while the active SDD's tests are RED.
# Armed by the sdd-apply skill via the session marker
# ~/.claude/sdd-active-<session_id> (key=value) — per session, so concurrent SDD
# sessions never read or clobber each other's marker.
#
# FAIL-OPEN by design: no session id / no marker / unset / unparseable => allow (exit 0).
# Only an unambiguous tests_green=false blocks (exit 2). Ordinary sessions
# (no active SDD) are never affected.
#
# Blocks once per stop attempt: when stop_hook_active=true (the retry after a
# block) it allows, so a deliberate pause cannot trap the session in a loop.

input="$(cat)"
sid=""
if command -v jq >/dev/null 2>&1; then
  [ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)" = "true" ] && exit 0
  sid="$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null)"
fi
[ -n "$sid" ] || sid="$CLAUDE_CODE_SESSION_ID"
[ -n "$sid" ] || exit 0

MARKER="$HOME/.claude/sdd-active-$sid"
[ -f "$MARKER" ] || exit 0

tests_green="$(grep -E '^tests_green=' "$MARKER" 2>/dev/null | head -1 | cut -d= -f2-)"
ticket="$(grep -E '^ticket=' "$MARKER" 2>/dev/null | head -1 | cut -d= -f2-)"

if [ "$tests_green" = "false" ]; then
  echo "[sdd-gate] BLOCKED: active SDD ($ticket) has red tests. Run the tests to green before stopping — do not bypass." >&2
  echo "[sdd-gate] If you are genuinely abandoning this apply run, disarm with: rm $MARKER" >&2
  exit 2
fi
exit 0
