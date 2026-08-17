#!/bin/bash
# pg_url — prints the connection URL for the english_log database.
# Override via ENGLISH_LOG_DATABASE_URL for CI or remote testing.
pg_url() {
  printf '%s' "${ENGLISH_LOG_DATABASE_URL:-postgresql://${USER}@localhost:5432/english_log}"
}
