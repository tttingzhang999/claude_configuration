# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These bias toward caution over speed. For trivial tasks, use judgment.

---

Owner: Your Name
Role: Software Engineer

---

## Obsidian as Second Brain, Claude Code as engine

The Obsidian vault is the source of truth for who Your Name is (engineering identity, coding conventions, communication voice), ongoing work, knowledge notes, and personal projects. Any session that needs to act _as Your Name_, judge a tradeoff from Your Name's standpoint, or touch a personal/work project should drill into it.

- **Vault root:** `{base_url}` — start from `Context Map.md`, which explains every layer.
- **Path placeholders:** vault-tracked files never hardcode an absolute path. They write `{base_url}` (vault root) and `{home}` (this machine's home dir). `install.sh` resolves both per machine into `~/.claude/rules/00-machine-paths.md` — a generated, machine-local file that is never committed and never symlinked, picked up by the automatic load of `~/.claude/rules/`. Expand a placeholder before passing any path to a tool.
- **Before acting as Your Name:** read `00 Self/` — `Coding Conventions.md`, `Writing & Communication Voice.md`, `Engineering Self.md`.
- **Real repos + conversation history:** resolve a project/repo name to its real local path with the `repo-router` skill.

---

## 1. Think Before Coding

**Don't assume. Surface tradeoffs. Ask when uncertain.**

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop and ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If 200 lines could be 50, rewrite it.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- IMPORTANT: Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- Unrelated dead code: mention it — don't delete it.
- Remove imports/variables/functions that YOUR changes made unused.

The test: every changed line traces directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → write tests for invalid inputs, make them pass
- "Fix the bug" → write a test that reproduces it, make it pass
- "Refactor X" → ensure tests pass before and after

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

Strong criteria let you loop independently. Weak criteria ("make it work") need clarification.

**Max retries on failure: 3.** When a fix→run cycle keeps failing:

- Count = consecutive failed cycles for the _same_ task. Reset the counter when the failure mode genuinely changes (new error ≠ same wall).
- On exhaustion: STOP — don't thrash. Report what each attempt tried, root-cause hypotheses, and the specific blocker, then ask how to proceed.
- Never bypass to force green (no `--no-verify`, no skipping tests). Diagnose the root cause instead.

---

## Project-Specific

- **Docs lookup:** Use Context7 MCP or Agent Skills — not web search.
- **Git:** No Claude/Anthropic references in messages.
- **Python:** Ensure `pyproject.toml` has a valid `build-system` section.

Additional rules — generic, apply to every project (vault-only rules are imported from the vault's own root `CLAUDE.md`):

@rules/common/coding-style.md
@rules/common/git-workflow.md
@rules/common/development-workflow.md
@rules/common/testing.md
@rules/common/security.md
@rules/common/hooks.md
@rules/chinese-output.md

Language-scoped rules under `rules/python/` and `rules/typescript/` bind by file extension via their `paths:` frontmatter and load only when a matching file is in play.
