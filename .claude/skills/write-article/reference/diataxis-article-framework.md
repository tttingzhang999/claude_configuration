# Diátaxis Article Framework

> Distilled from https://diataxis.fr/ (fetched 2026-07-08). Purpose: give Stage 0 of the write-article pipeline a systematic way to pick the article's type, and give the critique loop (Stage 4) a way to detect type-mixing. This is a decision aid, not documentation theory — load it only when deciding article positioning.

## Core Concept

Diátaxis organizes technical writing into **four distinct forms**, positioned on two axes:

- **Action vs. Cognition** — does the text serve _doing_ (practical steps) or _thinking_ (propositional knowledge)?
- **Acquisition vs. Application** — is the reader _studying_ (learning something new) or _working_ (applying skill they already have)?

Two binary axes → four quadrants:

| Type             | Informs   | Serves the reader's | One-line definition                                                                        |
| ---------------- | --------- | ------------------- | ------------------------------------------------------------------------------------------ |
| **Tutorial**     | Action    | Acquisition (study) | A lesson: take the learner by the hand through an experience that is guaranteed to succeed |
| **How-to guide** | Action    | Application (work)  | Directions: help an already-competent reader accomplish a specific real-world goal         |
| **Reference**    | Cognition | Application (work)  | Description: accurate, complete, neutral information, free of instruction and opinion      |
| **Explanation**  | Cognition | Acquisition (study) | Discussion: illuminate _why_ — context, trade-offs, alternatives, design reasoning         |

Each type answers a different reader need. A reader in "work" mode is annoyed by teaching; a reader in "study" mode is lost without it.

## The Compass (decision procedure)

When unsure which type an article is, answer two questions **in order**:

1. Does the content inform **action** (steps to do) or **cognition** (things to know)?
2. Does it serve the reader's **acquisition** of skill (study) or **application** of skill (work)?

Then read the answer off the table above. The compass works as a truth-table: it converts a fuzzy "what kind of article is this?" into two binary choices. Use it as a course-correction tool whenever a draft feels like it's pulling in two directions — the usual cause is that the two questions have different answers for different sections.

## The Critical Rule: One Article, One Type

Per Diátaxis, **crossing or blurring the boundaries between types is the root of most documentation problems.** For this pipeline it is a hard rule:

- Pick exactly one type in Stage 0, before outlining.
- If the material genuinely spans two types, **split into two articles** or demote the secondary type to a short section with a link out (state the assumption inline in 1–2 sentences, then link to a separate article that covers it in full).
- The most common failure: a Tutorial or How-to bloated with explanation. Fix: keep inline context to 1–2 sentences, move the _why_ to a separate Explanation piece or an appendix.

### Type-mixing smells (for the Stage 4 critique loop)

| Smell                                                          | Likely violation                                               |
| -------------------------------------------------------------- | -------------------------------------------------------------- |
| A How-to that pauses to explain internals or history           | How-to leaking into Explanation                                |
| A Tutorial offering choices, flags, or alternatives mid-lesson | Tutorial leaking into Reference/How-to — a lesson has one path |
| An Explanation that turns into numbered setup steps            | Explanation leaking into Tutorial/How-to                       |
| A step sequence with no guaranteed, verifiable outcome         | Tutorial failing its own contract                              |
| Neutral spec-like listing inside an opinion piece              | Concept/Explanation leaking into Reference                     |

## Mapping to This Skill's Stage 0 Taxonomy

Stage 0 of SKILL.md uses **Concept / Tutorial / How-to / Explanation**. This is a deliberate adaptation of Diátaxis for personal blog writing, not a different framework:

| Stage 0 type | Diátaxis equivalent                 | Adaptation note                                                                                                                                                                                                                 |
| ------------ | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tutorial     | Tutorial                            | Identical contract: following along **must** succeed. Every step verified, one path, expected output shown                                                                                                                      |
| How-to       | How-to guide                        | Identical: assume competence, go straight at the goal, do not explain principles                                                                                                                                                |
| Explanation  | Explanation                         | Identical: why, trade-offs, alternatives. Deep-dives and postmortems live here                                                                                                                                                  |
| Concept      | (Explanation quadrant, opinion-led) | Blog-specific: viewpoint and discussion with **no implementation detail**. Diátaxis has no "opinion piece" type; Concept occupies the cognition/acquisition quadrant but leads with a thesis rather than a technology           |
| —            | Reference                           | **Intentionally dropped.** Pure reference (neutral, complete, spec-like) does not work as a blog article; official docs own that quadrant. If material is reference-shaped, link to the official docs instead of rewriting them |

Practical consequence for Stage 0: if the compass says "Reference", that is a signal the topic is not (yet) a blog article — either reframe it as an Explanation (why it is designed this way) or a How-to (how to use it for a goal), or drop it.

## Per-Type Contracts (what Stage 1 outlines must honor)

- **Tutorial** — reader is a learner. Concrete steps, one path, no options, minimal context, visible result at every stage. Success is the reader's success, not coverage.
- **How-to** — reader is competent and mid-task. Start from the goal, not from setup. Omit anything the goal doesn't need. No teaching, no theory.
- **Explanation** — reader wants understanding. Safe to approach from multiple directions, compare alternatives, admit uncertainty, discuss history and trade-offs. This is the only type where opinion about design is on-topic.
- **Concept** — reader wants a perspective. Thesis first, argument-driven sections, examples serve the argument. No step sequences, no API detail.

## Source

- https://diataxis.fr/ — framework overview and quadrant map
- https://diataxis.fr/compass/ — the two-question decision procedure
- https://diataxis.fr/start-here/ — type definitions and the boundary-blurring warning
