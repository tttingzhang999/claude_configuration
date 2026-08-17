---
project: _template
type: reference
status: active
tags: [meta, agentic-coding, harness, template]
created: 2026-07-09
---

```table-of-contents

```

> [!important] 這是什麼
> `01 Work/projects/` 的**專案骨架範本**，也是 [[Agentic Coding Harness 實作計劃]] M2「Vault State 層」的落地參考。任何新專案照這個結構開；AI（propose / apply / verify skill）以此為讀寫 artifact 的格式契約。`_` 前綴表示它是範本、不是真專案。

## 目錄結構

| 層                       | 用途                                                                      | 誰寫                       | 備註                |
| ------------------------ | ------------------------------------------------------------------------- | -------------------------- | ------------------- |
| `keypoint/`              | 知識點（架構 / 干係人 / 決策 / bug 根因）                                 | 人 + skill 建議            | 沿用既有慣例        |
| `meetings/`              | 會議記錄                                                                  | 人，`cook-meeting` 整理    | 沿用既有慣例        |
| `Session Record/`        | 每日工作筆記（原 `daily/` 更名；`cook-daily-tasks` 已移除，不再自動產生） | 人手寫                     | 沿用                |
| `SDD/{ticket}-{title}/`  | **開發進度四件套**（proposal / design / tasks / specs）                   | propose·apply·verify skill | M2 新增，本範本重點 |
| `Action Items - WIP.md`  | Your Name 個人進行中工作項                                                     | 人 + `cook-progress`       | 沿用                |
| `Action Items - Done.md` | 已完成項（[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) 記法） | 人 + `cook-progress`       | 沿用                |
| `tickets.base`           | SDD 進度看板（掃 `SDD/*/proposal.md`）                                    | 手寫一次，之後自動渲染     | M2 新增             |

## SDD 四件套與生命週期

一個 change = `SDD/{ticket}-{title}/` 一個資料夾，裡面四個檔（線性鏈，缺哪個就是下一步）：

```
proposal.md → design.md → tasks.md → specs/*.md
```

- **proposal.md** — Why / What Changes / Capabilities / Impact，frontmatter 帶 `type: proposal`（`tickets.base` 靠它過濾）、`propose_tier`、`jira`、`design_approved`（gate 用）。
- **design.md** — Context / Goals / Decisions / Risks（架構圖放這）。
- **tasks.md** — `## N` 分節 + `- [ ] N.M`，**TDD 排序**（先 failing test → 實作 → 驗 GREEN），逐 task 標 `[模型]`。
- **specs/\*.md** — delta spec，用 `ADDED / MODIFIED / REMOVED` 標變更，`#### Scenario` 用 WHEN/THEN。

**狀態流**（`proposal.md` 的 `status`）：

```
proposed → approved → applying → verifying → delivered → archived
```

對映 canvas 七階段：Stage 1 產四件套→`proposed`；設計拍板→`design_approved: true` + `approved`；Stage 2 apply→`applying`；Stage 3–4 CI/Review→`verifying`；Stage 5 交付→`delivered`；Stage 6 歸檔→`archived`。

## Tier 類別

| Tier             | 在哪                            | 值                                                   | 給誰用                               |
| ---------------- | ------------------------------- | ---------------------------------------------------- | ------------------------------------ |
| **propose_tier** | `proposal.md` frontmatter       | `lint` / `unit` / `integration` / `e2e` / `e2e-live` | Stage 3 CI 決定查多深                |
| **task tier**    | `tasks.md` 每個 task 的 `[...]` | `sonnet` / `opus`                                     | Stage 2 apply 開 subagent 時指定模型 |

`propose_tier` 是**難度→CI 深度**的階梯（愈難查愈深）；task tier 是**單一 task 用哪個模型**。

## Further Reading

- [[Agentic Coding Harness 實作計劃]] — M2 出處
- [[Agentic Coding 開發流程設計]] — 七階段設計本體
- [[CLAUDE.md]] — vault 全域規則
