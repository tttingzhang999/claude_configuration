# Apply loop — per-task TDD (language-agnostic)

The methodology each per-task subagent follows. The RED → GREEN → REFACTOR →
coverage shape is borrowed from the `tdd-workflow` skill, but **rewritten
language-agnostic** — that skill is hardcoded for TS/React (jest / vitest /
playwright / Next.js / Supabase). Here the test stack is decided by the **target
repo's `CLAUDE.md`**, not assumed.

> The apply loop (pause conditions, mark-complete flow) is ported from OpenSpec
> `src/core/templates/workflows/apply-change.ts` at OpenSpec v1.13.2 (`db230978`), with CLI calls removed.

## Detect the stack (from the target repo, never assume)

For genuinely non-code tasks with explicit document/link/config validation, use those commands without requiring a language manifest or test framework. Mark inapplicable code checks N/A with reasons. Missing tools for an applicable check still block; a refactor is code work and needs regression tests.

Repo instructions are constraints, not evidence of completion. Report conflicts with the approved plan or explicit user choices; never silently change scope or treat context as a passing result.

Before writing any test, determine how this repo tests — in order:

1. The target repo's `CLAUDE.md` / `AGENTS.md` (test command, framework, coverage rule).
2. Manifest + convention:
   - Python → `pytest` (run via `uv run pytest` when the repo uses uv; per the vault rule, never bare `python`/`python3`).
   - Node/TS → the `test` script in `package.json` (vitest / jest / node:test).
   - Go → `go test ./...`. Rust → `cargo test`. Others → the ecosystem default.
3. If still unknown → **pause and ask** (don't guess a framework).

Coverage threshold: whatever the repo's `CLAUDE.md` states; otherwise the global
`~/.claude/rules/common/testing.md` default (**80%**).

## The per-task cycle

For a behavior task `N.M`, perform the whole cycle below. A docs/config/non-behavior task uses its named verification instead; record TDD/coverage as N/A with a reason when genuinely inapplicable. A refactor still needs regression evidence. Legacy separate RED/GREEN tasks must be reconciled into complete behavior tasks through `/sdd-propose --update` before dispatch, never silently skipped.

1. **RED — write the failing test first.**
   - Translate the relevant spec scenario (WHEN/THEN) into a test in the repo's framework.
   - Test _observable behavior_, not implementation details.
   - Cover the edge/error cases the scenario implies (empty, null, boundary, failure path).
2. **Run tests — confirm RED.** The new test must fail for the right reason (feature missing), not a syntax/import error. If it errors instead of failing, fix the test until it fails cleanly.
3. **GREEN — minimal implementation.** Write the least code that makes the test pass. No speculative abstraction, no features beyond the task (Simplicity First).
4. **Run tests — confirm GREEN.** The new test passes and **no previously green test regressed**.
5. **REFACTOR (optional).** Improve names/dedupe **only while keeping every test green**. Re-run after.
6. **Coverage check.** If the repo/global rule sets a threshold, confirm the changed code meets it; add tests for uncovered branches if not.

**Hard rule: once a test is green, do not edit the test to fit the code.** If the
test looks wrong, that's a design issue → pause (see below), don't silently weaken it.

**Hard rule: mark a task `- [x]` only when its stated outcome and verification are complete.** Partly done, stubbed, or deferred does not count as complete.

## Scope discipline (per Surgical Changes)

- Edit only files **inside the target repo** (`repo_path`). Never write SDD
  artifacts or vault files from an apply subagent.
- Every changed line traces to this task. Don't "improve" adjacent code.
- Remove only imports/vars your change made unused.

## Pause conditions (report to the orchestrator, don't push through)

- The task is unclear or under-specified → ask for clarification.
- The task needs work **beyond what the spec and tasks describe** → name the added scope and ask. Never absorb it silently, and never drop, narrow, defer, or grant an exception to specified behavior just to make the task fit.
- Implementation reveals a **design issue** (the spec/design is wrong or incomplete) → stop and suggest updating the artifact, don't patch around it.
- An error/blocker you can't resolve → report it.
- Tests won't go green after focused attempts → hand back (the orchestrator counts consecutive failures; ≥3 stops the run per the global max-retries-3).

## Report back (subagent → orchestrator)

Return a compact result: which task, files touched, the test command run, RED-then-GREEN
confirmed (yes/no), final test outcome (**green / red**), coverage if measured, and any
pause reason. The orchestrator uses `green/red` to update the session marker's
`tests_green` and to decide whether to mark the task `- [x]`.
