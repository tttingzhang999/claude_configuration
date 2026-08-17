---
name: write-article
description: Generates blog articles that match the author's personal writing style through a human-gated iterative pipeline. Use when the user provides a topic, outline, or raw material and wants an article co-written — the skill drives outline → material decisions → draft → critique loops, with human approval gates between stages.
argument-hint: [topic or outline]
allowed-tools: Read, Grep, Glob, Write, Edit, WebSearch, WebFetch, Agent, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Write Article Skill

幫 Your Name 寫個人 blog 文章 — 人工掌舵、AI 執行的迭代管線。產出必須像 Your Name 親自寫的。絕對不能讀起來像 ChatGPT 寫的，這條凌駕一切。

本檔只做流程編排，規則與參考資料在 `reference/` 下三份檔案，按階段載入，不要在開頭全讀：

| 檔案                                                          | 內容                                                         | 載入時機                   |
| ------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------- |
| `${CLAUDE_SKILL_DIR}/reference/diataxis-article-framework.md` | Diátaxis 型別框架：四象限定義、Compass 判斷、對應階段 0 定位 | 階段 0 決定文章定位時      |
| `${CLAUDE_SKILL_DIR}/reference/style-guide-core.md`           | 生成端正例與硬規則：定位、幻覺防護、語言、Markdown 格式      | 階段 3 生成時              |
| `${CLAUDE_SKILL_DIR}/reference/style-guide-verify.md`         | 檢查端負例：Rule A–K 檢查清單                                | 階段 4 傳給 critique agent |

產出寫入 `03 Writing/drafts/[slug].md` — 這是整條管線的迭代溝通平台，階段 1–4 的產出與修改都在此檔案更新，階段 5 交付時移至 `03 Writing/blog/`。檔案開頭放一個 callout 標示目前所在階段與待確認事項。

## Important Rules

- 數字紀律
  - 素材裡的數字是全流程唯一可用的數字來源。
  - 素材不足時根據事實蒐集。可能是程式碼、網頁資訊、官方文件、API 文件、MCP、WebSearch 等。不允許 AI 自行生成數字。
  - 任何階段都禁止生成無 Reference 的數字、版本號、定價 — 缺就寫 `[待補：___]`。

## 階段 0：選題、蒐集原始素材

收斂主題 + 蒐集原始素材（經驗描述、真實數據、log、code、截圖）。
決定文章定位（Tutorial / How-to / Explanation / Reference）、TA、TL;DR。

產出以下內容：

- 選用框架與理由：
  - 技術文章可參考 `reference/diataxis-article-framework.md`
  - 非技術文章
    - Concept：論點驅動、觀點討論、沒有實作細節
    - Thinking：思考過程、經驗分享、沒有實作細節
- TA：這篇為哪一個具體的人寫
- TL;DR：1~2 句話整理文章摘要
- 預計要使用的原始素材:
  - 原始素材來源（程式碼、截圖、log、官方文件、網頁文章、MCP 查詢結果等）
  - 任何引用的數據來源
  - 任何引用的技術文件或官方文件

完成後等待使用者確認與迭代

## 階段 1：定位與大綱

產出以下內容：

- 大綱：每個 Section 要傳遞的內容、架構、引用的素材等，所有後續實作該 Section 需要用到的所有 Context，使用 Unordered list 整理

完成後等待使用者確認與迭代

## 階段 2：文章內非純文字 Context 設計

對通過的大綱提案，在文章中設計在哪邊建議可以插入哪些非純文字 Context（圖、code、數據盤點），以及放在哪個段落。提案時要說明理由：

- 圖：依「非平凡流程才畫」（分支、狀態機、請求路徑、pipeline）提案位置與型式，Mermaid 優先
- Code：提案哪些段落放 code（原則：最小但完整可跑 + 預期輸出），實際 code 由使用者提供或指定來源
- 數據盤點：列出大綱中每個技術錨點及其來源；無來源者標示 `[待補：___]`

完成後等待使用者確認與迭代

## 階段 3：初稿生成

1. 讀 `reference/style-guide-core.md`
2. 取樣風格錨點：從 `03 Writing/blog/`（或 `content/blog/`）讀至少 3 篇既有文章 — 同類別優先、至少 1 篇跨類別、整篇讀完。輸出觀察筆記（句長分佈、開頭 pattern、段落長度、技術密度）。寫作對齊觀察筆記，core 只當 guardrail
3. 技術事實驗證：涉及 API 名稱、行為、版本時用 `context7:resolve-library-id` + `context7:query-docs` 或 WebSearch 查證，驗證過的資訊才能寫入
4. 寫初稿：只用階段 0–2 已確認的素材；缺的數據保留 `[待補]`；每個 section 服務「TL;DR」；重點放句尾、舊資訊開頭新資訊結尾

## 階段 4：批判迭代

啟動 Agent（subagent_type: general-purpose），傳入：

1. 草稿全文
2. `reference/style-guide-verify.md` 全文
3. 階段 1 通過的大綱與「TL;DR」
4. 指令：逐 Rule A–K 檢查，依 `reference/style-guide-verify.md` 輸出格式回報

完成後：**依回報套用改寫 → 更新草稿 → 重跑本階段 critique**，直到 **Rule J(幻覺/未查證事實)為零、且無 CRITICAL** 才進階段 5。每一輪先給使用者變更預覽並等確認再改寫。

## 階段 5：交付

寫入 `03 Writing/blog/[slug].md`（或使用者指定路徑），frontmatter：

```yaml
---
title: ""
description: ""
date: "YYYY-MM-DD"
tags: []
category: ""
author: "Your Name"
image: ""
draft: false
---
```
