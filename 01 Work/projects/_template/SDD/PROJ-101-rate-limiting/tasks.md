---
ticket: PROJ-101
title: Add per-user API rate limiting
type: tasks
created: 2026-07-09
---

## 1. Rate limiter core

- [ ] 1.1 `[sonnet]` Write a failing test: `RateLimiter` allows requests within quota and rejects over-quota ones (RED)
- [ ] 1.2 `[sonnet]` Implement the token-bucket `RateLimiter` and the `RateLimitStore` interface to make 1.1 pass (GREEN)
- [ ] 1.3 `[sonnet]` Run unit tests to confirm GREEN and a clean lint

## 2. Middleware wiring

- [ ] 2.1 `[sonnet]` Write a failing integration test: over-quota requests return `429` with a `Retry-After` header (RED)
- [ ] 2.2 `[sonnet]` Implement the middleware, mounted after auth and before routing, to make 2.1 pass (GREEN)
- [ ] 2.3 `[opus]` Add a test proving health-check paths are NOT rate limited (boundary correctness) and make it pass

## 3. Configuration and wrap-up

- [ ] 3.1 `[sonnet]` Make the per-user quota overridable by config, defaulting to `60 req/min`
- [ ] 3.2 `[sonnet]` Run the full integration suite (`propose_tier: integration`) and confirm all tests pass
