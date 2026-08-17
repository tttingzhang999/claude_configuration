#!/usr/bin/env bash
# PostToolUse (Write|Edit): format the file that was just written with Prettier.
#
# Rules come from the .prettierrc / .prettierignore that Prettier resolves from
# the edited file's own directory — so other repos get their own config, and this
# vault gets proseWrap: preserve (never re-wrap prose).
#
# Silent on success. Exit 2 on failure so Claude is told why the file is unformatted.
set -uo pipefail

file=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -n "$file" ] && [ -f "$file" ] || exit 0

# Skip what Prettier has no parser for, before paying the process-spawn cost.
case "$file" in
*.md | *.markdown | *.json | *.jsonc | *.js | *.mjs | *.cjs | *.jsx | *.ts | *.mts | *.cts | *.tsx | *.css | *.scss | *.less | *.html | *.vue | *.yaml | *.yml | *.graphql) ;;
*) exit 0 ;;
esac

runner=(npx --yes prettier)
command -v prettier >/dev/null 2>&1 && runner=(prettier)

if ! out=$("${runner[@]}" --write --ignore-unknown --log-level warn "$file" 2>&1); then
	printf 'Prettier could not format %s:\n%s\n' "$file" "$out" >&2
	exit 2
fi
exit 0
