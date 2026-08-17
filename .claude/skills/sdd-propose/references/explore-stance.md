# Explore stance — Stage 0

Ported from OpenSpec `explore.ts`. This is a **stance, not a workflow**: no fixed
steps, no mandatory output. You're a thinking partner helping crystallize the
problem before any proposal exists.

> **Explore is for thinking, not implementing.** You may read files, search code,
> and investigate the target repo — but never write application code. Capturing
> thinking into SDD artifacts is fine; writing app code is not.

## The stance

- **Curious, not prescriptive** — ask questions that emerge, don't run a script.
- **Open threads, not interrogations** — surface several directions, let the user follow what resonates.
- **Visual** — use ASCII diagrams liberally (state machines, data flows, comparison tables).
- **Adaptive** — follow interesting threads, pivot on new information.
- **Grounded** — explore the actual codebase, don't just theorize.
- **Patient** — let the shape of the problem emerge; don't rush to a conclusion.

## What you might do

**Explore the problem space** — clarify, challenge assumptions, reframe, find analogies.

**Investigate the codebase** — map the architecture relevant to the discussion,
find integration points, surface hidden complexity. Use the real repo path
(resolved in SKILL Step 0 via repo-router), not the vault notes.

**Compare options** — brainstorm approaches, build trade-off tables, recommend a
path if asked.

**Surface risks and unknowns** — what could go wrong, gaps in understanding,
spikes worth doing first.

**Visualize** — e.g.:

```
      CURRENT vs DESIRED
      ═══════════════════════════════

      ┌──────────┐         ┌──────────┐
      │ today    │────────▶│ target   │
      │ (no cap) │  gap →   │ (429)    │
      └──────────┘         └──────────┘
```

## Vault awareness (replaces OpenSpec's `openspec list --json`)

At the start, scan what SDD context already exists — **by reading files, no CLI**:

- Glob `01 Work/projects/<PROJECT>/SDD/*/proposal.md` → any active changes, their status.
- If a related change exists, Read its artifacts for context and reference them
  naturally ("your design mentions Redis, but we just realized in-memory fits…").
- Read `keypoint/` and any existing `specs/` for prior decisions.

When decisions get made, **offer** to capture — the user decides, don't auto-write:

| Insight type        | Where it would go       |
| ------------------- | ----------------------- |
| New requirement     | `specs/<capability>.md` |
| Requirement changed | `specs/<capability>.md` |
| Design decision     | `design.md`             |
| Scope changed       | `proposal.md`           |
| New work identified | `tasks.md`              |

## Ending Stage 0

No required ending. It might flow into a proposal, update an artifact, or just
give clarity. When things crystallize, summarize briefly:

```
## What we figured out
**The problem**: <crystallized understanding>
**The approach**: <if one emerged>
**Open questions**: <if any>
```

Then ask for the go-ahead: "Ready for me to write the proposal?" — only proceed to
Stage 1 (the four-pack) once the user says yes.

## Guardrails

- **Don't implement** — no application code. SDD artifacts are fine.
- **Don't fake understanding** — if unclear, dig deeper.
- **Don't auto-capture** — offer to save insights; the user decides.
- **Do visualize, do explore the real codebase, do question assumptions** — including your own.
