---
ticket: PROJ-101
type: decision-log
created: 2026-07-09
---

> Human-authored. Record decisions as you make them. The agent may append
> challenges under "Challenges", never the decisions.

## Decisions

- 2026-07-09 — 限流後端先 in-memory，介面抽 `RateLimitStore`，日後換 Redis 只換實作。(human)

## Challenges

- (agent-appended) in-memory 下實際上限隨實例數放大，跨實例配額不共享——多實例部署時是否可接受？
