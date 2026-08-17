#!/usr/bin/env bash
# sdd-validate-posttooluse.sh — Stage 0-2 schema feedback (M3/M4, item #16).
#
# After an edit to an SDD proposal.md/tasks.md, run the shared validator
# (validate_sdd.py) on that change folder and surface WARN/ERROR to stderr.
#
# INFORMATIONAL ONLY — always exit 0 (never blocks; a half-written four-pack is
# normal mid-propose). FAIL-OPEN: no jq / no uv / not an SDD file / validator not
# found => silently allow. Shares the one validator with the propose/apply skills.

command -v jq >/dev/null 2>&1 || exit 0
input="$(cat)"
fp="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)"
[ -n "$fp" ] || exit 0

# Only react to the two files the validator checks, inside an SDD change folder.
case "$fp" in
  */SDD/*/proposal.md|*/SDD/*/tasks.md) ;;
  *) exit 0 ;;
esac

folder="$(dirname "$fp")"
command -v uv >/dev/null 2>&1 || exit 0

# Walk up from the change folder to find the vault's validator (machine-agnostic).
dir="$folder"
validator=""
while [ "$dir" != "/" ] && [ -n "$dir" ]; do
  if [ -f "$dir/.claude/scripts/validate_sdd.py" ]; then
    validator="$dir/.claude/scripts/validate_sdd.py"
    break
  fi
  dir="$(dirname "$dir")"
done
[ -n "$validator" ] || exit 0

out="$(uv run "$validator" "$folder" 2>&1)" || true
# Only speak up when there is something to say (ERROR/WARN); stay quiet on clean pass.
if printf '%s' "$out" | grep -qE '^(ERROR|WARN)'; then
  echo "[sdd-validate] $(basename "$folder"):" >&2
  printf '%s\n' "$out" | grep -E '^(ERROR|WARN)' >&2
fi
exit 0
