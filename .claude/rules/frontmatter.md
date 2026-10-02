# Frontmatter Schemas

## `_raw/<category>/*.md` (Raw Sources, required fields)

```yaml
---
source_url: <URL>
source_type: article | gist | paper | video | podcast | screenshot
author: <author>
fetched_at: YYYY-MM-DD
tags: [tag1, tag2]
related_wiki:
  - "[[wiki note name]]"
---
```

## `02 Knowledge/<topic>/*.md` (Wiki Notes, recommended fields)

```yaml
---
tags: [domain-tag, ...]
status: draft | active | archived
last_reviewed: YYYY-MM-DD # optional, used by lint to detect staleness
---
```

## `03 Writing/**/*.md` (Personal articles)

Folder membership is the only publication state: `drafts/**` is writing;
`blog/**` is published source. No `draft`, `status`, `target`, or
`published_at` field duplicates that state. Other Writing folders are not published.

Blog articles require title, description, YYYY-MM-DD string date, string-array tags,
and category. Author defaults to Your Name; image is optional. Optional language
and updatedAt describe content, not sync/deployment status. Keep technical sync state
in the website's generated manifest, and query the deployment provider for live status.
