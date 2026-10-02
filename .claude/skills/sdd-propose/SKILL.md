---
name: sdd-propose
description: >-
  Plan or revise an SDD change in the Obsidian vault. Explore the real repo, write proposal/specs/design/tasks, and assign CI depth and task models. Use --update to reconcile an existing plan and invalidate stale approval; use --explore for discussion only. Handles explicit skip_specs for changes without behavior changes. Triggers: sdd propose, plan this feature, 開一張 SDD, 幫這張票做提案. Never implements application code.
argument-hint: "[<project>] [<ticket|description>] [--explore] [--update] [--list] [--status <ticket>]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, TodoWrite
model: inherit
---

# sdd-propose

**This is a task command, not reference material. Once you've read it, start executing from Step 0.**

Turn a ticket or a request into an SDD four-pack living in the vault, ready for M4 apply to pick up. This covers **Stage 0 (frame the problem) + Stage 1 (design the SDD)** of [[Agentic Coding Harness 實作計劃]].

> [!note] Milestone legend (the "M" numbers used throughout the SDD family)
> M3 propose (this skill) → M4 apply → M5 verify + review → M6 deliver.

> [!important] Three red lines (violate → stop)
>
> 1. **Never write application code.** Stage 0–1 produce only SDD artifacts (Markdown); they never touch the target repo's source. Implementation is M4 apply. If the user asks you to write code directly → remind them "finalize the proposal first; implementation goes through apply."
> 2. **Specs live in the vault; zero footprint in the target repo.** The four-pack always goes to `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`. **Never** add any file to the target repo. Read project conventions from the repo's existing `CLAUDE.md` (fallback: `package.json` / `pyproject.toml`); never introduce a new config file.
> 3. **Zero compute script.** The linear chain's list / status / next are decided entirely by you reading and globbing files — never write or invoke any `sdd.*` script. The only script you may run is the existing `validate_sdd.py` (Step 5 validation).

## Triggers

- `/sdd-propose <project> <ticket|description>` — explicit
- `/sdd-propose` (no args) — infer from the conversation / cwd / open IDE files
- `/sdd-propose --list` — scan every project's SDD, list each one's status + next step, then stop
- `/sdd-propose --status <ticket>` — report a single change's chain state + next step, then stop
- `/sdd-propose ... --explore` — Stage 0 only (thinking partner); do not produce the four-pack
- `/sdd-propose <project> <ticket> --update` — follow `references/update-flow.md` instead of the new-proposal flow
- Natural language: "open an SDD", "write a proposal/design for this ticket", "propose a change", "plan this feature", "開一張 SDD", "幫這張票做提案", "sdd propose"

## Planning order and completeness

```
proposal.md  →  specs/<capability>.md  →  design.md  →  tasks.md
```

Use this order to draft ordinary changes. It does not prove completeness: compare every declared capability to its spec. With explicit `skip_specs: true`, the specs step is intentionally N/A. For existing-plan revisions use --update. On entry, scan artifacts and apply the shared contract:

| Present                        | Next step                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------- |
| (empty)                        | proposal                                                                        |
| proposal.md                    | specs                                                                           |
| proposal.md + all declared specs (or explicit skip) | design                                                                          |
| + design.md                    | tasks                                                                           |
| all applicable artifacts       | proposal complete → hand to apply (M4); a human flips `design_approved` to true |

`specs/` is ready only when every declared capability has its corresponding valid delta; a single matching file is insufficient. An explicit valid skip_specs opt-out needs no specs.

---

## Flow

Let `VAULT_ROOT = {base_url}` — resolve `{base_url}` via `rules/00-machine-paths.md` before passing any path to a tool.

Read `.claude/skills/sdd-propose/references/planning-contract.md` on entry for artifact applicability, shared validation/task parsing, review freshness, and durable PR identity. Its `skip_specs` exception applies wherever this skill says four-pack/specs. Read-only list/status modes do not advance work. For backward transitions or plan edits, use that reference's `update-flow.md`; do not bypass phase ownership.

### Step 0 — Locate (resolve project / repo / ticket / chain state)

1. **PROJECT**: infer from `$ARGUMENTS` / conversation / cwd; if unsure → `AskUserQuestion` listing the subdirectories under `01 Work/projects/` (excluding `_template`).
2. **Target-repo conventions**: use `repo-router`'s `repos.yaml` (`.claude/skills/repo-router/repos.yaml`) to resolve the real repo path where `vault_project == <PROJECT>`.
   - Found → Read that repo's `CLAUDE.md` (fallback: `package.json` / `pyproject.toml` / `go.mod`) to infer language, test framework, and conventions. These drive the technical decisions and tier judgments in the artifacts.
   - No mapping → mark "repo not registered, conventions unknown"; ask the user during Stage 0 or fall back to the vault's existing specs. **Do not create a config file because of this.**
