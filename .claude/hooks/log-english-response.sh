#!/bin/bash
# Stop hook: when the last user turn was English, read the transcript,
# ask Haiku to compact the assistant response for language-learning review,
# and append the result to today's JSONL log.
#
# Input: JSON on stdin with {transcript_path, cwd, session_id, stop_hook_active}.
# Output: nothing (Stop hook doesn't modify conversation).
set -uo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
ERR_LOG="${HOME}/.claude/english-log/.errors.log"
mkdir -p "${HOME}/.claude/english-log"

INPUT=$(cat)

{
  TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
  CWD=$(printf '%s' "$INPUT"        | jq -r '.cwd // empty'             2>/dev/null)
  SID=$(printf '%s' "$INPUT"        | jq -r '.session_id // empty'      2>/dev/null)
  ACTIVE=$(printf '%s' "$INPUT"     | jq -r '.stop_hook_active // false' 2>/dev/null)

  [ "$ACTIVE" = "true" ] && exit 0
  if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then exit 0; fi

  # Last real user prompt: type=user, content is a string, not meta,
  # and not a slash/command wrapper.
  LAST_USER=$(jq -r '
      select(.type=="user"
             and (.message.content | type == "string")
             and (.isMeta // false | not)
             and (.message.content | startswith("<command-") | not)
             and (.message.content | startswith("<local-command-") | not)
             and (.message.content | startswith("/") | not))
      | .message.content
    ' "$TRANSCRIPT" 2>/dev/null | tail -1)

  [ -z "$LAST_USER" ] && exit 0

  # shellcheck disable=SC1091
  source "${HOOK_DIR}/lib/is-english.sh"
  is_english "$LAST_USER" || exit 0

  # Last assistant message: flatten any text blocks into a single string.
  LAST_ASSISTANT=$(jq -r '
      select(.type=="assistant")
      | .message.content
      | if type=="string" then .
        else (map(select(.type=="text") | .text) | join("\n"))
        end
    ' "$TRANSCRIPT" 2>/dev/null | awk 'NF' | tail -1)

  [ -z "$LAST_ASSISTANT" ] && exit 0

  # shellcheck disable=SC1091
  source "${HOOK_DIR}/lib/pg-url.sh"
  PG_URL=$(pg_url)

  # Background the Haiku compaction + psql UPDATE so session end is never delayed.
  nohup bash "${HOOK_DIR}/lib/compact-response.sh" \
    "$LAST_ASSISTANT" "$SID" "$ERR_LOG" "$PG_URL" \
    >/dev/null 2>>"$ERR_LOG" &
  disown 2>/dev/null || true
} 2>> "$ERR_LOG"

exit 0
