---
name: code-reviewer
description: Comprehensive code review of local uncommitted changes or a GitHub PR. Size-gates the diff — tiny diffs review inline single-pass; larger diffs dispatch a multi-agent Workflow (scout → parallel reviewers over 7 categories + git-history + CLAUDE.md-compliance → adversarial refute-verify to drop false positives). Runs project validation (typecheck/lint/test/build), forms an APPROVE/REQUEST-CHANGES/BLOCK decision, and writes a review artifact. Report-only — never posts to GitHub. Use on "code review", "review this PR", "review my changes", "review the diff", or /code-reviewer.
argument-hint: "[pr-number | pr-url | blank for local review]"
allowed-tools: Read, Grep, Glob, Bash, Workflow
---

# Code Review

> Base structure adapted from ECC's `code-review` (PRPs-agentic-eng by Wirasm). Multi-agent
> fan-out, size-gating, and adversarial refute-verify adapted from smith's `review-pr-general`.
> This is a report-only reviewer: it never writes code and never publishes to GitHub.

**Input**: `$ARGUMENTS`

---

## Mode Selection

- `$ARGUMENTS` contains a PR number, PR URL, or `--pr` → **PR Review Mode**.
- Otherwise → **Local Review Mode** (uncommitted changes).

Both modes share Steps 2–8; only Step 1 (fetch) differs.

---

## Step 0 — Preflight

```bash
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || echo "NOT_REPO"
```

- **NOT_REPO** → report "Not inside a git repository. `cd` into your project first." and stop.
- **PR mode only** — also verify `gh`:
  ```bash
  command -v gh >/dev/null 2>&1 || echo "MISSING_GH"
  gh auth status >/dev/null 2>&1 || echo "NOT_AUTHED"
  ```
  - **MISSING_GH** → "GitHub CLI not installed (`brew install gh`)." Fall back to a local review of the diff if possible, else stop.
  - **NOT_AUTHED** → "GitHub CLI not authenticated. Run `gh auth login`." Stop.

---

## Step 1 — Fetch the Diff

### Local Review Mode

```bash
git diff --name-only HEAD          # changed files (staged + unstaged)
git diff HEAD                       # the diff to review
git diff --stat HEAD
```

If no changed files → "Nothing to review." Stop.

### PR Review Mode

Resolve the PR from input (number → use as-is; URL → extract number; branch → `gh pr list --head <branch>`), then:

```bash
gh pr view <N> --json number,title,body,author,baseRefName,headRefName,isDraft,state,changedFiles,additions,deletions
gh pr diff <N>
```

- PR not found → "Could not find PR #<N>. Verify the number and repo." Stop.
- Store: title, body, author, base/head branch, **isDraft** (affects strictness), the full diff.

---

## Step 2 — Size-Gate (inline vs Workflow)

Measure the diff you already fetched:

```bash
echo "$DIFF" | grep -cE '^[+-]'        # changed lines (added + removed)
echo "$DIFF" | grep -cE '^diff --git'  # changed files
```

- **Tiny diff** — changed lines < 100 **AND** files ≤ 3 → **inline single-pass** (Step 4a). The multi-agent overhead isn't worth it.
- **Larger diff** — ≥ 100 changed lines **OR** ≥ 4 files → **dispatch the Workflow** (Step 4b).

---

## Step 3 — Build Context

