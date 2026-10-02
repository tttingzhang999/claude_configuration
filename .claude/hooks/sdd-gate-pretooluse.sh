#!/usr/bin/env bash
# Backstop for path-based edits in an active SDD's repo/worktrees.
# No marker/scope => no-op. Within that scope, current proposal approval wins
# over the cached marker. This is not a sandbox for arbitrary Bash commands.

command -v jq >/dev/null 2>&1 || exit 0
input="$(cat)"
sid="$(printf '%s' "$input" | jq -r '.session_id // empty')"
[ -n "$sid" ] || sid="${CLAUDE_CODE_SESSION_ID:-}"
[ -n "$sid" ] || exit 0
MARKER="$HOME/.claude/sdd-active-$sid"
[ -f "$MARKER" ] || exit 0
field() { sed -n "s/^$1=//p" "$MARKER" | head -1; }
repo_path="$(field repo_path)"
sdd_path="$(field sdd_path)"
ticket="$(field ticket)"
fp="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.path // empty')"
[ -n "$fp" ] && [ -n "$repo_path" ] || exit 0

scoped=false
# Existing worktrees plus explicitly registered paths (one worktree_path= per
# integration/group worktree). No word splitting: vault paths contain spaces.
while IFS= read -r scope; do
  [ -n "$scope" ] || continue
  case "$fp" in "$scope"|"$scope"/*) scoped=true ;; esac
done <<EOF_PATHS
$repo_path
$(sed -n 's/^worktree_path=//p' "$MARKER")
$(git -C "$repo_path" worktree list --porcelain 2>/dev/null | sed -n 's/^worktree //p')
EOF_PATHS
[ "$scoped" = true ] || exit 0

approved="$(field design_approved)"
if [ -n "$sdd_path" ]; then
  # Resolve the installed hook symlink to the vault before locating the script.
  hook_source="${BASH_SOURCE[0]}"
  while [ -L "$hook_source" ]; do
    link="$(readlink "$hook_source")" || exit 2
    case "$link" in
      /*) hook_source="$link" ;;
      *) hook_source="$(dirname "$hook_source")/$link" ;;
    esac
  done
  hook_dir="$(cd "$(dirname "$hook_source")" && pwd -P)" || exit 2
  validator="$hook_dir/../scripts/validate_sdd.py"
  if ! command -v uv >/dev/null 2>&1 || [ ! -f "$validator" ]; then
    echo "[sdd-gate] Cannot verify current approval for $ticket; restore uv/validator before scoped edits." >&2
    exit 2
  fi
  if ! approved="$(uv run "$validator" "$sdd_path" --approval 2>/dev/null)"; then
    approved=false
  fi
fi
[ "$approved" = true ] && exit 0
echo "[sdd-gate] BLOCKED: $ticket has no current design approval for '$fp'." >&2
echo "[sdd-gate] Complete /sdd-propose --update and human sign-off, then resume /sdd-apply." >&2
exit 2
