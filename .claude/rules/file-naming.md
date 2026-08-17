# File Naming & Wikilinks

## No Emoji in Filenames (MUST)

- **Filenames must NOT start with (or contain) an emoji.** Name notes by their plain title only — e.g. `Python Decorator.md`, `API 系統架構.md`, `assume.md`.
- This applies to every layer (`00 Self/`, `01 Work/`, `02 Knowledge/`, `03 Writing/`, `04 English Learning/`, `archived/`, vault-root notes) and to any file a skill generates.
- Categorize notes by **directory + `tags:` frontmatter**, not by a filename emoji prefix.
- When renaming/creating a note, if the intended name has a leading emoji, drop the emoji and the following space.

## Wikilinks

- Internal links use the plain note title: `[[Note Title]]` (no emoji, since filenames carry none).
- For custom display text: `[[Python Decorator|裝飾器]]`
- Every note should have at least 3 meaningful wikilinks
- End with a "Further Reading" section linking back to related notes and [[index]]

## Language & Format

- **Primary language**: Traditional Chinese for content notes (`02 Knowledge/`, `03 Writing/`, etc.); technical terms may remain in English. The machine-facing spine (`CLAUDE.md`, `.claude/rules/`, `00 Self/`, `Context Map.md`) is in English — see the Language Policy in the root `CLAUDE.md`.
- **TOC**: add a ` ```table-of-contents ``` ` block at the top of every note
- **No H1**: Obsidian automatically uses the filename as the title, no need to repeat it with `#`
- **Code blocks**: use a language identifier (````python`, ` ```yaml`…)
- **No hard-wrapping (MUST)**: write each paragraph, list item, and table row as ONE line, however long. Do not break prose at 80/100 columns — Obsidian soft-wraps, and hard breaks make later edits and diffs worse. Applies to every generated file, including skill output (SDD four-packs, meeting records, reports).
