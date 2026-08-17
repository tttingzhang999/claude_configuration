# claude-configuration

A sanitized, public snapshot of the agent + LLM-wiki configuration that runs my
personal [Obsidian](https://obsidian.md) "second brain" vault with
[Claude Code](https://docs.claude.com/en/docs/claude-code). It contains the
**setup** — Claude Code skills, rules, hooks, `CLAUDE.md` layers, and the
Karpathy-style LLM-wiki pattern scaffolding — but **none of the private
knowledge, work, or writing content** that lives in the real vault.

The private vault stays local-only; this repo is a curated export produced by
[`sync-from-vault.py`](./sync-from-vault.py). See
[MAINTAINING.md](./MAINTAINING.md) for how it is kept in sync.

## What's inside

```
CLAUDE.md, Context Map.md      # top-level agent instructions + layer map
install.sh                     # symlink the config into ~/.claude/, resolve machine paths
.claude/
  CLAUDE.md                    # behavioral guidelines
  rules/
    common/                    # coding style, git, testing, security, hooks, performance…
    python/, typescript/       # language-scoped rules, bound by `paths:` frontmatter
    *.md                       # vault-specific: file naming, frontmatter, wiki workflows
  hooks/                       # SDD gate hooks, formatter, prompt logging
  scripts/validate_sdd.py      # SDD four-pack validator
  skills/                      # portable Claude Code skills (see below)
00 Self/CLAUDE.md              # identity-layer schema (no personal content)
01 Work/CLAUDE.md              # work-layer schema
01 Work/projects/_template/    # example project scaffolding (SDD four-pack, meetings, keypoints)
03 Writing/writing-board.base  # dynamic view definition
index.md, index.base           # wiki catalog + dynamic view
templates/                     # example configs you copy + fill in
```

### Paths are placeholders

No tracked file hardcodes an absolute path. They write `{base_url}` (vault root)
and `{home}`, and `install.sh` resolves both for the current machine into a
generated, machine-local `~/.claude/rules/00-machine-paths.md` that is never
committed. It defaults to dry-run:

```bash
./install.sh                              # DRY-RUN, prints every action
DRY_RUN=0 PROFILE=personal ./install.sh   # apply
```

`PROFILE=work|personal|all` selects which skills get linked; the other profile's
skills are pruned. Only symlinks pointing into your own vault are ever removed,
and anything replaced is backed up under `~/.claude/backups/`.

### Skills

| Skill                                                                     | Purpose                                                                    |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `sdd-propose` / `sdd-apply` / `sdd-verify` / `sdd-review` / `sdd-deliver` | Spec-Driven Development pipeline (propose → apply → CI → review → deliver) |
| `sdd-orch`                                                                | Pipeline driver: reads the proposal's status, dispatches the next phase    |
| `code-reviewer`                                                           | Multi-agent diff/PR review workflow                                        |
| `write-article`                                                           | Human-gated article writing pipeline                                       |
| `promptlingo` / `vocab`                                                   | English-learning report from your conversations + adaptive vocab quiz      |
| `repo-router`                                                             | Resolve a project name → local repo path + conversation history            |
| `cook-meeting` / `cook-progress` / `cook-messages`                        | Organize meetings, progress, and Gmail/Slack messages into the vault       |
| `cook-staging` / `cook-loop`                                              | Staging-review promotion + the automation loop that drives the cook skills |
| `cook-blog-publish`                                                       | Publish vault articles to a personal blog repo                             |
| `openclaw`                                                                | Configure and debug the OpenClaw chat-to-agent gateway                     |

## Using it

1. Point Claude Code at a directory containing these files, or run `install.sh`
   from it to symlink the pieces you want into your own `~/.claude/`.
2. Copy the example configs and fill in your own values:
   - `templates/repos.example.yaml` → `.claude/skills/repo-router/repos.yaml`
   - `templates/cook-messages.config.example.json` → `.claude/skills/cook-messages/config.json`
3. Skills that operate on a vault read a `VAULT_ROOT` path — `install.sh` fills it
   in from `{base_url}`. Placeholders like `AcmeCorp`, `ExampleProject`,
   `YOUR_SLACK_USER_ID`, and `alice@example.com` are illustrative; replace them
   with yours.

## Notes

- Content notes are primarily written in Traditional Chinese; the machine-facing
  spine (`CLAUDE.md`, `.claude/rules/`, `00 Self/`) is in English.
- Wiki pattern based on Karpathy's
  [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## License

[MIT](./LICENSE)
