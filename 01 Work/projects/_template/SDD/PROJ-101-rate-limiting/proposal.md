---
ticket: PROJ-101
title: Add per-user API rate limiting
type: proposal
project: _template
jira: "https://your-org.atlassian.net/browse/PROJ-101"
propose_tier: integration
status: proposed
design_approved: false
created: 2026-07-09
---

## Why

The public API has no traffic control. A single authenticated user can exhaust downstream capacity and degrade service for everyone. We need per-user quotas that reject excess traffic with `429`.

## What Changes

- Add a token-bucket rate-limiting middleware.
- Enforce a default quota of `60 requests/minute` per authenticated user, overridable by config.
- Return `429 Too Many Requests` with a `Retry-After` header when the quota is exceeded.
- Exempt health-check and internal endpoints from rate limiting.

## Capabilities

### New Capabilities

- `rate-limit`: per-user request throttling with a configurable quota and `429` responses. See `specs/rate-limit.md`.

### Modified Capabilities

<!-- None. No existing requirement changes. -->

## Impact

- **Affected code**: the request middleware chain — the limiter must sit after auth and before routing.
- **Dependencies**: needs a shared counter backend; starts in-memory, later swappable for Redis.
- **Risk**: wrong middleware ordering can disable limiting or wrongly block health checks.
- **Backward compatibility**: clients within quota see no behavior change.
