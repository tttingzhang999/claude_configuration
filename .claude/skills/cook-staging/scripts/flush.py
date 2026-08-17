#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Promote reviewed staging files into the vault.

Scans `_staging/*.md`. Each staging file keeps machine control fields in a
`<!--cook-staging ... -->` comment (YAML) in the body, so Obsidian's Properties
panel only shows `reviewed` (plus the note's own frontmatter). For each file
where the control block has `staging: true` and the frontmatter has
`reviewed: true`, this strips the control comment + the `reviewed` key and
writes/overwrites/appends the remainder to `target_path`, then deletes the
staged file and appends a line to `_log.md`. Files with `reviewed: false` are
left in place.

Deterministic and idempotent. Prints a JSON summary on stdout; the git commit is
left to the caller (cook-staging SKILL / cook-loop), which reads `promoted`.

Usage:  uv run flush.py [--dry-run]
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

# <vault>/.claude/skills/cook-staging/scripts/flush.py → vault root is 4 parents up
VAULT = Path(__file__).resolve().parents[4]
STAGING = VAULT / "_staging"
LOG = VAULT / "_log.md"

# The one frontmatter key that is control-only (human review gate); stripped on
# promote. All other control fields live in the CONTROL comment block below.
FM_CONTROL = {"reviewed"}
CONTROL_RE = re.compile(r"[ \t]*<!--\s*cook-staging\s*\n(.*?)\n\s*-->[ \t]*\n?", re.DOTALL)
TZ = timezone(timedelta(hours=8))  # Asia/Taipei


def parse(text: str) -> tuple[dict, str]:
    """Split a markdown file into (frontmatter dict, body)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm = yaml.safe_load(text[4:end]) or {}
    body = text[end + 5:]
    return fm, body


def parse_control(body: str) -> tuple[dict, str]:
    """Extract the `<!--cook-staging ... -->` control block (YAML) from the body.
    Returns (control dict, body with the comment removed)."""
    m = CONTROL_RE.search(body)
    if not m:
        return {}, body
    control = yaml.safe_load(m.group(1)) or {}
    stripped = (body[:m.start()] + body[m.end():]).lstrip("\n")
    return control, stripped


def dump_note(fm: dict, body: str) -> str:
    """Reassemble a note from its (control-stripped) frontmatter and body."""
    if fm:
        front = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
        return f"---\n{front}\n---\n{body}"
    return body


def append_under_anchor(target: Path, anchor: str, body: str) -> None:
    """Append `body` at the end of the section headed by `anchor` (a heading line
    like '## 進行中'). If the target or anchor is missing, create/append sensibly.
    Also refresh a top-level `last_updated:` frontmatter field if present."""
    if not target.exists():
        header = f"{anchor}\n\n" if anchor else ""
        target.write_text(f"{header}{body.rstrip()}\n", encoding="utf-8")
        return

    fm, rest = parse(target.read_text(encoding="utf-8"))
    if "last_updated" in fm:
        fm["last_updated"] = datetime.now(TZ).date().isoformat()

    lines = rest.splitlines()
    insert_at = len(lines)
    if anchor:
        try:
            a = next(i for i, ln in enumerate(lines) if ln.strip() == anchor.strip())
            # next top-level section after the anchor, else EOF
            insert_at = next(
                (j for j in range(a + 1, len(lines)) if lines[j].startswith("## ")),
                len(lines),
            )
        except StopIteration:
            # anchor not found: append the anchor + body at EOF
            lines += ["", anchor.strip()]
            insert_at = len(lines)

    block = ["", body.rstrip(), ""]
    new_rest = "\n".join(lines[:insert_at] + block + lines[insert_at:]).rstrip() + "\n"
    target.write_text(dump_note(fm, new_rest) if fm else new_rest, encoding="utf-8")


VALID_OPS = {"write", "append"}


def promote(control: dict, fm: dict, body: str) -> None:
    op = control.get("op", "write")
    if op not in VALID_OPS:
        # Never fall through to an unconditional write on a typo'd/unknown op —
        # that would silently clobber an existing vault file.
        raise ValueError(f"unknown op {op!r} (expected one of {sorted(VALID_OPS)})")
    target = VAULT / control["target_path"]
    target.parent.mkdir(parents=True, exist_ok=True)

    if op == "append":
        append_under_anchor(target, control.get("append_anchor", ""), body)
        return

    if op == "write" and target.exists() and not control.get("overwrite_existing"):
        raise FileExistsError(f"{control['target_path']} exists and overwrite_existing is false")

    note_fm = {k: v for k, v in fm.items() if k not in FM_CONTROL}
    target.write_text(dump_note(note_fm, body), encoding="utf-8")


def main() -> None:
    dry = "--dry-run" in sys.argv
    promoted, pending, errors = [], [], []

    for f in sorted(STAGING.glob("*.md")):
        if f.name == "README.md":
            continue
        try:
            fm, body = parse(f.read_text(encoding="utf-8"))
            control, body = parse_control(body)
        except Exception as e:  # noqa: BLE001 - report, don't crash the batch
            errors.append({"file": f.name, "error": f"parse: {e}"})
            continue
        if not control.get("staging"):
            continue
        if not fm.get("reviewed"):
            pending.append({"file": f.name, "target": control.get("target_path")})
            continue
        if not control.get("target_path"):
            errors.append({"file": f.name, "error": "missing target_path"})
            continue
        if dry:
            promoted.append({"file": f.name, "target": control["target_path"], "op": control.get("op", "write")})
            continue
        try:
            promote(control, fm, body)
            promoted.append({"file": f.name, "target": control["target_path"], "op": control.get("op", "write")})
            f.unlink()
        except Exception as e:  # noqa: BLE001
            errors.append({"file": f.name, "error": str(e)})

    if promoted and not dry:
        date = datetime.now(TZ).date().isoformat()
        entry = f"\n## [{date}] flush | {len(promoted)} item(s)\n" + "".join(
            f"- `{p['op']}` → {p['target']}\n" for p in promoted
        )
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(entry)

    print(json.dumps({
        "promoted": promoted,
        "pending": pending,
        "errors": errors,
        "log": str(LOG.relative_to(VAULT)) if promoted and not dry else None,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
