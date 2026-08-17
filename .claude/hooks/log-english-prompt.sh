#!/bin/bash
# UserPromptSubmit hook: INSERT English-only prompts into Postgres (english_log.turns).
# Input: JSON on stdin with {prompt, cwd, session_id}.
# Output: echoes stdin back unchanged (never blocks the prompt).
set -uo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
ERR_LOG="${HOME}/.claude/english-log/.errors.log"
mkdir -p "${HOME}/.claude/english-log"

INPUT=$(cat)
printf '%s' "$INPUT"

{
  PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)
  CWD=$(printf '%s' "$INPUT"    | jq -r '.cwd // empty'    2>/dev/null)
  SID=$(printf '%s' "$INPUT"    | jq -r '.session_id // empty' 2>/dev/null)

  [ -z "$PROMPT" ] && exit 0
  case "$PROMPT" in
    "<command-"*|"<local-command-"*|"/"*) exit 0 ;;
  esac

  # shellcheck disable=SC1091
  source "${HOOK_DIR}/lib/is-english.sh"
  is_english "$PROMPT" || exit 0

  PROJECT=$(basename "$CWD" 2>/dev/null | tr -c 'A-Za-z0-9._-' '_' | sed 's/^_*//;s/_*$//')
  [ -z "$PROJECT" ] && PROJECT="unknown"

  # shellcheck disable=SC1091
  source "${HOOK_DIR}/lib/pg-url.sh"

  psql "$(pg_url)" -v ON_ERROR_STOP=1 --no-psqlrc -q \
    -v project="$PROJECT" -v sid="$SID" -v prompt="$PROMPT" \
    >/dev/null <<'SQL' || true
INSERT INTO turns (project, session_id, prompt_ts, prompt)
VALUES (:'project', :'sid', now(), :'prompt')
ON CONFLICT (session_id, prompt_ts) DO NOTHING;
SQL
} 2>> "$ERR_LOG"

exit 0
