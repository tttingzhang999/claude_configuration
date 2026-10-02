#!/usr/bin/env bash
# test-sdd-gates.sh — self-check for the three SDD gate hooks' marker isolation.
#
# Run: bash .claude/hooks/test-sdd-gates.sh
# Uses a throwaway HOME so it never touches real markers, and fake repo paths so
# `gh` is never reached (pr_state returns empty => the not-MERGED block path).

set -u
HOOKS="$(cd "$(dirname "$0")" && pwd)"
FAILED=0

ok() { echo "  ok   — $1"; }
bad() { echo "  FAIL — $1"; FAILED=1; }
expect() { # expect <want-exit> <got-exit> <label>
  if [ "$1" = "$2" ]; then ok "$3"; else bad "$3 (want exit $1, got $2)"; fi
}

# Keep installed interpreter/dependency caches visible after HOME isolation.
export UV_CACHE_DIR="${UV_CACHE_DIR:-$(uv cache dir)}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$(uv python dir)}"
SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
export HOME="$SANDBOX"
mkdir -p "$HOME/.claude"

SID_A="aaaaaaaa-1111-1111-1111-aaaaaaaaaaaa"
SID_B="bbbbbbbb-2222-2222-2222-bbbbbbbbbbbb"
REPO="/tmp/does-not-exist-repo"

# Session A: unapproved design, tests red.
cat > "$HOME/.claude/sdd-active-$SID_A" <<EOF
ticket=TEST-1
design_approved=false
repo_path=$REPO
tests_green=false
EOF

edit_payload() { # <session_id> <file_path>
  printf '{"session_id":"%s","tool_name":"Edit","tool_input":{"file_path":"%s"}}' "$1" "$2"
}

echo "== PreToolUse gate: per-session isolation =="
echo "$(edit_payload "$SID_A" "$REPO/src/x.py")" | bash "$HOOKS/sdd-gate-pretooluse.sh" 2>/dev/null
expect 2 $? "A's own unapproved SDD blocks a repo edit"

echo "$(edit_payload "$SID_B" "$REPO/src/x.py")" | bash "$HOOKS/sdd-gate-pretooluse.sh" 2>/dev/null
expect 0 $? "B is NOT blocked by A's marker (the collision bug)"

echo "$(edit_payload "$SID_A" "$SANDBOX/vault/proposal.md")" | bash "$HOOKS/sdd-gate-pretooluse.sh" 2>/dev/null
expect 0 $? "edits outside repo_path stay allowed"

echo "== Current proposal approval and worktree scope =="
mkdir -p "$SANDBOX/change" "$SANDBOX/worktree"
printf '%s\n' '---' 'design_approved: false' '---' > "$SANDBOX/change/proposal.md"
cat >> "$HOME/.claude/sdd-active-$SID_A" <<EOF
sdd_path=$SANDBOX/change
worktree_path=$SANDBOX/worktree
EOF
# A stale cached approval must not override the actual proposal.
sed 's/design_approved=false/design_approved=true/' "$HOME/.claude/sdd-active-$SID_A" > "$SANDBOX/marker"
cp "$SANDBOX/marker" "$HOME/.claude/sdd-active-$SID_A"
echo "$(edit_payload "$SID_A" "$SANDBOX/worktree/src/x.py")" | bash "$HOOKS/sdd-gate-pretooluse.sh" 2>/dev/null
expect 2 $? "revoked approval blocks edits in a registered worktree despite cached true"
printf '%s\n' '---' 'design_approved: true' '---' > "$SANDBOX/change/proposal.md"
echo "$(edit_payload "$SID_A" "$SANDBOX/worktree/src/x.py")" | bash "$HOOKS/sdd-gate-pretooluse.sh" 2>/dev/null
expect 0 $? "current approved proposal permits worktree edits"
printf '%s\n' 'broken metadata' > "$SANDBOX/change/proposal.md"
echo "$(edit_payload "$SID_A" "$SANDBOX/worktree/src/x.py")" | bash "$HOOKS/sdd-gate-pretooluse.sh" 2>/dev/null
expect 2 $? "unreadable approval fails closed only inside scoped active work"
echo "$(edit_payload "$SID_A" "$SANDBOX/unrelated.txt")" | bash "$HOOKS/sdd-gate-pretooluse.sh" 2>/dev/null
expect 0 $? "bad proposal does not block unrelated files"

