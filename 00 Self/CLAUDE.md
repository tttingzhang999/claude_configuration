# CLAUDE.md — `00 Self/` (the distilled source-of-truth layer for the self)

This layer is the **source** for the entire vault: it describes **Your Name as a person** (engineering identity, coding conventions, writing & communication voice), not any single output. All other outputs (`02 Knowledge/` notes, `03 Writing/` articles, `01 Work/` meetings and progress updates) should stay consistent with this layer.

## Agent Loading Guide (must read)

**Before any agent starts work, read the relevant file in this layer first**, then begin:

| What you're doing                                                                             | Read first                                                                         |
| --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Writing / changing code, giving technical advice, code review                                 | [[Coding Conventions]]                                                             |
| Writing work documents (PRD / tech doc / spec), PR descriptions, Slack updates                | [[Writing & Communication Voice]]                                                  |
| Anything requiring judgment "from Your Name's point of view," deciding delegate vs. do it yourself | [[Engineering Self]]                                                               |
| Writing personal articles / blog                                                              | The `write-article` skill's `style-guide.md` (the voice file — don't copy it here) |

## Maintenance Principles

- This layer is **confirmed by Your Name personally** — agents may draft but must not unilaterally rewrite established positions
- Content is built via an "interview method": agent asks question by question → synthesizes → Your Name corrects
- **No duplication** with existing assets: the writing voice lives in `write-article/style-guide.md`; this layer only links to it
- Update each file's `last_reviewed` frontmatter field on any significant change
