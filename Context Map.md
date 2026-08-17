---
tags: [meta, entry-point]
status: active
---

```table-of-contents

```

> [!important] What this is
> The single entry point to Your Name's distilled second brain. It maps every layer and shows how a Claude Code session can, in principle, reach **all** of Your Name's context — identity, work, knowledge, personal projects, real repos, and past conversations. Read this first; drill into the layer the task needs.

## The Layers

| Layer         | Path                   | What it holds                                                                               | Who maintains it                                         |
| ------------- | ---------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| **Self**      | `00 Self/`             | Your Name's engineering identity, coding conventions, communication voice — the distilled source | Your Name-confirmed; agents may draft, never override stances |
| **Work**      | `01 Work/`             | Work projects: meetings, keypoints, action items, daily logs, speaking                      | Your Name + cook-* skills                                     |
| **Knowledge** | `02 Knowledge/`        | Wiki layer (Karpathy pattern) — synthesized notes                                           | LLM-maintained                                           |
| **Writing**   | `03 Writing/`          | Personal articles (drafts / workspace / blog)                                               | Your Name + write-article skill                               |
| **English**   | `04 English Learning/` | promptlingo reports                                                                         | promptlingo skill                                        |
| **Life Plan** | `05 Life Plan/`        | Life planning, company                                                                      | Your Name                                                     |
| **Raw**       | `_raw/`                | Raw sources, append-only, verbatim                                                          | append-only                                              |

## Read-Before-Acting (by task)

| Doing this                                                               | First read                               |
| ------------------------------------------------------------------------ | ---------------------------------------- |
| Writing / changing code, code review, technical advice                   | [[Coding Conventions]]                   |
| Work documents (PRD / tech doc / spec), PR descriptions, Slack updates   | [[Writing & Communication Voice]]        |
| Any judgment "standing in Your Name's shoes" — tradeoffs, self-do vs delegate | [[Engineering Self]]                     |
| Personal articles / blog                                                 | `write-article` skill's `style-guide.md` |

## Reaching Real Code & Past Conversations

Vault notes _describe_ projects; they don't contain the source. To reach ground truth:

- **Real repos:** use the `repo-router` skill to resolve a project/repo name → this machine's real local path (`~/code/{personal,work,side}`), then Read/Grep. Registry: `.claude/skills/repo-router/repos.yaml` (`name`/`path`/`remote`/`host`/`vault_project`/`description`). Human-readable view: [[Repo Registry]].
- **Conversation history:** the same skill locates a repo's `~/.claude/projects/<slug>` directory (slug = the working directory's absolute path with `/` replaced by `-`).
- **This vault's own history:** `~/.claude/projects/-Users-you-vault/`.

## Conventions & Workflows

- Global rules & skill routing: root [[CLAUDE.md]]; directory-scoped rules in each subdir's `CLAUDE.md`.
- Formatting / frontmatter / wiki workflows: `.claude/rules/`.
- Language: machine-facing spine (this file, `CLAUDE.md`, `.claude/rules/`, `00 Self/`) is English; personal layers stay Traditional Chinese.

## Further Reading

- [[Coding Conventions]] · [[Writing & Communication Voice]] · [[Engineering Self]]
- [[Repo Registry]]
- [[index]]