echo "== PostToolUse finds the change root for nested specs =="
mkdir -p "$SANDBOX/vault/.claude/scripts" "$SANDBOX/vault/SDD/TEST-2/specs/domain"
cp "$HOOKS/../scripts/validate_sdd.py" "$SANDBOX/vault/.claude/scripts/validate_sdd.py"
printf '%s\n' '---' 'type: proposal' 'ticket: TEST-2' 'title: Fixture' 'propose_tier: unit' 'status: proposed' 'design_approved: false' '---' > "$SANDBOX/vault/SDD/TEST-2/proposal.md"
printf '%s\n' '- [~] 1.1 Missing tier' > "$SANDBOX/vault/SDD/TEST-2/tasks.md"
echo "$(edit_payload "$SID_A" "$SANDBOX/vault/SDD/TEST-2/specs/domain/export.md")" | bash "$HOOKS/sdd-validate-posttooluse.sh" 2> "$SANDBOX/post.log"
expect 0 $? "draft feedback remains informational"
if grep -q 'tasks.md:L1' "$SANDBOX/post.log"; then
  ok "nested spec edit validates the owning change's tasks"
else
  bad "nested spec edit failed to locate owning change"
fi

echo "== Stop gate: per-session isolation =="
printf '{"session_id":"%s"}' "$SID_A" | bash "$HOOKS/sdd-gate-stop.sh" 2>/dev/null
expect 2 $? "A cannot stop on its own red tests"

printf '{"session_id":"%s"}' "$SID_B" | bash "$HOOKS/sdd-gate-stop.sh" 2>/dev/null
expect 0 $? "B can stop while A is red"

printf '{"session_id":"%s","stop_hook_active":true}' "$SID_A" | bash "$HOOKS/sdd-gate-stop.sh" 2>/dev/null
expect 0 $? "A's retry after one block is let through (no stop-hook loop)"

echo "== pr-status backstop: per-ticket, all markers scanned =="
for t in TEST-9 TEST-8; do
  cat > "$HOME/.claude/sdd-delivered-$t" <<EOF
ticket=$t
repo_path=$REPO
base_branch=release/RC
feature_branch=sdd/$t
pr=999
EOF
done

bash_payload() { printf '{"session_id":"%s","tool_name":"Bash","tool_input":{"command":"%s"}}' "$SID_A" "$1"; }

bash_payload "git merge sdd/TEST-8" | bash "$HOOKS/sdd-pr-status.sh" 2>/dev/null
expect 2 $? "blocks on the SECOND marker too (loop does not stop at the first)"

bash_payload "git merge sdd/TEST-9" | bash "$HOOKS/sdd-pr-status.sh" 2>/dev/null
expect 2 $? "blocks merging an unmerged feature branch"

bash_payload "git merge-base sdd/TEST-9 release/RC" | bash "$HOOKS/sdd-pr-status.sh" 2>/dev/null
expect 0 $? "merge-base is read-only, allowed"

bash_payload "git log --oneline -1" | bash "$HOOKS/sdd-pr-status.sh" 2>/dev/null
expect 0 $? "unrelated command allowed"

rm -f "$HOME/.claude"/sdd-delivered-*
bash_payload "git merge sdd/TEST-9" | bash "$HOOKS/sdd-pr-status.sh" 2>/dev/null
expect 0 $? "no markers => fail open"

echo "== --check mode is fail-closed =="
bash "$HOOKS/sdd-pr-status.sh" --check >/dev/null 2>&1
expect 1 $? "--check without a ticket refuses"

bash "$HOOKS/sdd-pr-status.sh" --check TEST-9 >/dev/null 2>&1
expect 1 $? "--check with no marker for that ticket refuses"

echo
[ "$FAILED" = 0 ] && { echo "all gate checks passed"; exit 0; }
echo "gate checks FAILED"; exit 1
