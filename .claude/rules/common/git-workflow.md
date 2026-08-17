# Git Workflow

## Commit Message Format

Follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>[optional scope]: <description>

<optional body>
```

Types: feat, fix, docs, style, refactor, perf, test, chore, ci

Breaking change: add `!` after the type/scope, or write `BREAKING CHANGE: <description>` in the footer.

Note: Attribution disabled globally via ~/.claude/settings.json.

## Pull Request Workflow

When creating PRs:

1. Analyze full commit history (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Draft comprehensive PR summary
4. Include test plan with TODOs
5. Push with `-u` flag if new branch

### PR Body Template (fallback when repo has no template)

**A repo PR template always wins** — check `.github/pull_request_template.md` (and `PULL_REQUEST_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE/*.md`, `docs/`) first and use its headings/order/checkboxes verbatim, mapping content into the closest sections. Only when no template exists, use this 4-section format:

```markdown
## Background

<1-3 sentences. The "why" — the problem this PR solves. Lead with the problem, not
the solution. Link an issue/ticket only if the user provided one — never invent.>

## What's Changed

- <Core behavior change or structural decision — NOT a file edit>
- <Good: "Reject empty payload before DB write to prevent malformed rows">
- <Bad: "Added validateInput function in utils.ts">

<Skip formatting, comment edits, import reordering, lock-file bumps.>

## Reference

<Mermaid flowchart ONLY for non-trivial new flow (branching, state machine,
request path, multi-step pipeline) — not for trivial CRUD/single-function fixes.
Otherwise list user-provided references (Jira/Linear/design doc). Omit if neither applies.>

## Test Plan

- [ ] <Verification step reviewer can tick>

<Omit for doc-only/trivial/fully test-covered changes; instead note coverage in
Background, e.g. "Covered by existing tests in X_test.go".>
```

**Title format:** `[<base-branch>] <type>: <description>` (imperative, ≤72 chars, no trailing period). Use the Conventional Commits prefix only if the repo already does; otherwise a plain imperative title.

**Do not fabricate** motivation, ticket numbers, or issue links not present in commits/code. If intent is ambiguous, ask before composing.

> For the full development process (planning, TDD, code review) before git operations,
> see [development-workflow.md](./development-workflow.md).
