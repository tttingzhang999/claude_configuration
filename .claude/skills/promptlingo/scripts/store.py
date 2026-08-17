#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Merge analyzer output into vocab.json + patterns.json and project per-entry Obsidian notes.

Stdin:  JSON {"vocab": [...], "patterns": [...], "date": "YYYY-MM-DD"}
Stdout: summary {"vocab_added", "vocab_updated", "patterns_added", "patterns_updated", ...}

Flags:
    --rebuild-notes    Skip stdin merge; just regenerate every vocab/pattern note from json.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (  # noqa: E402
    PATTERNS_JSON,
    VOCAB_JSON,
    ensure_dirs,
    pattern_note_path,
    vocab_note_path,
)


def load_json(path: Path) -> list:
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f)


def save_json(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def merge_vocab(existing: list, incoming: list, today: str) -> tuple[int, int, list[dict]]:
    index = {item["word"].lower(): item for item in existing}
    added = updated = 0
    touched: list[dict] = []
    for raw in incoming:
        word = (raw.get("word") or "").strip()
        if not word:
            continue
        key = word.lower()
        examples = [e for e in (raw.get("examples") or []) if e]
        if key in index:
            cur = index[key]
            if cur.get("last_seen") != today:  # idempotent: don't inflate count on same-day re-run
                cur["count"] = cur.get("count", 0) + 1
                cur["last_seen"] = today
            existing_examples = cur.get("examples") or []
            for ex in examples:
                if ex not in existing_examples:
                    existing_examples.append(ex)
            cur["examples"] = existing_examples[-5:]
            for field in ("zh", "cefr", "pos", "synonyms", "antonyms"):
                if raw.get(field) and not cur.get(field):
                    cur[field] = raw[field]
            updated += 1
            touched.append(cur)
        else:
            entry = {
                "word": word,
                "cefr": raw.get("cefr") or "",
                "zh": raw.get("zh") or "",
                "pos": raw.get("pos") or "",
                "synonyms": raw.get("synonyms") or [],
                "antonyms": raw.get("antonyms") or [],
                "count": 1,
                "first_seen": today,
                "last_seen": today,
                "examples": examples[:5],
            }
            index[key] = entry
            added += 1
            touched.append(entry)
    existing.clear()
    existing.extend(sorted(index.values(), key=lambda x: x["word"].lower()))
    return added, updated, touched


def _slug(pattern: str, user_wrote: str) -> str:
    base = (user_wrote or pattern).lower()
    base = re.sub(r"[^a-z0-9一-鿿\s-]", "", base)
    base = re.sub(r"\s+", "-", base.strip())
    return base[:80] or "pattern"


def merge_patterns(existing: list, incoming: list, today: str) -> tuple[int, int, list[dict]]:
    index = {(item["pattern"], item.get("user_wrote", "")): item for item in existing}
    added = updated = 0
    touched: list[dict] = []
    for raw in incoming:
        pat = (raw.get("pattern") or "").strip()
        if not pat:
            continue
        key = (pat, raw.get("user_wrote", ""))
        if key in index:
            cur = index[key]
            cur["occurrences"] = cur.get("occurrences", 0) + 1
            cur["last_seen"] = today
            if raw.get("correction") and not cur.get("correction"):
                cur["correction"] = raw["correction"]
            updated += 1
            touched.append(cur)
        else:
            entry = {
                "pattern": pat,
                "user_wrote": raw.get("user_wrote", ""),
                "correction": raw.get("correction", ""),
                "occurrences": 1,
                "first_seen": today,
                "last_seen": today,
                "slug": _slug(pat, raw.get("user_wrote", "")),
            }
            index[key] = entry
            added += 1
            touched.append(entry)
    existing.clear()
    existing.extend(index.values())
    return added, updated, touched


def advance_reviews(existing: list, reviewed: list, today: str) -> tuple[int, list[dict]]:
    """Surfacing a word in the daily review counts as one spaced-repetition rep:
    promote its Leitner box (count += 1) and reset the clock (last_seen = today).
    Idempotent per day — a word already touched today (learned or reviewed) is skipped."""
    index = {item["word"].lower(): item for item in existing}
    advanced = 0
    touched: list[dict] = []
    for raw in reviewed:
        word = (raw or "").strip().lower()
        cur = index.get(word)
        if not cur or cur.get("last_seen") == today:
            continue
        cur["count"] = cur.get("count", 0) + 1
        cur["last_seen"] = today
        advanced += 1
        touched.append(cur)
    return advanced, touched


def _yaml_str(s: str) -> str:
    s = (s or "").replace('"', "'")
    return f'"{s}"'


def _yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(_yaml_str(str(x)) for x in items) + "]"


def render_vocab_note(entry: dict) -> str:
    word = entry["word"]
    examples = entry.get("examples") or []
    example_lines = "\n".join(f"> - {ex}" for ex in examples) or "> - （尚無例句）"
    cefr = entry.get("cefr") or ""
    fm = [
        "---",
        "type: vocab",
        f"word: {word}",
        f"cefr: {cefr}",
        f"zh: {_yaml_str(entry.get('zh') or '')}",
        f"pos: {_yaml_str(entry.get('pos') or '')}",
        f"count: {entry.get('count', 1)}",
        f"first_seen: {entry.get('first_seen') or ''}",
        f"last_seen: {entry.get('last_seen') or ''}",
        f"synonyms: {_yaml_list(entry.get('synonyms') or [])}",
        f"antonyms: {_yaml_list(entry.get('antonyms') or [])}",
        f"tags: [vocab, cefr/{cefr or 'unknown'}]",
        "---",
    ]
    body = [
        "",
        "```table-of-contents",
        "```",
        "",
        f"> [!info] {word}",
        f"> **中文：** {entry.get('zh') or '—'}",
        f"> **詞性：** {entry.get('pos') or '—'} · **CEFR：** {cefr or '—'}",
        f"> **出現次數：** {entry.get('count', 1)} · **上次：** {entry.get('last_seen') or '—'}",
        "",
        "## 例句",
        "> [!example]",
        example_lines,
        "",
    ]
    syns = entry.get("synonyms") or []
    ants = entry.get("antonyms") or []
    if syns or ants:
        body.append("## 同反義")
        if syns:
            body.append(f"- 同義：{', '.join(syns)}")
        if ants:
            body.append(f"- 反義：{', '.join(ants)}")
        body.append("")
    body.append("---")
    body.append("延伸：[[promptlingo]] · [[vocab]] · [[index]]")
    body.append("")
    return "\n".join(fm + body)


def render_pattern_note(entry: dict) -> str:
    fm = [
        "---",
        "type: pattern",
        f"pattern: {_yaml_str(entry['pattern'])}",
        f"user_wrote: {_yaml_str(entry.get('user_wrote') or '')}",
        f"correction: {_yaml_str(entry.get('correction') or '')}",
        f"occurrences: {entry.get('occurrences', 1)}",
        f"first_seen: {entry.get('first_seen') or ''}",
        f"last_seen: {entry.get('last_seen') or ''}",
        "tags: [pattern]",
        "---",
    ]
    body = [
        "",
        "```table-of-contents",
        "```",
        "",
        f"> [!bug] {entry['pattern']}",
        f"> **出現次數：** {entry.get('occurrences', 1)} · **上次：** {entry.get('last_seen') or '—'}",
        "",
        "## 你寫的",
        "> [!fail] 原句",
        f"> {entry.get('user_wrote') or '—'}",
        "",
        "## 修正",
        "> [!success] 正確寫法",
        f"> {entry.get('correction') or '—'}",
        "",
        "---",
        "延伸：[[promptlingo]] · [[patterns]] · [[index]]",
        "",
    ]
    return "\n".join(fm + body)


def write_note(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def project_vocab_notes(entries: list[dict]) -> int:
    n = 0
    for e in entries:
        write_note(vocab_note_path(e["word"]), render_vocab_note(e))
        n += 1
    return n


def project_pattern_notes(entries: list[dict]) -> int:
    n = 0
    for e in entries:
        slug = e.get("slug") or _slug(e["pattern"], e.get("user_wrote", ""))
        write_note(pattern_note_path(slug), render_pattern_note(e))
        n += 1
    return n


def rebuild() -> dict:
    vocab = load_json(VOCAB_JSON)
    patterns = load_json(PATTERNS_JSON)
    ensure_dirs()
    v = project_vocab_notes(vocab)
    p = project_pattern_notes(patterns)
    return {"rebuilt_vocab_notes": v, "rebuilt_pattern_notes": p}


def main() -> int:
    if "--rebuild-notes" in sys.argv[1:]:
        result = rebuild()
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    payload = json.load(sys.stdin)
    today = payload.get("date") or date.today().isoformat()

    ensure_dirs()
    vocab = load_json(VOCAB_JSON)
    patterns = load_json(PATTERNS_JSON)

    v_add, v_upd, v_touched = merge_vocab(vocab, payload.get("vocab", []), today)
    p_add, p_upd, p_touched = merge_patterns(patterns, payload.get("patterns", []), today)
    r_adv, r_touched = advance_reviews(vocab, payload.get("reviewed", []), today)

    save_json(VOCAB_JSON, vocab)
    save_json(PATTERNS_JSON, patterns)

    project_vocab_notes(v_touched + r_touched)
    project_pattern_notes(p_touched)

    json.dump({
        "vocab_added": v_add, "vocab_updated": v_upd,
        "patterns_added": p_add, "patterns_updated": p_upd,
        "reviews_advanced": r_adv,
        "vocab_total": len(vocab), "patterns_total": len(patterns),
        "vocab_notes_written": len(v_touched) + len(r_touched),
        "pattern_notes_written": len(p_touched),
    }, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
