# Claude Clichés — Detect and De-cliché

> Loaded in Stage 4, after the Rule A–K pass. Source: "A Catalog of Claude Clichés" (https://www.linkandth.ink/p/catalog-of-claude-cliches). Its sister piece, "The Division of Interpretive Labor", was written by Claude as the experiment; most verbatim examples below come from that text.

## Contents

- Why this pass exists · Scope for Chinese drafts · Overlap with Rule A–K
- The 22 patterns · Budgets · Detection protocol · What this pass must not destroy
- Rewrite prompt (hand to the rewrite agent verbatim)

## Why this pass exists

The tell is not vocabulary. It is metadiscourse and cheap rhetoric. The model signposts, ranks its own points, and lands sections on quotable epigrams.

The source author calls this an attractor. In a dynamical system, an attractor is the state the system slides back to from any starting point. Prompts change the content. The closing rhetorical shapes stay the same. Reinforcement learning strengthens them, because many readers rate heavily signposted answers as clearer.

The cost is interpretive labor. A reader must first orient: is this clause a claim or an aside, is this hedge a real limit or a courtesy? Every "this matters because" and every "the deepest point is" does that orienting for the reader. It is convenient. It also closes off readings that could be worth more.

This pass is not an AI detector. Using a model does not make prose bad. Avoiding one does not make prose good. The value is awareness, and a draft that leaves the reading to the reader.

## Scope for Chinese drafts

Your Name's articles are Traditional Chinese. The patterns still apply. Each entry below gives the English markers from the source and the Chinese form to look for.

Match on the rhetorical move, not on the string. A pattern counts when the sentence does the same job, in any wording.

## Overlap with Rule A–K

Do not double-report. When a sentence matches both, report it once under the cliché code and name the rule.

| Cliché  | Existing rule                             | How to treat it                                                                          |
| ------- | ----------------------------------------- | ---------------------------------------------------------------------------------------- |
| **CB**  | Rule A (「這不是…而是…」, zero tolerance) | Same offence. CB is the wider form: it also catches 與其說／不如說、rather than          |
| **AHM** | Rule J (hallucination and sourcing)       | An AI-humility line is never acceptable in a signed personal article                     |
| **CDF** | Rule G (over-casual)                      | 「老實說」 is both an over-casual fragment and a candor flag                             |
| **RG**  | Rule I (reasoning gaps)                   | If the gloss is the only explanation, the gap is real — fix the reasoning, not the gloss |
| **AE**  | Rule K (no literal callback at the end)   | AE is narrower: any paragraph or section ending on an epigram                            |

## The 22 patterns

| Code    | Name                        | The move                                                                            | English markers (source)                                                                                                                                | Chinese form                                                         |
| ------- | --------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **CB**  | Contrastive binary          | Manufactures a clean opposition and resolves it in the same breath                  | "not a style but an attractor"; "a stance, not its absence"; "is not abolished; it is relocated"; "on impression rather than measurement"               | 不是 X 而是 Y／X，不是 Y／與其說是 X，不如說是 Y／重點不在 X，而在 Y |
| **MCS** | Mirrored-clause symmetry    | Two clauses in one grammatical frame, side by side, with two or three slots swapped | "High-metadiscourse prose runs the channel at high redundancy; thinned prose runs it at high density"; "The first failure wastes … the second misleads" | 兩個同構分句用分號並排：「A 走的是…；B 走的是…」                     |
| **AE**  | Aphoristic ender            | Lands a paragraph or section on a compact, quotable epigram                         | "the dense version is the courtesy"; "leaves fingerprints, and fingerprints can be counted"; "evidence of training, not of virtue"                      | 段末補一句十到二十字的警句，不帶新資訊，只負責收得漂亮               |
| **ARR** | Anticipate-and-rebut        | States an implied opinion, then kills it with an abrupt fragment                    | "as though it carried no stance. It carries one"                                                                                                        | 「看起來像沒有立場。它有。」— 短殘句反轉                             |
| **SS**  | Significance-signaling      | Declares that what follows matters, instead of letting it matter                    | "That reduction is useful, because"; "This matters for the comparison, because"                                                                         | 這一點很重要，因為…／這裡值得注意的是…                               |
| **MS**  | Meta-signposting            | Narrates the document's structure instead of only having one                        | "Four caveats belong at the front"; "below I try to specify"; "One qualification carries through the rest of this piece"                                | 以下分三部分說明／先講四個前提／本文接下來會…                        |
| **CR**  | Colon-reveal                | Setup clause, colon, tidy payload — manufactured suspense                           | "not a style but an attractor: the center of gravity of a distribution"; "a measurable claim: markers per thousand words"                               | 鋪陳子句＋冒號＋俐落答案：「問題只有一個：cold start。」             |
| **SH**  | Suspense hook               | Withholds a term or claim for one beat                                              | "has a name"; "the cleanest organizing idea is this"                                                                                                    | 這個現象有一個名字／最乾淨的說法是這樣                               |
| **SK**  | Stakes-raising              | Inflates the importance of what comes next; the payload rarely earns it             | "because they shape everything that follows"                                                                                                            | 這決定了後面所有事情／這是全篇最關鍵的一段                           |
| **SRC** | Self-ranking one's claims   | Tells the reader which point is the profound one                                    | "most important"; "cleanest organizing idea"; "The deepest point in the usual comparison is"                                                            | 最重要的是／最深的一層是／真正關鍵的是                               |
| **RF**  | Reframe                     | Repositions the question into the version the writer prefers                        | "Better posed:"; "the harder skill is usually"                                                                                                          | 換個問法會更好：／更該問的是                                         |
| **CP**  | Corrective pivot            | Stages a small debate with itself                                                   | "It would be wrong, though, to call the difference padding"                                                                                             | 不過，把這個差異說成贅字並不公平                                     |
| **VP**  | Validate, then promise      | Issues a stamp of correctness, then promises precision in the same sentence         | "is correct, and it can be made precise"; "is right, and this is its exact form"                                                                        | 你說得對，而且可以講得更精確                                         |
| **CF**  | Contribution framing        | Presents the point as completing a gap earlier accounts left                        | "supplies the other half"; "it pins down something the earlier explanations left open"                                                                  | 這補上了前面缺的另一半／這把先前沒說清楚的部分定下來                 |
| **CCC** | Clean-consequence connector | Lends an inevitability the argument did not earn                                    | "follows directly"; "falls out of"; "comes straight out of this"                                                                                        | 這直接導出／順著就會得到／自然就是                                   |
| **CL**  | Confidence by litotes       | States by negating the opposite, so the claim cannot be questioned                  | "not difficult to specify"; "blind tagging is not optional"                                                                                             | 這不難指出／這並非不可行／沒有人會反對                               |
| **RG**  | Restatement gloss           | Announces a paraphrase of what was just said. Overuse is the offence                | "in other words"; "put differently"                                                                                                                     | 換句話說／也就是說／講白一點                                         |
| **RH**  | Reflexive hedging           | Uncertainty markers applied as a verbal reflex, not as calibration                  | "almost"; "tends to"; "with few exceptions"; "roughly"; "largely"                                                                                       | 幾乎／大致上／傾向於／多半／某種程度上                               |
| **DT**  | Deflating tail clause       | A short theatrical qualifier at sentence end, worn as modesty or precision          | "and no more"; "and no evidence of anything finer"                                                                                                      | 僅此而已／就這樣，不多不少／沒有更多了                               |
| **CDF** | Candor flag                 | Marks what follows as especially frank                                              | "the honest answer"                                                                                                                                     | 老實說／講真的／坦白講                                               |
| **AHM** | Reflexive AI humility       | Flags itself as a model, or hedges the whole text, as a modesty gesture             | "this essay is written by one of the systems under examination"; "Most of the above is structured impression, and could be wrong"                       | 本文由 AI 協助撰寫／以上多為印象，可能有誤                           |
| **SDA** | Spaced-dash aside           | Heavy reliance on dash-flanked asides, qualifiers, and lists                        | "– it carries no fact, only an instruction about how to read what follows"                                                                              | 大量用破折號夾插語、限定詞、清單                                     |

The three highest-frequency patterns are **CB**, **MCS**, and **AE**. CB and AE fuse often: an aphoristic ender built on a binary.

The agreement tell: when a model concedes a point, the first paragraph is near-fixed — grant that you are right, state what still holds, close on "But that's not all it's doing". That is **ARR** plus **CB**.

## Budgets

This skill's policy, not the source article's.

| Tier | Codes                                                          | Budget per article                                                      |
| ---- | -------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 1    | CB, MCS, AE, AHM                                               | **0.** Every instance is CRITICAL and must be rewritten                 |
| 2    | ARR, SS, MS, CR, SH, SK, SRC, RF, CP, VP, CF, CCC, CL, DT, CDF | **3 total**, and at most 1 per code. Everything over budget is CRITICAL |
| 3    | RG, RH, SDA                                                    | RG ≤ 2 · RH ≤ 3, never two in one sentence · SDA ≤ 2                    |

Tier 3 exists because the moves are legitimate at low density. Repetition is what makes them a tic.

## Detection protocol

1. **Sweep per pattern, not per paragraph.** Read the draft once for each Tier 1 code, then once for Tier 2, then once for Tier 3. A single read for all 22 misses instances.
2. **Tag every hit inline** in a working copy: `⟦CB⟧`, `⟦MCS⟧`. Keep the tags out of the delivered draft.
3. **Check the last sentence of every paragraph and every section** for AE. This is where the pattern concentrates.
4. **Count.** Report the count per code, and the total per tier, against the budget.
5. **Report each hit** as: quote / code / why it is that move / rewrite direction. Never rewrite in this step.

Output format:

```
### Cliché scan

| Code | Count | Budget | Status |
|------|-------|--------|--------|
| CB   | 4     | 0      | OVER   |
...

#### CRITICAL
1. ⟦CB⟧「這不是快取問題，而是 cold start。」— manufactured binary, resolved in one breath. Direction: state the finding flat — 「Cold start 造成這段 latency。快取在這條路徑上沒有參與。」
```

## What this pass must not destroy

Over-correction is a failure too. These are legitimate and stay:

- **Substantive contrast teaching** (`style-guide-core.md`, 對比式教學). A worked comparison of two approaches, with real differences, is not CB. CB is a sentence-level binary asserted in one breath and resolved by the assertion itself.
- **A real limitation at the end of a section.** A boundary case with content is not AE. AE has no new information; it only sounds good.
- **Calibrated uncertainty** (Rule C's exception: 「我不確定 X 在 Y 場景會不會壞」). This is a real epistemic state with a named subject. RH is a reflex adverb attached to a claim the author is in fact sure of.
- **Genuine parallel structure** where two systems really do differ along one axis. MCS is the empty version: the frame is copied because it scans well, and the second clause adds nothing.
- **A colon introducing a list or a definition.** CR is the suspense version, where the colon withholds a one-word answer for effect.

When a hit is arguable, report it as WARNING with the reason, not as CRITICAL.

## Rewrite prompt

Hand this to the rewrite agent verbatim, with the draft and the scan report.

```
You are rewriting a Traditional Chinese technical article by Your Name. A scan has tagged rhetorical patterns from the Claude cliché catalog. Your job is to remove them without losing a single fact.

Inputs: the full draft, the cliché scan report, `reference/claude-cliches.md`, the Stage 1 outline and TL;DR.

Rules:

1. Fix every CRITICAL hit. Fix WARNING hits when the fix costs no content.
2. Preserve every technical anchor byte-for-byte: numbers, versions, API names, error messages, code, `[待補：___]` placeholders, and Mermaid blocks. Never introduce a number that is not already in the draft.
3. Rewrite by these conversions:
   - CB → one flat declarative for the thing that is true. Delete the negated half unless the reader would otherwise assume it; if they would, give the correction its own sentence.
   - MCS → keep one clause. Write the second as an ordinary sentence with its own shape, or cut it if it added nothing.
   - AE → delete the epigram. End the section on its last piece of content. If the section needs a close, close on a concrete consequence or a limitation.
   - ARR → state the position once, plainly. No fragment reversal.
   - SS / SK / SRC → delete the announcement and keep the claim. Let the reader rank it.
   - MS → delete the structural narration. The headings carry the structure.
   - CR / SH → put the payload in the main clause. No withholding.
   - RF → answer the question as asked, or say plainly why it is the wrong question and then ask a better one as a separate sentence.
   - CP / VP / CF → state the position directly. No self-debate, no self-issued correctness stamp, no gap-filling frame.
   - CCC → name the actual mechanism, or downgrade to what the evidence supports.
   - CL → say it positively. If the claim needs support, add the support instead of the litotes.
   - RG → keep one formulation, the clearer one. If the first was unclear, delete the first.
   - RH → delete the hedge, or replace it with a stated condition ("在 X 情境下").
   - DT / CDF / AHM → delete the clause. Nothing replaces it.
   - SDA → convert the dash aside into a comma clause, a separate sentence, or a footnote-style parenthesis. Keep at most two dashes in the whole article.
4. Obey the constraints already in force: `style-guide-core.md` (voice, language mix, Markdown limits) and Rules A–K in `style-guide-verify.md`. Do not introduce a new violation while removing a cliché.
5. Do not over-correct. Read "What this pass must not destroy" first. Substantive contrast, real limitations, calibrated uncertainty, and honest parallel structure stay.
6. Do not add content. Do not add sections. Do not smooth the prose beyond the fixes.

Output: the full rewritten draft, then a change table — original sentence / code fixed / new sentence. Flag anything you chose not to fix and why.
```

## Further reading

- Source catalog: https://www.linkandth.ink/p/catalog-of-claude-cliches
- Sister piece, the Claude-written experiment the examples come from: "The Division of Interpretive Labor"
