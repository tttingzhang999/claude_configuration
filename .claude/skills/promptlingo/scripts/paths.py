"""Resolve filesystem paths for promptlingo.

The skill code lives at <vault>/.claude/skills/promptlingo. Learning artifacts
(reports, vocab notes, pattern notes, SRS state) live at <vault>/04 English Learning.
Override with PROMPTLINGO_LEARNING_DIR for tests.
"""
from __future__ import annotations

import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent

_DEFAULT_LEARNING_DIR = SKILL_DIR.parent.parent.parent / "04 English Learning"
LEARNING_DIR = Path(os.environ.get("PROMPTLINGO_LEARNING_DIR") or _DEFAULT_LEARNING_DIR)

DATA_DIR = LEARNING_DIR / "data"
REPORTS_DIR = LEARNING_DIR / "reports"
VOCAB_DIR = LEARNING_DIR / "vocab"
PATTERNS_DIR = LEARNING_DIR / "patterns"

VOCAB_JSON = DATA_DIR / "vocab.json"
PATTERNS_JSON = DATA_DIR / "patterns.json"

TEMPLATE_DIR = SKILL_DIR / "data" / "templates"


def ensure_dirs() -> None:
    for d in (DATA_DIR, REPORTS_DIR, VOCAB_DIR, PATTERNS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def report_path(date_str: str) -> Path:
    return REPORTS_DIR / f"{date_str} English Daily.md"


def vocab_note_path(word: str) -> Path:
    safe = word.strip().lower().replace("/", "-")
    return VOCAB_DIR / f"{safe}.md"


def pattern_note_path(slug: str) -> Path:
    safe = slug.strip().lower().replace("/", "-").replace(" ", "-")[:80]
    return PATTERNS_DIR / f"{safe}.md"
