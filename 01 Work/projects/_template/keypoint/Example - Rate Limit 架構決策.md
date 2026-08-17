---
project: _template
type: keypoint
created: 2026-07-09
source:
  - "[[01 Work/projects/_template/SDD/PROJ-101-rate-limiting/design]]"
tags:
  - architecture
  - technical
  - template
---

```table-of-contents

```

> [!note] 範例 keypoint
> 知識點筆記格式範例：架構 / 決策 / bug 根因。frontmatter 需 `project` / `type: keypoint` / `source` / `tags`。內容主要用繁中，技術名詞留英文。

## 決策：限流後端先 in-memory

- token bucket + `RateLimitStore` 介面抽象。
- in-memory 下實際上限 ≈ `配額 × 實例數`，範圍已知、可接受。
- 換 Redis 時只換 `RateLimitStore` 實作，middleware 不動。

## 相關

- [[01 Work/projects/_template/SDD/PROJ-101-rate-limiting/design]]
- [[README]]
