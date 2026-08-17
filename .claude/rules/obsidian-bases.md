---
paths:
  - "**/*.base"
---

# Obsidian Bases

When you need to "list a category of notes," **prefer a `.base` dynamic view** over a hand-written markdown table:

- [[index.base]] — full-topic view of `02 Knowledge/` (grouped by folder, recently updated, gallery)
- [[03 Writing/writing-board.base|writing-board.base]] — kanban board for `03 Writing/` articles (draft/workspace/blog)

To display a view inside a `.md` file:

```markdown
![[index.base]]
![[index.base#最近更新]]
```

When you need to add a new dynamic view, use the `obsidian-bases` skill to write it, and follow the YAML quoting rules (if a formula contains double quotes, wrap the outer layer in single quotes).
