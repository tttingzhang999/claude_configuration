#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Generate 01 Work/Repo Registry.md from repo-router repos.yaml (single
source of truth). Re-run after scan.py to refresh the human-readable view."""
from pathlib import Path
import yaml

VAULT = Path(__file__).resolve().parents[4]  # …/.claude/skills/repo-router/scripts → vault root
YAML = VAULT / ".claude/skills/repo-router/repos.yaml"
OUT = VAULT / "01 Work/Repo Registry.md"

GROUPS = [
    ("gc", "Acme Corp (Work)", "code/work/"),
    ("personal", "Personal", "code/personal/"),
    ("side", "Side (side)", "code/side/"),
    ("others", "Others (reference clones)", "code/others/"),
]

data = yaml.safe_load(YAML.read_text(encoding="utf-8"))
repos = data["repos"]

lines = [
    "---",
    "tags: [meta, work, registry]",
    "status: active",
    "---",
    "",
    "```table-of-contents",
    "```",
    "",
    "> [!note] What this is",
    "> Human-readable index of local git repos, **generated from** "
    "`.claude/skills/repo-router/repos.yaml` (the single source of truth). "
    "Don't hand-edit — edit `repos.yaml` `description`/`vault_project` and re-run "
    "the generator, or re-run `scan.py` after cloning/moving a repo. "
    "Use the `repo-router` skill to resolve a name to its real path and read the code.",
    "",
]

for key, title, prefix in GROUPS:
    root = prefix.rstrip("/")
    group = [r for r in repos if r["path"] == root or r["path"].startswith(prefix)]
    if not group:
        continue
    lines += [f"## {title}", "", "| Repo | Path (`~/`) | Vault project | What it does |", "|------|------|------|------|"]
    for r in sorted(group, key=lambda r: r["path"]):
        vp = r.get("vault_project", "")
        vp_cell = f"[[{vp}]]" if vp else ""
        desc = r.get("description", "").replace("|", "\\|")
        lines.append(f"| `{r['name']}` | `{r['path']}` | {vp_cell} | {desc} |")
    lines.append("")

lines += ["## Further Reading", "", "- [[Context Map]]", "- [[CLAUDE.md]]", ""]

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT} ({sum(len([r for r in repos if r['path'].startswith(p)]) for _,_,p in GROUPS)} repos across {len(GROUPS)} groups)")
