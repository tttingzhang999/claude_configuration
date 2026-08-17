# Done.md changelog 格式規範

`Action Items - Done.md` 採 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) +
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) 格式。**每一次 cook-progress =
一個版本 release**：該次所有 `completed` 項合成一個版本區塊，不逐項標日期、不用 checkbox。

## 版號判定（LLM 依該批完成項性質決定）

起始 `0.0.0`。讀 Done.md 最上方第一個 `## [X.Y.Z]` 當現行版；沒有（空檔 / 舊格式）→ 視為 `0.0.0`。
一批混合時取**最高影響者**：

| 該批內容                                          | bump                | 範例                         |
| ------------------------------------------------- | ------------------- | ---------------------------- |
| 大階段完成 / 交付里程碑                           | **major** — X+1.0.0 | MVP 上線、大版交付 → `1.0.0` |
| 新功能 / 新能力（Added，或重大 Changed）          | **minor** — x.Y+1.0 | 新增匯出功能 → `0.3.0`       |
| 小修正 / bug / 文件 / 小調整（Fixed、小 Changed） | **patch** — x.y.Z+1 | 修 timezone bug → `0.2.1`    |

首次寫入（現行 `0.0.0`）通常落在 `0.1.0`（minor）。

## 版本區塊格式

- **Header**：`## [X.Y.Z] - YYYY-MM-DD - <Title>`
  - 日期 = 該次 cook-progress 日期（沒指定用 today）
  - Title = 一句話概括該批完成內容
- **Sections**：六類 —— `Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`
  - **該次沒有對應項目的類別就不列出**
  - 順序固定照上面六類的先後
- **條目**：`- **<重點>**: <描述>`
  - 無 checkbox、無逐項日期
  - 有 notes 連結就在句尾帶 `[[<wikilink>]]`
  - 無法歸類的 completed 項 → 預設歸 `Changed`
- **排序**：newest-first —— 新版本區塊 prepend 到 intro note 之後、所有既有版本之上

## Worked example

```markdown
## [0.2.0] - 2026-07-14 - Rate Limiting 與專案骨架

### Added

- **Rate limiting**: 實作 `PROJ-101` 的限流中介層，proposal 與設計已拍板 [[SDD/PROJ-101-rate-limiting/proposal]]。

### Changed

- **專案骨架**: 建立初始目錄結構與 CI 設定。

## [0.1.0] - 2026-07-09 - 初始化

### Added

- **Repo 建立**: 從 template 建立專案 repo 與基礎 README。
```

## Done.md 新建模板

````markdown
---
project: <PROJECT>
last_updated: <YYYY-MM-DD>
---

```table-of-contents

```

> [!note]
> The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
> and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
````

（依 vault 規則：intro 用 `> [!note]` callout、不加 H1、保留 TOC 區塊。第一次寫入時把首個版本區塊
prepend 到 intro note 之後。）
