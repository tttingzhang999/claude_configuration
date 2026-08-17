# CI ladder + coverage rubric (language-agnostic)

How Stage 3 decides _how deep to check_, keyed off the proposal's `propose_tier`.
The stack (test / typecheck / lint commands) is taken from the **target repo's
`CLAUDE.md`**, never assumed — same detection as `sdd-apply/references/apply-loop.md`.

## The ladder (each rung includes all rungs below it)

| Rung            | What runs                                                                           | Deterministic?                |
| --------------- | ----------------------------------------------------------------------------------- | ----------------------------- |
| **lint**        | format check + linter + typecheck (e.g. `mypy`, `tsc --noEmit`, `clippy`)           | yes                           |
| **unit**        | + unit tests                                                                        | yes                           |
| **integration** | + integration tests (DB, filesystem, cross-module, API contract)                    | yes                           |
| **e2e**         | + end-to-end tests, headless (no live service by hand)                              | yes                           |
| **e2e-live**    | + start the service locally, LLM drives e2e against the running app, then tear down | yes run, LLM-driven scenarios |

`propose_tier` selects the top rung; always climb from **lint** up to that rung.
A lower rung red stops the climb — don't run higher rungs on a red base.

## Stack detection (in order)

1. Target repo `CLAUDE.md` / `AGENTS.md` — explicit test/typecheck/lint commands + coverage rule.
2. Manifest + convention:
   - **Python** → `uv run mypy` (types) + `uv run pytest` (tests); lint `uv run ruff` if configured. Never bare `python`/`python3` (vault rule).
   - **Node / TS** → `package.json` scripts: `lint`, `typecheck` (`tsc --noEmit`), `test` (vitest / jest / node:test).
   - **Go** → `go vet ./...` + `go test ./...`.
   - **Rust** → `cargo clippy` + `cargo test`.
   - Others → the ecosystem default.
3. Still unknown → **pause and ask**; never guess a framework.

Run everything **inside the feature-branch worktree** (`sdd/<ticket>`), never the main tree.
For any long-running / service process, use tmux so logs are reachable.

## Coverage rubric (judge, don't bare-ask)

A numeric percentage alone is a weak judge. Assess coverage on both:

**Numeric** — the changed code meets the threshold from the repo's `CLAUDE.md`, else the
global `~/.claude/rules/common/testing.md` default (**80%**).

**Behavioral (the rubric)** — for the change's specs, is each of these exercised by a test?

- [ ] **Happy path** — every `#### Scenario:` WHEN/THEN has a passing test.
- [ ] **Error paths** — each failure/rejection the spec names is tested (not just the success case).
- [ ] **Boundaries** — empty, null/absent, min/max, first/last, off-by-one edges.
- [ ] **Regression surface** — behavior adjacent to the change still has covering tests (nothing silently broken).

Coverage passes only when **both** the numeric threshold and every rubric line hold.
A gap on any rubric line → add a targeted test (Step 4), don't lower the bar.

## What "red" means (never silence it)

Red = any deterministic rung fails, a gap-filling test exposes a real bug, or coverage
can't reach the bar honestly. Red is **reported and diagnosed**, never masked by
`--no-verify`, `skip`/`xfail`, deleting an assertion, or lowering the threshold.
Max 3 focused retries on the same rung, then stop and hand back (global max-retries-3).
