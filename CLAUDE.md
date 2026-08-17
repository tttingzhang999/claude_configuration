# CLAUDE.md

Global rules for the Obsidian vault. For subdirectory specifics, see the corresponding `CLAUDE.md` and `.claude/rules/`.

> [!important] Entry point
> This vault is Your Name's distilled "second brain". Start from `[[Context Map]]` (vault root) — it explains every layer and how to reach all of Your Name's context (identity, work, knowledge, real repos + conversation history).

## Vault Overview

Personal knowledge base. Covers backend, infra, AI/ML, AWS, security, and personal writing. Follows the [Karpathy LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — see [[LLM Wiki Pattern]].

```
00 Self/          # Distilled source layer (engineering identity / coding conventions / communication voice)
01 Work/          # Work projects (details in 01 Work/CLAUDE.md)
02 Knowledge/     # Wiki Layer, fully maintained by the LLM
03 Writing/       # Personal articles (drafts / workspace / blog)
04 English Learning/  # promptlingo output
05 Life Plan/     # Life planning (details in 05 Life Plan/CLAUDE.md)
_raw/             # Raw Sources, append-only, must not be modified
archived/         # Archived, not actively maintained
```

> [!important] Read the Self layer before starting
> Writing/changing code → first read [[Coding Conventions]]; writing work documents/PR/Slack → first read [[Writing & Communication Voice]]; making a tradeoff from Your Name's standpoint → first read [[Engineering Self]]. Details in `00 Self/CLAUDE.md`.

Vault-only rules — imported here rather than from `.claude/CLAUDE.md`, so they don't load in non-vault projects:

@.claude/rules/file-naming.md
@.claude/rules/frontmatter.md
@.claude/rules/wiki-workflows.md
@.claude/rules/obsidian-bases.md

> [!note] Language Policy
> The **machine-facing spine is English**: every `CLAUDE.md`, everything under `.claude/rules/`, the `00 Self/` identity layer, and `Context Map.md`. This is the context Claude reads on every run — English keeps it precise and token-efficient.
> **Personal thinking layers stay Traditional Chinese**: `02 Knowledge/`, `03 Writing/`, `04 English Learning/`, `05 Life Plan/`, and `_raw/`. User-facing string examples inside rules also stay in Chinese.

## Real Repos & Conversation History

Vault notes describe repos; they do not contain the code. To read **actual source** (verify an implementation, trace a bug, check architecture), use the `repo-router` skill to resolve a project name into this machine's real local path, then Read/Grep — don't guess from notes.

- Registry (single source of truth): `.claude/skills/repo-router/repos.yaml` — `name`, `path` ($HOME-relative), `remote`, `host`, `vault_project`, `description`. Repos live under `~/code/{personal,work,side}`.
- Human-readable view: [[Repo Registry]] (generated from `repos.yaml`).
- After cloning/moving a repo, re-run `uv run .claude/skills/repo-router/scripts/scan.py` (curated `vault_project`/`description` are preserved, keyed by remote).
- The same skill also locates a repo's `~/.claude/projects/<slug>` conversation-history directory.

## Commit Workflow (must read)

**After any change (edit, add, delete), proactively ask whether to commit** — do not end silently.

- Ask format: "Changes complete, commit? Suggested message: `<type>: <description>`" — message format per `.claude/rules/common/git-workflow.md`
- Only run `git commit` after the user agrees; if declined, leave the working tree untouched
- **Exception (user pre-authorized)**: `cook-loop` auto-tick writes commit automatically without asking; but it may only add the files that tick wrote — never `git add -A`
- **This repo is local-only, no remote**: do not attempt `git push` / `git pull` / `git fetch`, and do not ask about pushing
- **Formatting is automatic — never run Prettier by hand.** The `PostToolUse` hook `.claude/hooks/prettier-format.sh` formats every file Write/Edit touches. Config: `.prettierrc` (`proseWrap: "preserve"` — prose is never re-wrapped); `.prettierignore` excludes `_raw/`, `archived/`, and `.claude/settings.json` (the app rewrites that one itself). Note Prettier also honours `.gitignore`, so ignored paths stay untouched.

## Skill Usage (must read)

Before modifying vault content, use the matching skill instead of hand-writing markdown — each skill's own `description` carries its triggers.

> **Skill model specification**: the SKILL.md frontmatter `model` field only accepts an **alias** (`opus` / `sonnet` / `haiku` / `inherit`) or a **full model ID** (e.g. `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`). It does not accept `/model` nicknames like `haiku-4.5`. This vault's `promptlingo` is pinned to `model: haiku` (cost consideration).

## Mandatory Markdown Rules

- **No emoji in filenames or wikilinks** — plain title only (`Python Decorator.md`, `[[Python Decorator]]`). Full rules in `.claude/rules/file-naming.md`.
- Always use `> [!type]` callout syntax (`note`, `tip`, `warning`, `important`, `example`, `bug`, `question`, `todo`) — don't use plain blockquotes to mark key points
- Use `![[...]]` for embeds, `[[...]]` for links; images can specify width `![[image.png|600]]`
- Use LaTeX for math: `$inline$` / `$$block$$`
- Mermaid diagrams: when linking a node to a note, add `class NodeName internal-link;`
- Use YAML frontmatter; use a `tags:` array rather than inline `#tag`

### Don't

- Don't wrap an entire raw source in a `>` blockquote — use a callout or embed instead
- Don't use inline HTML for speed — Obsidian may not support it
- Don't hand-write a list of notes a `.base` can generate (e.g. manually listing all `02 Knowledge/` notes) — prefer a dynamic view: [[index.base]] for `02 Knowledge/`, [[03 Writing/writing-board.base|writing-board.base]] for articles. Details in `.claude/rules/obsidian-bases.md`.

## Python Execution (must read)

**No `python3` / `python` — always `uv run`.**

- Bash: `uv run scripts/foo.py` ✅ / `python3 scripts/foo.py` ❌
- Scripts with external dependencies: add PEP 723 inline metadata at the top
  ```python
  #!/usr/bin/env -S uv run --script
  # /// script
  # requires-python = ">=3.11"
  # dependencies = ["pyyaml", "anthropic"]
  # ///
  ```
- Pure stdlib: still use `uv run`, with `dependencies = []`
- SKILL.md `allowed-tools` should use `Bash(uv *)`, not `Bash(python3 *)`