3. **ticket + slug**:
   - A Jira key is given (e.g. `PROJ-101`) → read the ticket (Atlassian MCP or `jira-automation`) for its title / description / acceptance criteria.
   - Only a description → agree a ticket key with the user (no formal ticket → use `<PROJECT-UPPER>-<short>` or ask the user for one).
   - `slug` = kebab-case of the title. **SDD folder** = `01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>/`.
4. **Scan the chain state**: Glob that folder and compare capabilities against specs using the shared contract. If --update was requested, read `references/update-flow.md`, execute it, and stop this new-proposal flow. For opted-in canonical-spec projects, read `../sdd-deliver/references/spec-sync.md` and capture/recover baselines before authoring deltas.
   - Folder exists with partial artifacts → **resume** at the unfinished step (don't rewrite finished ones unless asked).
   - `--list`: Glob `01 Work/projects/*/SDD/*/proposal.md`, Read each frontmatter, print a table (ticket / title / status / design_approved / next step), then **stop**.
   - `--status <ticket>`: report only that change's chain state + next step, then **stop**.

### Step 1 — Stage 0: explore / frame the problem (thinking partner)

> Read `references/explore-stance.md` and adopt its stance. **Think, don't implement**: you may read code, search, and draw ASCII diagrams, but write no code and don't rush to produce artifacts.

- Read the Jira ticket; read the **real repo's code** (use the repo path from Step 0; Grep/Read for relevant implementations and integration points); read existing vault `SDD/`, `keypoint/`, and specs.
- Map the gap between **current implementation vs desired**, using ASCII diagrams / comparison tables to frame the problem clearly.
- Use `AskUserQuestion` (open-ended, multiple rounds allowed) to converge the problem definition with the user; challenge assumptions.
- **Convergence condition**: once the problem, scope, and definition of success are clear, summarize and proceed within existing authorization. If the user only requested exploration, offer the concrete capture scope and wait for their go-ahead. Do not re-ask an already authorized proposal request.
- `--explore` mode: stop here; do not produce the four-pack (but you may capture crystallized thinking into an existing artifact if the user asks).

> [!tip] When to skip Stage 0
> If the user has already framed the problem well (a complete ticket, clear scope), do just one lightweight scan to confirm and move straight to Step 2 — don't force multiple rounds.

### Step 2 — Stage 1: produce the four-pack (follow the linear chain, file by file)

> Each artifact's authoring method and template lives in `references/four-pack.md` — read the matching section before writing each file. Track the four files with **TodoWrite**. Start from the "next step" decided in Step 0 and work down the chain, **reading each file after you write it before producing the next** (downstream depends on upstream).

Red-line reminder: the `instruction` text in `references/four-pack.md` is a **constraint for you**, not content to copy — don't paste the guidance into the artifact.

1. **proposal.md** — Why / What Changes / Capabilities (split New·Modified) / Impact.
   - **Ratify the GOAL**: write the ticket's goal in one sentence, using the already-confirmed request; ask only if it remains unresolved. This is the **drift anchor** for every later round — run a drift check when producing specs/design/tasks ("did this step drift from the goal?"; if so, report it).
   - Fill the **propose tier** here (see Step 3) and the frontmatter (template below).
2. **specs/<capability>.md** — one file per New/Modified capability in the proposal. Delta format `## ADDED/MODIFIED/REMOVED/RENAMED Requirements` → `### Requirement:` (SHALL/MUST) → `#### Scenario:` (**exactly 4 `#`**) in WHEN/THEN form.
   - These scenarios **are the acceptance criteria**. Once produced, report the applicable operation-aware criteria as a **checkable checklist**; ask only about unresolved criteria (the criteria are M5 review's re-check list).
3. **design.md** — Context / Goals·Non-Goals / Decisions / Risks·Trade-offs (/ Migration / Open Questions as needed).
   - **Decisions must give N options + trade-offs** (why X over Y), not a flat narrative. A non-trivial flow gets a mermaid diagram (when a node links to a note, add `class X internal-link;`).
4. **tasks.md** — `## N <group>` + `- [ ] N.M \`[tier]\` <description>`.
   - **Task contract**: each behavior task contains RED→GREEN and named verification; each group includes its own required tests/docs. Declare group dependencies; final groups are for integration only. Non-behavior tasks use their own verification.
   - **Tag every task with a task tier** (see Step 3), for M4 apply to spawn subagents.

Then scaffold one **companion** file (not part of the validated four-pack):

- **decision-log.md** (scaffold only) — create the empty human-authored decision log for this ticket. The agent writes only the skeleton here and may later _append challenges_ (M6), but **never writes the decisions themselves** — that is the human's to fill as they work. It feeds M6's `/brief-back` and write-back. Skeleton:

  ```markdown
  ---
  ticket: <ticket>
  type: decision-log
  created: <YYYY-MM-DD>
  ---

  > Human-authored. Record decisions as you make them. The agent may append
  > challenges under "Challenges", never the decisions.

  ## Decisions

  - <date> — <decision + why> (human)

  ## Challenges

  - <agent-appended risks / counter-questions>
  ```

Throughout: only use `AskUserQuestion` when something is genuinely unclear; otherwise make a reasonable decision and keep momentum (don't ask on every small call).

### Step 3 — The two tiers (don't mix them)

| Tier             | Purpose                                       | Values                                                   | Location                          |
| ---------------- | --------------------------------------------- | -------------------------------------------------------- | --------------------------------- |
| **propose tier** | Whole-ticket difficulty → how deep M5 CI goes | `lint` \| `unit` \| `integration` \| `e2e` \| `e2e-live` | `proposal.md` frontmatter         |
| **task tier**    | Which model runs this task                    | `sonnet` \| `opus`                                       | `tasks.md`, per task `\`[tier]\`` |

**Judging the propose tier** (the harder to catch / more likely to break, the deeper): pure function/utility → `unit`; cross-module / middleware / API confluence → `integration`; touches a user flow / front+back end → `e2e`; needs a live service to run → `e2e-live`; config/doc-only tweak → `lint`.

**Judging the task tier** : mechanical, low-risk (run tests, edit config, format) → `sonnet`; ordinary implementation, writing tests, boundary correctness, tricky algorithms, security-sensitive → `opus`.

### Step 4 — Anti-over-engineering guard (mandatory, at least one pass)

Against [[Coding Conventions]]'s Simplicity First, self-check each item and report the result (flag what you find; say "none" if clean):

- Reinventing stdlib / something an existing library already provides?
- Redundant dependency (could reuse what's already there)?
- Speculative abstraction (a single-use case behind an interface / generic / config layer)?
- Dead flexibility (configurability / extension points nobody asked for)?
- Error handling for impossible scenarios?
- 200 lines that could be 50?

### Step 5 — Schema validation (the only script you may run)

```bash
uv run .claude/scripts/validate_sdd.py "01 Work/projects/<PROJECT>/SDD/<ticket>-<slug>" --mode ready
```

Any `ERROR` **must be fixed** before proceeding (missing required field / bad propose_tier or status value / task missing its tier). A `WARN` (e.g. jira still a placeholder) is tolerable until a real ticket key exists.

### Step 6 — Sync Jira (after the proposal converges)

If this is a real Jira ticket and the user agrees: invoke the `jira-automation` skill to update the ticket status / add a comment (link the vault SDD path; mark "proposal complete, awaiting sign-off"). No real ticket → skip.

### Step 7 — Report + offer to commit

Output:

- The SDD folder path + the list of four-pack files produced (one line each)
- The propose tier + a summary of each task's task tier
- The Step 4 guard result
- **Next step**: "Four-pack complete; awaiting a human to set `design_approved: true`, then apply (M4)."
- Ask per the vault CLAUDE.md commit policy:
  ```
  Proposal complete — commit?
  Suggested message: `docs(<project-slug>): SDD proposal for <ticket> <title>`
  ```

---

## Guardrails (must follow)

- **Never write application code** — produce only the SDD Markdown in the vault.
- **Zero footprint in the target repo** — create no file there; specs live only in the vault; read conventions from the repo's existing CLAUDE.md.
- **Zero compute script** — chain state comes from scanning files; the only runnable script is `validate_sdd.py`.
- `design_approved` is always written **false** at propose time (it's the M4 gate switch; flipping it to true is a human action, not yours).
- Read upstream dependencies before writing each file; verify a file exists after writing before moving on.
- The `context` / `rules` / `instruction` in `references/*.md` are constraints for you — **don't copy them into the artifact**.
- Don't jump from Stage 0 to Stage 2 without the user's go-ahead; don't commit or touch Jira without consent.
- No emoji in filenames; artifact content is written in English (to align with OpenSpec and avoid translation drift); your conversation with the user stays in the user's language.

## Edge cases

| Situation                                          | Handling                                                                                                            |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Applicable artifacts exist | Check capability coverage and ready validation; for revisions use --update; otherwise report approval/next phase |
| Only a description, no ticket key                  | After Stage 0 converges, agree a ticket key with the user before creating the folder                                |
| Repo not registered in repos.yaml                  | Mark "conventions unknown"; ask the user in Stage 0 / defer to vault specs; **create no config**                    |
| Capability is "modify existing behavior"           | Use `## MODIFIED Requirements` in specs, **with the full updated content** (never a partial diff fragment)          |
| User asks you to start coding                      | Remind: "Stage 0–1 only produce the proposal; implementation goes through apply (M4)"; write no code                |
| iCloud file is dataless / unreadable               | Stop and report; never overwrite when you can't read the existing artifact                                          |
| `--list` finds an empty folder with no proposal.md | Mark it "not started (next: proposal)"                                                                              |

## Further Reading

- `references/four-pack.md` — the four-pack's authoring method and templates (ported from OpenSpec schema + templates)
- `references/explore-stance.md` — the Stage 0 thinking-partner stance
- `.claude/scripts/validate_sdd.py` — the schema validator (Step 5)
- [[Agentic Coding Harness 實作計劃]] — where M3 sits in the overall pipeline
- [[Coding Conventions]] — the personal standard the Step 4 guard aligns to
