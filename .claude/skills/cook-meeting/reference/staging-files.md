# reference/staging-files.md

Step 5 產出的兩份 `_staging/` 檔案規格。兩份對應兩個 `target_path`：

- `target_path_1` = raw 檔相對 vault 路徑（例：`01 Work/projects/<PROJECT>/meetings/<file>.md`），內容用 Step 3a
- `target_path_2` = `01 Work/projects/<PROJECT>/Action Items - WIP.md`，內容用 Step 3b

## Slug 規則

把 `target_path` 中的 `/`、空格、結尾 `.md` 都換成 `_`，staging 檔路徑為 `<VAULT_ROOT>/_staging/<slug>.md`。

## 冪等檢查

每份 staging 檔各自先確認 `_staging/<slug>.md` 是否已存在；**已存在就跳過該份**（不覆寫使用者正在 review 的內容），在回報中標註「已存在，跳過」。

## 檔 1 — 正式會議紀錄（`op: overwrite`）

`Write` 到 `_staging/<slug1>.md`。**機器控制欄位放 `<!--cook-staging ... -->` 註解，frontmatter 只留 `reviewed` + 筆記正式欄位**（這樣 Obsidian Properties 面板不會被機器欄位灌爆）：

```markdown
---
reviewed: false
date: <YYYY-MM-DD>
project: <PROJECT>
type: meeting
title: <從檔名或 raw 第一行推斷>
participants:
  - <參與方>
cooked: true
keypoints_synced: true
action_items_synced: true
tags: [meeting, <project-slug>, <topic-tags>]
---

<!--cook-staging
staging: true
source_skill: cook-meeting
target_path: "<target_path_1>"
op: overwrite
overwrite_existing: true
staged_at: <ISO8601 +08:00，例：2026-07-06T14:32:00+08:00>
-->

<Step 3a 的完整 body>
```

## 檔 2 — WIP action items（`op: append`）

若 Step 3b 去重後沒有新增項目 → **不產出**此檔，在回報中註明「無新增 action items」。否則 `Write` 到 `_staging/<slug2>.md`，`append_anchor` 用 Step 2 讀到的 WIP 真實區段標題（通常是 `## 進行中`；沒有該區段時仍寫 `## 進行中`，交給 `cook-staging` 視情況建立）：

```markdown
---
reviewed: false
---

<!--cook-staging
staging: true
source_skill: cook-meeting
target_path: "<target_path_2>"
op: append
append_anchor: "## 進行中"
staged_at: <ISO8601 +08:00>
-->

### <主題>（來源：[[<會議檔名（不含 .md）>]]）

- [ ] ...
```