1. **Project rules** — read `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/`, contributing guidelines. **Project rules override the general principles below.**
2. **Planning artifacts** — check `.claude/prds/`, `.claude/plans/`, `.claude/reviews/` (and legacy `.claude/PRPs/{prds,plans,reviews}/`) for context on this change.
3. **Intent** — parse the PR description (or the user's stated goal) for goals, linked issues, test plans.
4. **Scope-alignment check** — does the diff match its stated intent? Unrelated changes, missing pieces, or scope creep → record a **CRITICAL** finding about the misalignment.
5. **Categorize** changed files: source / test / config / docs.

---

## Step 4a — Inline Single-Pass (tiny diffs)

Read each changed file **in full** (not just hunks — you need surrounding context; follow calls into unchanged code to check compatibility). Walk the **7 categories** (Step 4c) on the changed code.

Then **self-refute before reporting**: for every CRITICAL/HIGH you're about to raise, argue the opposing case in one line ("could this be intentional / already handled / a false positive?"). Drop anything you can't defend. Go to Step 5.

---

## Step 4b — Dispatch the Workflow (larger diffs)

This is a **sanctioned Workflow opt-in** — these instructions direct you to call the Workflow tool. Invoke by **scriptPath** (do not paste the script inline). Pass the diff you already fetched so agents don't re-run `gh`/`git`:

```
Workflow({
  scriptPath: "$HOME/.claude/skills/code-reviewer/code-reviewer.workflow.js",
  args: {
    pr_number: <number or null>,
    base: "<base branch, e.g. origin/main>",
    title: "<PR title, or branch name>",
    body: "<PR description, or ''>",
    is_draft: <true|false>,
    diff: "<the full diff string from Step 1>"
  }
})
```

**What it does** (the script orchestrates this — you don't):

- **Scout** — maps files, change-type, languages, diff↔description alignment, which CLAUDE.md files exist.
- **Review** — parallel reviewers: the 7 categories (each fed its own criterion) + a **git-history** agent (`git log`/`git blame` for regressions) + a **CLAUDE.md-compliance** agent.
- **Verify** — every CRITICAL/HIGH gets an **adversarial refute agent**; false positives are dropped. MEDIUM/LOW pass through.

It runs in the background; a `<task-notification>` arrives on completion. Returns `{ summary_hint, findings: [{file, line, severity, category, problem, fix}] }`. Empty `findings` → report a one-line clean verdict. Then go to Step 5.

---

## Step 4c — The 7 Review Categories

Apply to **changed code only** (mention pre-existing issues but don't count them):

| Category               | Check for                                                                                                                                    |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Correctness**        | Logic errors, off-by-one, nil/None deref, edge cases, races, resource leaks, error handling (swallowed / wrong-type / should-propagate)      |
| **Type Safety**        | Type mismatches, unsafe casts, `any` usage, missing generics, call-boundary compatibility                                                    |
| **Pattern Compliance** | Naming/structure/idioms diverging from surrounding code; new deps duplicating existing ones (read neighbor files to confirm)                 |
| **Security**           | At trust boundaries: input validation, injection, secret exposure, SSRF, path traversal, XSS, unsafe deserialization                         |
| **Performance**        | N+1 queries, unbounded loops/growth, missing indexes/timeouts, memory leaks, large payloads, over-engineering                                |
| **Completeness**       | Missing tests, missing error handling, incomplete migrations, missing docs for public APIs                                                   |
| **Maintainability**    | Dead code, magic numbers, deep nesting (>4), functions >50 lines mixing levels, unclear naming, DRY violations, misleading/outdated comments |

**Severity:**

| Severity     | Meaning                                | Gate action                  |
| ------------ | -------------------------------------- | ---------------------------- |
| **CRITICAL** | Security vuln or data-loss risk        | Must fix — BLOCK             |
| **HIGH**     | Bug/logic error likely to cause issues | Should fix — REQUEST CHANGES |
| **MEDIUM**   | Quality issue or missing best practice | Fix recommended              |
| **LOW**      | Style nit / minor suggestion           | Optional                     |

---

## Step 5 — Validate

Detect project type from config files and run only what applies. Record pass/fail/skipped for each.

- **Node/TS** (`package.json`): `npm run typecheck || npx tsc --noEmit`; `npm run lint`; `npm test`; `npm run build`
- **Rust** (`Cargo.toml`): `cargo clippy -- -D warnings`; `cargo test`; `cargo build`
- **Go** (`go.mod`): `go vet ./...`; `go test ./...`; `go build ./...`
- **Python** (`pyproject.toml`/`setup.py`): `pytest` (use `uv run` if the project uses uv)

Skip validation for doc-only/trivial diffs; note it as skipped.

---

## Step 6 — Decide

| Condition                             | Decision                  |
| ------------------------------------- | ------------------------- |
| Zero CRITICAL/HIGH, validation passes | **APPROVE**               |
| Only MEDIUM/LOW, validation passes    | **APPROVE with comments** |
| Any HIGH or validation failure        | **REQUEST CHANGES**       |
| Any CRITICAL                          | **BLOCK**                 |

Special cases: **Draft PR → always COMMENT** (only flag blocking bugs + structural issues; skip missing docs/tests/cleanup). Docs/config-only → lighter review. Explicit `--approve`/`--request-changes` flag → override decision but still report all findings.

---

## Step 7 — Report

Write the artifact to `.claude/reviews/<pr-N | local-YYYYMMDD>-review.md` (use legacy `.claude/PRPs/reviews/` only if the repo already does). Findings use a tight one-line anchor form; add a minimal ` ```diff ` block only when the fix isn't obvious.

**Finding line:** `<file>:L<line> — <problem>. <fix>.`

```markdown
# Code Review: <PR #N — TITLE | Local changes>

**Reviewed**: <date> · **Author**: <author> · **Branch**: <head> → <base>
**Decision**: APPROVE | APPROVE WITH COMMENTS | REQUEST CHANGES | BLOCK

## Summary

<1-2 sentences: what the change does + overall verdict>

## Findings

### CRITICAL

- <file>:L<line> — <problem>. <fix>. _(or "None")_

### HIGH

- ...

### MEDIUM

- ...

### LOW

- ...

## Validation Results

| Check      | Result                |
| ---------- | --------------------- |
| Type check | Pass / Fail / Skipped |
| Lint       | Pass / Fail / Skipped |
| Tests      | Pass / Fail / Skipped |
| Build      | Pass / Fail / Skipped |

## Files Reviewed

<file — Added/Modified/Deleted>
```

**Reporting rules:** all CRITICAL shown (no cap); cap MEDIUM/LOW at ~7 most impactful, add `(+N minor items omitted)` if more. Drop praise unless asked. Keep each finding to one line + optional diff.

---

## Step 8 — Output

```
<PR #N: TITLE | Local review>
Decision: <APPROVE | APPROVE_WITH_COMMENTS | REQUEST_CHANGES | BLOCK>
Issues: <c> critical, <h> high, <m> medium, <l> low
Validation: <pass>/<total> checks passed
Artifact: .claude/reviews/<...>-review.md
Next steps: <contextual suggestions>
```

---

## PUBLISH — DISABLED

Report-only. **Never** run `gh pr review` / `--approve` / `--request-changes` / `--comment`, post inline comments, or submit any GitHub review event. **Never modify files.** If the user explicitly wants findings posted, ask for confirmation first — otherwise stop at the artifact.

---

## What NOT to Flag

- **Style preferences** (braces, tabs/spaces, trailing commas) — unless inconsistent _within the PR itself_.
- **Generated code** (protobuf, OpenAPI codegen) — only flag if the generation input is wrong.
- **Test verbosity / DRY in tests** — repetition that aids readability or isolation is fine.
- **Draft PRs** — only blocking bugs + structural issues.
- **Pre-existing code** — only flag changed lines; note surrounding problems as "pre-existing" without counting them.
- **Obvious future work** — a TODO with a planned follow-up isn't an incompleteness finding.
- **Linter/formatter territory** (unused imports, formatting) — mention only if it signals a deeper problem (e.g. an incomplete refactor).

---

## Error Handling

- **No changes** → "Nothing to review." Stop.
- **PR not found** → verify number/repo. Stop.
- **`gh` not authed** → `gh auth login`. Stop.
- **Cannot read a source file** → skip its snippet, note "Could not read `<file>`.", continue.
- **Base branch undetectable** → ask for the PR number or ensure `origin/main`/`origin/master` exists. Stop.
- **Large PRs (>50 files)** → warn about scope; review source first, then tests, then config/docs.
