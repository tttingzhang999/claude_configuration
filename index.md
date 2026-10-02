```table-of-contents

```

> Vault 入口。`02 Knowledge/` 與 `03 Writing/` 的內容由 `.base` 動態視圖產出，不手動維護。
> 維護方式請見 [[CLAUDE#Karpathy Wiki Workflows]]。

## 三層結構

| 區塊                     | 內容                                       | 動態視圖                                              |
| ------------------------ | ------------------------------------------ | ----------------------------------------------------- |
| **01 Work/**             | 工作專案（projects / meetings / research） | —                                                     |
| **02 Knowledge/**        | 知識管理（Wiki Layer，LLM 維護）           | [[index.base]]                                        |
| **03 Writing/**          | 個人文章（drafts / workspace / blog）      | [[03 Writing/writing-board.base\|writing-board.base]] |
| **04 English Learning/** | promptlingo 每日報告 + 單字 + 語法分類     | [[english-board.base]] · [[Glossary Index]] · [[grammar.base]] |
| **\_raw/**               | Raw Sources（不可修改原始素材）            | —                                                     |
| **archived/**            | 舊內容封存                                 | —                                                     |

---

## 02 Knowledge — 動態視圖

![[index.base]]

---

## 03 Writing — 文章看板

![[03 Writing/writing-board.base]]

---

## 系統檔案

- [[CLAUDE]] — Schema layer（vault 規則 + LLM workflow）
- [[_log]] — Chronological log（ingest / query / lint 紀錄）
- [[_raw/README|_raw/]] — Raw sources 使用說明
- [[promptlingo]] — 每日英文學習 skill（Krashen i+1 + Leitner SRS）

---

## 📦 _raw — 最近 ingest

| 日期       | 類型 | 標題                           | 對應 Wiki            |
| ---------- | ---- | ------------------------------ | -------------------- |
| 2026-05-05 | gist | [[20260505-karpathy-llm-wiki]] | [[LLM Wiki Pattern]] |
