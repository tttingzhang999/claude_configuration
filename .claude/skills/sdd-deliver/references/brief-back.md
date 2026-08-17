# /brief-back — the ownership ritual (anti-automation)

The point of brief-back is **ownership**: the pipeline can design, implement, verify,
and deliver, but the human must still be able to _account for_ the change. This is the
one step deliberately designed to resist automation — the agent asks, the human answers,
and the agent reflects the answer back against what was actually built.

It is a **ritual, not a gate**: it never blocks delivery or the status flow. Its only
output is `briefback.md`. If the user skips, record "skipped" and move on.

## When

Immediately after the draft PR is opened (context is still fresh), decoupled from the
async PR merge.

## The 3 questions (generated from `decision-log.md` + the diff)

Generate one concrete question per axis, grounded in _this_ change (name the real
module / decision / risk — never generic):

1. **Why this design?** — "Why did we choose <approach in design.md> over <the rejected alternative>?"
2. **The trade-off** — "What did that choice cost us? What did we give up?"
3. **Where it's most likely to break** — "If this pages someone at 3am, where does the failure start?"

## How feedback works

- Ask the questions; take the user's (usually verbal) answers.
- Compare each answer to the implementation, `design.md`, and `review.md`:
  - **Solid** → affirm briefly.
  - **Gap** → point to the specific file/line/decision the answer missed. Don't lecture; show where to look.
  - **Wrong** → surface the contradiction with evidence, and (per the vault rule) if the user can't account for a load-bearing decision, tell them which artifact to re-read rather than answering for them.
- The agent's job is to _challenge and locate_, not to hand over the answer.

## `briefback.md` (SDD folder)

```markdown
---
ticket: <ticket>
type: briefback
created: <YYYY-MM-DD>
---

## Q1 — Why this design?

- asked: <question>
- answered: <the user's answer, or "skipped">
- feedback: <solid | gap@<file:line> | wrong: <contradiction>>

## Q2 — Trade-off

...

## Q3 — Where it breaks

...

## Follow-ups

- <anything the user should re-read / revisit; blank if none>
```

## Feeds write-back

`briefback.md` is one of the 6 learning sources — where the user reveals what they
actually understand and own is exactly where the durable learnings are. See
`write-back.md`.
