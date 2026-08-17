---
project: _template
participants: [Your Name, PM]
cooked: true
keypoints_synced: true
action_items_synced: true
created: 2026-07-09
tags: [meeting, template]
---

```table-of-contents

```

> [!note] 範例 meeting
> 會議記錄格式範例。會後 `cooked: false` 表示待 LLM 整理；`cook-meeting` 抓未 cooked 的會議 → 正式記錄、抽 keypoints、同步 Action Items 到 WIP → 標 `cooked: true` 與對應 `*_synced`。

## 決議

- `PROJ-101` rate limiting 本期做，先 in-memory。
- 配額預設 `60 req/min`，待 PM 最終確認。

## Action Items（→ 已同步）

- Your Name：完成 rate limiter 核心。
- 追蹤 @PM 確認配額值。
