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

## `03 Writing/**/*.md` (Personal articles, recommended fields)

```yaml
---
title: <title>
status: draft | workspace | blog
created: YYYY-MM-DD
published_at: YYYY-MM-DD # workspace / blog only
target: workspace | blog | both
tags: [...]
---
```
