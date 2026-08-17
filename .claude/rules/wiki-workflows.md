# Karpathy Wiki Workflows

Three-layer architecture:

- **Raw Sources** = `_raw/` (append-only, must not be modified)
- **Wiki Layer** = `02 Knowledge/` (fully maintained by the LLM)
- **Schema** = `CLAUDE.md`
- **Catalog** = `index.md` (updated after every ingest)
- **Log** = `_log.md` (append-only chronological log)

## Ingest Workflow

Trigger phrases: "ingest this article", "help me archive this article", "add this material to the vault"

1. **Fetch the source**: use WebFetch to get the full content (for paywalled content, tell the user to use the Web Clipper instead)
2. **Save as raw**: write to `_raw/<category>/YYYYMMDD-<slug>.md`
   - category: `articles | papers | transcripts | screenshots`
   - frontmatter must include: `source_url`, `source_type`, `author`, `fetched_at`, `tags`, `related_wiki`
   - content must be preserved **verbatim**, do not summarize
3. **Produce the wiki note**: create or update a note under `02 Knowledge/<topic>/`
   - follow `file-naming.md` (no emoji in filenames)
   - add a TOC block at the top
   - primarily Traditional Chinese, at least 3 wikilinks, ending with links back to the raw source and [[index]]
4. **Update the index**: `index.md` only maintains the "latest ingest" row of the `_raw` table; the `02 Knowledge/` listing is generated dynamically by [[index.base]] — **do not edit it manually**
5. **Append to the log**: append `## [YYYY-MM-DD] ingest | <title>` to `_log.md`, listing the touched files
6. **Report back**: give the user the raw path, wiki path, and list of touched files

## Query Workflow

Trigger: the user asks any question

1. First read [[index]] to find the most relevant pages
2. Drill into the wiki layer, read the full content, then answer
3. Only fall back to `_raw/` for supplementary detail if the wiki is insufficient
4. If the answer is worth preserving (cross-source synthesis, comparison table, new finding) → organize it into a wiki note or append it to an existing note, and append `## [YYYY-MM-DD] query | <question>` to `_log.md`
5. Always cite using `[[wikilink]]`

## Lint Workflow

Trigger phrases: "lint vault", "health check the notes"

Scan and produce a to-fix list (**do not auto-modify, wait for user approval**):

- Orphan nodes (wiki notes with no backlinks)
- Broken wikilinks
- Wiki note filenames containing an emoji (filenames must be the plain title)
- Notes over 30 lines missing a TOC
- `index.md` drift (important notes that exist but aren't listed)
- Contradictory statements (two pages giving different accounts of the same concept)
- Stale information (`fetched_at` over 1 year old and tagged `#需要複習`)

Output: append `## [YYYY-MM-DD] lint | <scope>` to `_log.md`, with the to-fix list attached.

**Prefer `obsidian-cli` for linting** (if Obsidian is running):

```bash
# find orphan nodes
obsidian search query="[[" --invert  # pseudo-example, adjust to what the CLI actually supports
obsidian backlinks file="<note>"

# list all tags with counts
obsidian tags sort=count counts

# batch-query a frontmatter property
obsidian property:list file="<note>"
```

Fall back to Read / Grep when the CLI is unavailable.
