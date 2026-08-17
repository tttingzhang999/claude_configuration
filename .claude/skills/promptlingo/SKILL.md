---
name: promptlingo
description: Analyzes the user's daily Claude Code conversations and produces an Obsidian-flavored English-learning report (vocabulary, grammar focus, sentence improvement, sentence rewrites, i+1 article, spaced review). Triggered when the user runs /promptlingo or /promptlingo YYYY-MM-DD.
argument-hint: "[YYYY-MM-DD]"
allowed-tools: Bash(uv *) Bash(cat *) Read Write
model: haiku
---

# promptlingo

Read JSONL transcripts from `~/.claude/projects/`, filter noise, and generate study material calibrated to the user's CEFR level. Output is written into the user's Obsidian vault at `04 English Learning/` so reports, vocab, and patterns are browsable, searchable, and linkable.

## Invocation

- `/promptlingo` — analyze today
- `/promptlingo 2026-04-25` — analyze a specific ISO-8601 date

## Paths

Let `SKILL_DIR` be the directory of this file. The scripts read paths from `scripts/paths.py`:

- `LEARNING_DIR` = `<vault>/04 English Learning/` (override with `PROMPTLINGO_LEARNING_DIR`)
- Reports → `$LEARNING_DIR/reports/<DATE> English Daily.md`
- Vocab JSON (SRS state) → `$LEARNING_DIR/data/vocab.json`
- Patterns JSON → `$LEARNING_DIR/data/patterns.json`
- Vocab notes (projected) → `$LEARNING_DIR/vocab/<word>.md`
- Pattern notes (projected) → `$LEARNING_DIR/patterns/<slug>.md`

## Steps

Let `DATE_ARG` be the user's second token (empty if none).

### 1. Read config

```bash
cat "$SKILL_DIR/config.json"
```

Hold onto `level` (CEFR) and `native_lang` (default `zh-TW`). Use `native_lang` for explanations.

### 2. Load and clean turns

```bash
uv run "$SKILL_DIR/scripts/transcript_loader.py" $DATE_ARG
```

Returns `{date, sources, stats, turns}`. Each turn carries `project` (cwd-encoded) and `cwd`. If `stats.stage3_turns == 0`, tell the user there's nothing to analyze and stop.

### 2.5 Narrow bundle (Krashen narrow input)

Group `turns` by `project`. Pick the project with the most user turns as `topic_project`; collect those turns as `topic_turns`. Tie-break by most-recent turn. Infer a short `topic_label` from the dominant subject — don't invent topics not in the turns.

### 2.6 Spaced review query

```bash
uv run "$SKILL_DIR/scripts/due.py" $DATE_ARG --limit=5
```

Returns `{today, due: [{word, cefr, zh, last_seen, count, interval, days_overdue, examples}]}`. Hold this list as `review_words`. Weave them into the article (step 4) and surface in section 3.5.

### 3. Per-language analysis

Use `config.level` as baseline; `native_lang` for explanations.

**3a. Sentence rewrites (Chinese → English)**
Filter `lang == "zh"` and `role == "user"`. Pick up to 5 high-value sentences. Give one English rewrite at exactly `config.level` per sentence.

**3b. Sentence improvement (English user prompts)**
Filter `lang == "en"` and `role == "user"`. **Drop fragments and quick imperatives** (under ~5 words OR one-clause imperative with no detail worth correcting — `ok`, `commit it`, `fix it`, `go`, `do it`, `thanks`). Only critique full sentences where grammar / word choice / naturalness matter. If nothing qualifies, skip the section with a `> [!tip]` callout — don't emit an empty table.

**3c. Vocabulary extraction (assistant first, user second)**
Pull 8–15 words.

- **Hard filter: only at or above `config.level`.** Drop easier words.
- Drop programming jargon, variable names, file paths, brand names, proper nouns.
- Each entry: `{word, cefr, zh, pos, examples, synonyms, antonyms}`. `pos` is part-of-speech (`n.`, `v.`, `adj.`, etc.).

**3d. Grammar focus (overall)**
Pick 1–3 grammar points. For each: one example pulled from the day plus one contrast example.

### 4. Generate the i+1 short article

Write **one short article, ~150 words**, at `config.level`. Hard rules:

- **Topic = `topic_label`** from step 2.5.
- **Comprehension target ≥ 95%**: at most 5% of word tokens above `config.level`.
- **Massed repetition**: every word from step 3c appears at least once; on-level words twice in different sentences.
- **Spaced repetition**: weave 3–5 of `review_words` naturally — don't list them.
- **Style**: third-person narrative recap; past or present perfect tense.
- **Glossing**: any above-level word gets inline `(中文)` first occurrence.

Output: a single paragraph plus a 2-line `> Coverage: vocab X/X · review Y/5` footer.

### 5. Persist

Build:

```json
{ "date": "<YYYY-MM-DD>", "vocab": [...from 3c], "patterns": [...from 3a+3b], "reviewed": ["...the review_words surfaced in 3.5"] }
```

`reviewed` = the `word` of every `review_words` entry you surfaced in section 3.5.
Surfacing a word IS one spaced-repetition rep, so `store.py` promotes its Leitner box
(`count += 1`, `last_seen = today`) — this is what stops the same overdue words from
reappearing every day. Omit / leave empty only if section 3.5 had no words.

Then:

```bash
uv run "$SKILL_DIR/scripts/store.py" <<'PLJSON'
<the json above>
PLJSON
```

> [!warning] 用 heredoc,不要 `echo '...' |`
> payload 裡的英文縮寫(`don't`、`it's`)和使用者引號含單引號,用 `echo '...'` 會截斷 shell 字串、腐化 JSON。上面的 quoted heredoc(`<<'PLJSON'`)不做任何展開,單引號原樣送進 stdin。

`store.py` is idempotent (a word already touched today is not advanced twice, so
re-running a date is safe). It updates `vocab.json` / `patterns.json`, advances the
reviewed words, then projects each touched entry into a per-entry note (`<word>.md`,
`<slug>.md`) — so the new vocab and patterns are immediately browsable in Obsidian and
indexed by `vocab.base` / `patterns.base`.

To regenerate every note from JSON (e.g. after schema change):

```bash
uv run "$SKILL_DIR/scripts/store.py" --rebuild-notes
```

### 6. Write the daily report

Write Markdown to `$LEARNING_DIR/reports/<DATE> English Daily.md`.

Read `references/report-template.md` (relative to `SKILL_DIR`) — it holds the exact
frontmatter, the Obsidian-flavored section skeleton (no H1), and the hard rules for
each section. Fill every `<placeholder>` and follow those rules.

### 7. Echo a short summary in chat

Output:

- `topic_label`
- top 3 takeaways
- report path
- `obsidian://open?vault=<URL-encoded vault name>&file=<URL-encoded file path within vault>` — 一鍵打開

Vault name 從 `LEARNING_DIR.parent.name` 取；file path 是 `04 English Learning/reports/<DATE> English Daily.md`，URL-encode 整串。

Don't paste the full report or the i+1 article.

---

## Adjust level

Edit `config.json` `level` to A1 / A2 / B1 / B2 / C1 / C2.
