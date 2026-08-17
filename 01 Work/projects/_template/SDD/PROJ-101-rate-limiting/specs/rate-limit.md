---
ticket: PROJ-101
capability: rate-limit
type: spec-delta
created: 2026-07-09
---

## ADDED Requirements

### Requirement: Per-user rate limiting

The API SHALL reject authenticated requests that exceed the per-user quota within a rolling one-minute window, and SHALL exempt health-check and internal endpoints from limiting.

#### Scenario: Request within quota is allowed

- **WHEN** a user's request count within the trailing minute is at or below the quota
- **THEN** the request is routed normally and the response is unaffected

#### Scenario: Over-quota request is rejected

- **WHEN** a user exceeds the quota within the trailing minute
- **THEN** the API responds with `429 Too Many Requests` and a `Retry-After` header giving the retry delay in seconds

#### Scenario: Health checks are never limited

- **WHEN** a request targets a health-check or internal endpoint
- **THEN** the limiter is bypassed and the request is never rejected with `429`
