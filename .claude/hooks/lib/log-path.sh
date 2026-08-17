#!/bin/bash
# log_path "$cwd" — prints today's JSONL log path for the given project cwd.
# Sanitizes basename to [A-Za-z0-9._-]. Creates the parent directory.
log_path() {
  local cwd="$1"
  local base
  base=$(basename "$cwd" 2>/dev/null | tr -c 'A-Za-z0-9._-' '_' | sed 's/^_*//; s/_*$//')
  [ -z "$base" ] && base="unknown"
  local root="${HOME}/.claude/english-log/${base}"
  mkdir -p "$root"
  printf '%s/%s.jsonl' "$root" "$(date +%Y-%m-%d)"
}
