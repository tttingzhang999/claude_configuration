# Staging 檔模板（Step C 用）

機器控制欄位放 body 開頭的 `<!--cook-staging ... -->` 註解裡，frontmatter 只留 `reviewed`（append 型）或 `reviewed` + 筆記自身 frontmatter（新筆記）。這樣 Obsidian Properties 面板只顯示 `reviewed` 與筆記正式欄位，不被機器欄位灌爆；註解在 Live Preview / Reading 模式隱藏。時間戳一律 `Asia/Taipei`（`+08:00`）。

**來源標籤 `<來源>`**：Gmail = 寄件人顯示名；Slack = `頻道名 · 發話人`（DM 用 `DM · 發話人`）。Slack 的 body 與 Action Item 尾端附 `Permalink`（`[原訊息](<permalink>)`）供點回原訊息。

## Action Items（append）

```markdown
---
reviewed: false
---

<!--cook-staging
staging: true
source_skill: cook-messages
target_path: "01 Work/projects/<P>/Action Items - WIP.md"
op: append
append_anchor: "## 進行中"
staged_at: 2026-07-06T14:32:00+08:00
-->

- [ ] <具體任務描述>（來源：<來源>）
```

## Meeting / Keypoint（write，新筆記）

```markdown
---
reviewed: false
project: <P>
type: keypoint
source: "<來源>"
tags: [<project-slug>]
---

<!--cook-staging
staging: true
source_skill: cook-messages
target_path: "01 Work/projects/<P>/keypoint/<slug>.md"
op: write
overwrite_existing: false
staged_at: 2026-07-06T14:32:00+08:00
-->

<body，依 01 Work/CLAUDE.md 對應目錄的慣例撰寫>
```

Meeting 筆記的自身 frontmatter 依 `cook-meeting` 的 schema（`date`、`project`、`type: meeting`、`title`、`participants`、`parsed`、`tags`）；Keypoint 依上例（`project`、`type: keypoint`、`source`、`tags`）。
