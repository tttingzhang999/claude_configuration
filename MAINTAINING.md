# Maintaining this repo

This repo is a **sanitized export** of a private Obsidian vault. Never edit the
synced files here by hand — edit them in the vault, then re-run the sync. The
only files authored directly in this repo are: `README.md`, `MAINTAINING.md`,
`LICENSE`, `.gitignore`, `sync-from-vault.py`, `sanitize-rules.example.py`, and
`templates/`.

## The scrubbing rules live outside git

`sync-from-vault.py` reads its rules from **`sanitize-rules.local.py`**, which is
gitignored and required — the sync exits 2 without it.

```bash
cp sanitize-rules.example.py sanitize-rules.local.py   # once, then fill it in
```

That file is the only place naming the real people, employer, clients, hosts and
local paths being removed. **It must never be committed.** A committed mapping is
a complete index of exactly what the export exists to hide — including names that
are not yours to publish. Everything else here, `sync-from-vault.py` included, is
scanned by the same fail-closed check that guards the exported content.

## Update flow

```bash
cd ~/code/personal/claude-configuration   # this repo
VAULT_ROOT="/path/to/your/private/vault" uv run sync-from-vault.py
git diff                                   # review every change
git add -A && git commit -m "chore: sync config from vault"
git push
```

`sync-from-vault.py`:

1. Loads `SUBSTITUTIONS` + `FORBIDDEN` from `sanitize-rules.local.py`.
2. Wipes the managed mirror paths (`.claude/`, `install.sh`, the scaffolding
   files) and recopies them from the vault per its `MANIFEST`.
3. Skips machine state and caches (`EXCLUDE`): `__pycache__`, `.ruff_cache`,
   `*/state/`, `promptlingo/data/`, `vocab/data/`, `settings.local.json`.
4. Sanitizes every copied text file (org/client/colleague names, Slack ids,
   personal paths → placeholders).
5. Replaces two files wholesale from `templates/` (`repos.yaml`,
   `cook-messages/config.json`) so real registries never ship.
6. **Fail-closed final scan**: if any forbidden token survives, it prints the
   offending `file:line` and exits non-zero — nothing is committed.

## When the scan fails

Add a rule to `SUBSTITUTIONS` (source token → placeholder) and, if needed, widen
`FORBIDDEN`, then re-run. The scan skips only `templates/` and the
`sanitize-rules.*` files, because those legitimately name the mapping.

Each rule is a `(kind, pattern, replacement)` tuple. Use kind `"word"` for a bare
identifier — a name, a ticket prefix, a Slack id — and `"re"` for a raw regex.
Do not hand-write `\b`: regex counts `_` as a word character, so `\bNAME\b` does
not match `NAME` inside markdown emphasis (`_as NAME_`), and because the scan
once reused the same `\b`, it reported clean on a file that still carried a real
name. Kind `"word"` treats punctuation and underscores as edges, and the
sanitizer and the scan share one implementation of it.

## Adding a new skill / file to the export

Add its vault-relative path to `MANIFEST`. If it is a whole skill dir, add the
skill name to `PORTABLE_SKILLS`. If it carries a real registry/config, add it to
`WHOLESALE` with a matching example under `templates/`. Re-run and review the
diff — the fail-closed scan is the backstop, not a substitute for reading it.
