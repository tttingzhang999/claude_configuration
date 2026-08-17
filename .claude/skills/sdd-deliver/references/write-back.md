# Write-back — the learning checkpoint (human-in-loop)

Distilled from `continuous-learning-v2`'s _model_ (atomic, evidence-backed,
confidence-weighted, project↔global scope) — **without its machinery**: no background
observer, no `observe.sh` hooks, no homunculus store, no 0.3–0.9 auto-scoring. Learning
happens as **one deliberate checkpoint per delivered ticket**, gated by human approval.

Two independent tracks. Track 1 is work-tracking; Track 2 is knowledge.

## Track 1 — Action Items + progress (via `cook-progress`)

- Update `Action Items - WIP.md` / `Action Items - Done.md` and note progress against the roadmap.
- Governed by `cook-progress`'s own rules: **personal work items only** (rejects PM-led / team / ExampleClient-window items), and its **mandatory preview → approve → write**.

## Track 2 — Learning checkpoint (knowledge, not work items)

Not bound by the "personal work items only" rule — learnings are engineering knowledge.

### The 6 evidence sources

| Source              | Yields                                             |
| ------------------- | -------------------------------------------------- |
| `design.md`         | chosen approach, trade-offs, rejected alternatives |
| `decision-log.md`   | human decisions + agent challenges                 |
| `review.md`         | Stage 4 CRITICAL / WARNING / SUGGESTION            |
| `sdd/<ticket>` diff | what actually changed                              |
| `briefback.md`      | the human's answers — the richest ownership signal |
| CI gotchas          | red→green struggles worth remembering              |

### The learning unit (extraction-stage intermediate only — do NOT embed in keypoint notes)

```yaml
trigger: <one situation — when this applies>
action: <one takeaway — what to do / what's true>
evidence: <ticket + source line, e.g. design.md §2 / briefback Q3>
confidence: tentative | moderate | strong # coarse tag, not an auto number
domain: architecture | testing | gotcha | convention | ...
scope: project | global
```

Keypoint notes keep their existing free-form format; the schema is only the shape used
while extracting and previewing candidates.

### Scope routing

| scope         | criterion                                                        | landing spot                                                                                              |
| ------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **project**   | specific to this repo/project (architecture, convention, gotcha) | `01 Work/projects/<PROJECT>/keypoint/<title>.md` — existing keypoint format, `source:` → the SDD artifact |
| **global**    | cross-project engineering pattern                                | `00 Self/Coding Conventions.md` — appended as a **candidate**, flagged for human confirmation             |
| **synthesis** | worth a wiki note (cross-source)                                 | `02 Knowledge/<topic>/` — via the standard wiki ingest workflow                                           |

### The 5 steps (mirrors `cook-progress`: preview → approve → write)

1. **Extract candidates** — scan the 6 sources → atomic candidates (trigger/action/evidence/proposed scope). Draft only.
2. **Dedup** — check existing `keypoint/` + `Coding Conventions.md`; if a candidate matches an existing learning's trigger, propose **bump confidence / merge**, not a duplicate.
3. **Preview → approve** (MANDATORY) — show the candidate list; the user picks which to keep, edits scope/wording. **Nothing persists without approval** — this is the anti-automation guard: the human decides what enters their brain.
4. **Persist approved** — project → `keypoint/`; global candidate → `Coding Conventions.md` (flagged candidate); synthesis → `02 Knowledge/`.
5. **Confidence over time (across tickets)** — a learning that recurs and the user keeps → bump its confidence tag; one the user contradicts → mark contested / lower. **project → global promotion is agent-suggested, human-decided** (never automatic).

## Hard rules

- No learning is written anywhere without the user approving the preview.
- `decision-log.md` is human-authored; write-back reads it but never writes decisions into it.
- Confidence is a coarse human-facing tag, adjusted by recurrence + non-contradiction — never an auto-computed number.
- If nothing is worth capturing, say so and write nothing (still do Track 1).
