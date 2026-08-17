#!/bin/bash
# compact-response.sh — backgrounded helper that calls Haiku to summarize an
# assistant message, parses the "Vocab: ..." suffix, and UPDATEs the latest
# open `turns` row for a session_id.
#
# Args: MSG SID ERR_LOG PG_URL
set -uo pipefail

MSG="${1:-}"
SID="${2:-}"
ERR_LOG="${3:-/dev/null}"
PG_URL="${4:-}"

[ -z "$MSG" ] && exit 0
[ -z "$SID" ] && exit 0
[ -z "$PG_URL" ] && exit 0

INSTR="Summarize the assistant response below in 1-2 concise English sentences for a language learner. Preserve phrasal verbs, idioms, and uncommon vocabulary worth learning; list them afterwards as Vocab: word1, word2."
FULL=$(printf '%s\n\n---\nAssistant response to summarize:\n\n%s' "$INSTR" "$MSG")

COMPACT=$(printf '%s' "$FULL" | claude -p --model claude-haiku-4-5-20251001 2>>"$ERR_LOG")
[ -z "$COMPACT" ] && exit 0

SUMMARY=$(printf '%s' "$COMPACT" | awk 'BEGIN{IGNORECASE=1} /[Vv]ocab:/{exit} {print}')
VOCAB_LINE=$(printf '%s' "$COMPACT" | awk 'BEGIN{IGNORECASE=1} /[Vv]ocab:/{sub(/^.*[Vv]ocab:[[:space:]]*/, ""); print; exit}')
[ -z "$SUMMARY" ] && SUMMARY="$COMPACT"

VOCAB_ARR=$(printf '%s' "$VOCAB_LINE" | awk -F',' '
  BEGIN { out="{"; first=1 }
  {
    for (i=1; i<=NF; i++) {
      s = $i
      sub(/^[[:space:]]+/, "", s)
      sub(/[[:space:].,]+$/, "", s)
      if (length(s) == 0) continue
      gsub(/\\/, "\\\\", s)
      gsub(/"/,  "\\\"", s)
      if (!first) out = out ","
      out = out "\"" s "\""
      first = 0
    }
  }
  END { print out "}" }
')
[ -z "$VOCAB_ARR" ] && VOCAB_ARR="{}"

OLEN=$(printf '%s' "$MSG" | wc -c | tr -d ' ')

psql "$PG_URL" -v ON_ERROR_STOP=1 --no-psqlrc -q \
  -v sid="$SID" -v summary="$SUMMARY" -v vocab="$VOCAB_ARR" -v olen="$OLEN" \
  >/dev/null 2>>"$ERR_LOG" <<'SQL' || true
UPDATE turns
   SET response_ts  = now(),
       compact      = :'summary',
       vocab        = :'vocab'::text[],
       original_len = :'olen'::int
 WHERE id = (
   SELECT id FROM turns
   WHERE session_id = :'sid' AND response_ts IS NULL
   ORDER BY prompt_ts DESC LIMIT 1
 );
SQL
