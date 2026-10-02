"""Resolve filesystem paths for promptlingo.

The skill code lives at <vault>/.claude/skills/promptlingo. Learning artifacts
(reports, glossary notes, grammar notes, SRS state) live at <vault>/04 English Learning.
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
GLOSSARY_DIR = LEARNING_DIR / "glossary"
GRAMMAR_DIR = LEARNING_DIR / "grammar"

VOCAB_JSON = DATA_DIR / "vocab.json"
PATTERNS_JSON = DATA_DIR / "patterns.json"

TEMPLATE_DIR = SKILL_DIR / "data" / "templates"

# Grammar categories. Slug is the machine key (frontmatter + skill payload);
# label is the note filename and the human-facing title.
GRAMMAR_CATEGORIES: list[tuple[str, str]] = [
    ("articles-and-determiners", "冠詞與限定詞"),
    ("agreement-and-number", "主謂一致與單複數"),
    ("tense-and-aspect", "時態"),
    ("passive-voice", "被動語態"),
    ("questions", "疑問句與間接問句"),
    ("word-form", "詞性與構詞"),
    ("sentence-boundaries", "句子切分"),
    ("spelling-and-typography", "拼字與排版"),
    ("requests-and-instructions", "提出要求與下指令"),
    ("contrast-and-alternatives", "對比與取捨"),
    ("conditions-and-consequences", "條件、時間與後果"),
    ("inquiry-and-assessment", "探詢與評估"),
    ("other", "未分類"),
]
CATEGORY_LABEL = dict(GRAMMAR_CATEGORIES)
CATEGORY_ORDER = {slug: i for i, (slug, _) in enumerate(GRAMMAR_CATEGORIES)}

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def ensure_dirs() -> None:
    for d in (DATA_DIR, REPORTS_DIR, GLOSSARY_DIR, GRAMMAR_DIR):
        d.mkdir(parents=True, exist_ok=True)


def report_path(date_str: str) -> Path:
    return REPORTS_DIR / f"{date_str} English Daily.md"


def glossary_note_name(level: str) -> str:
    """Note name (no extension) holding every word of one CEFR level."""
    return f"Glossary {level or 'Other'}"


def glossary_note_path(level: str) -> Path:
    return GLOSSARY_DIR / f"{glossary_note_name(level)}.md"


GLOSSARY_INDEX_PATH = GLOSSARY_DIR / "Glossary Index.md"


def word_link(word: str, level: str) -> str:
    """Wikilink to a word's heading inside its level note."""
    return f"[[{glossary_note_name(level)}#{word}|{word}]]"


def grammar_note_path(category: str) -> Path:
    label = CATEGORY_LABEL.get(category, CATEGORY_LABEL["other"])
    return GRAMMAR_DIR / f"{label}.md"
