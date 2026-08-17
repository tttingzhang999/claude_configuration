#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Sync the publishable agent + LLM-wiki config from the private Obsidian vault
into this public repo, sanitizing personal / employer / client data on the way.

Usage:
    cp sanitize-rules.example.py sanitize-rules.local.py   # once, then fill it in
    VAULT_ROOT="/path/to/your/vault" uv run sync-from-vault.py [--check]

Flow:
    1. Load the scrubbing rules from sanitize-rules.local.py (gitignored — the
       mapping names the very identifiers this export removes, so it never ships).
    2. Wipe the managed mirror paths in this repo (never touches native files
       like README / LICENSE / templates / this script).
    3. Copy each manifest entry from the vault, skipping EXCLUDE patterns.
    4. Sanitize every copied text file via SUBSTITUTIONS.
    5. Drop the two wholesale-replaced files in from templates/.
    6. FINAL SCAN for any leaked sensitive token; fail-closed (exit 1) if found.

--check does everything but leaves the result staged for `git diff` review
(same as normal run — nothing is committed or pushed by this script).
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent

# --- Managed mirror paths (wiped + recopied each run; native files untouched) ---
MANAGED = [
    "CLAUDE.md",
    "Context Map.md",
    "index.md",
    "index.base",
    "install.sh",
    ".claude",
    "00 Self",
    "01 Work",
    "03 Writing",
]

# --- Manifest: vault-relative paths to copy (file or dir) ---
# Anything not listed here is deliberately NOT portable: employer-specific skills
# (ticketing, internal services, cluster access) and empty placeholders.
PORTABLE_SKILLS = [
    "sdd-propose", "sdd-apply", "sdd-verify", "sdd-review",
    "sdd-deliver", "sdd-orch",
    "code-reviewer", "write-article", "promptlingo", "repo-router",
    "cook-meeting", "cook-progress", "cook-staging",
    "cook-loop", "cook-messages", "cook-blog-publish",
    "vocab", "openclaw",
]
MANIFEST = [
    "CLAUDE.md",
    "Context Map.md",
    "index.md",
    "index.base",
    "install.sh",
    ".claude/CLAUDE.md",
    ".claude/rules",
    ".claude/hooks",
    ".claude/scripts/validate_sdd.py",
    "00 Self/CLAUDE.md",
    "01 Work/CLAUDE.md",
    "01 Work/projects/_template",
    "03 Writing/writing-board.base",
] + [f".claude/skills/{s}" for s in PORTABLE_SKILLS]

# --- Never copy (machine state, caches, secrets) ---
EXCLUDE = [
    "__pycache__", ".ruff_cache", ".pytest_cache",
    ".DS_Store", "settings.local.json",
    "/state/",              # per-skill machine state (loop checkpoints, run state)
    "promptlingo/data/",    # personal learning store (templates re-added below)
    "vocab/data/",          # personal vocabulary progress
]

# --- Files replaced wholesale by a bundled example (not copied+sanitized) ---
WHOLESALE = {
    ".claude/skills/repo-router/repos.yaml": "templates/repos.example.yaml",
    ".claude/skills/cook-messages/config.json": "templates/cook-messages.config.example.json",
}

# --- Sanitization rules live OUTSIDE this repo -----------------------------
# sanitize-rules.local.py is gitignored. It is the only place that names the real
# identifiers being scrubbed, and committing that mapping would publish exactly
# what this export exists to remove. See sanitize-rules.example.py.
RULES_FILE = REPO / "sanitize-rules.local.py"


def load_rules():
    if not RULES_FILE.exists():
        print(
            f"ERROR: {RULES_FILE.name} not found.\n"
            "       cp sanitize-rules.example.py sanitize-rules.local.py and fill it in.\n"
            "       It stays gitignored — the mapping must never be committed.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    spec = importlib.util.spec_from_file_location("sanitize_rules", RULES_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SUBSTITUTIONS, mod.FORBIDDEN


# Standalone-token boundary for the "word" rule kind. NOT `\b`: regex counts `_`
# as a word char, so `\bNAME\b` silently misses `_as NAME_` in markdown emphasis —
# and the scan missed it too, because it used the same `\b`. Underscores and other
# punctuation must count as edges.
def word(token: str) -> str:
    return rf"(?<![A-Za-z0-9]){token}(?![A-Za-z0-9])"


def compile_pattern(kind: str, pattern: str) -> str:
    if kind == "word":
        return word(pattern)
    if kind == "re":
        return pattern
    raise ValueError(f"unknown rule kind {kind!r} (expected 're' or 'word')")


# --- Sanitizer + fail-closed scan, both built from the private rules file ---
_SUBS, _FORBIDDEN = load_rules()
SUBSTITUTIONS = [(compile_pattern(k, p), r) for k, p, r in _SUBS]
FORBIDDEN = re.compile("|".join(compile_pattern(k, p) for k, p in _FORBIDDEN))

TEXT_SUFFIXES = {".md", ".py", ".js", ".json", ".yaml", ".yml", ".sh", ".base", ".txt"}


def is_excluded(path_str: str) -> bool:
    return any(pat in path_str for pat in EXCLUDE)


def sanitize(text: str) -> str:
    for pat, repl in SUBSTITUTIONS:
        text = re.sub(pat, repl, text)
    return text


def copy_entry(vault: Path, rel: str) -> list[Path]:
    src = vault / rel
    dst = REPO / rel
    written: list[Path] = []
    if not src.exists():
        print(f"  ! missing in vault, skipped: {rel}")
        return written
    files = [src] if src.is_file() else [p for p in src.rglob("*") if p.is_file()]
    for f in files:
        rel_f = f.relative_to(vault)
        if is_excluded(str(rel_f)):
            continue
        target = REPO / rel_f
        target.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix.lower() in TEXT_SUFFIXES:
            target.write_text(sanitize(f.read_text(encoding="utf-8")), encoding="utf-8")
        else:
            shutil.copy2(f, target)
        written.append(target)
    return written


def final_scan() -> list[str]:
    hits: list[str] = []
    for f in REPO.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in TEXT_SUFFIXES:
            continue
        # The rules files are the only ones allowed to name what is being scrubbed;
        # sanitize-rules.local.py is gitignored and never ships. templates/ holds
        # the bundled example configs that WHOLESALE drops in.
        if REPO / "templates" in f.parents or f.name.startswith("sanitize-rules."):
            continue
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if FORBIDDEN.search(line):
                    hits.append(f"{f.relative_to(REPO)}:{i}: {line.strip()[:100]}")
        except UnicodeDecodeError:
            continue
    return hits


def main() -> int:
    vault = os.environ.get("VAULT_ROOT")
    if not vault:
        print("ERROR: set VAULT_ROOT to the private vault path.", file=sys.stderr)
        return 2
    vault_root = Path(vault).expanduser().resolve()
    if not (vault_root / "CLAUDE.md").exists():
        print(f"ERROR: {vault_root} does not look like the vault.", file=sys.stderr)
        return 2

    print(f"Vault:  {vault_root}\nRepo:   {REPO}\n")
    for m in MANAGED:
        p = REPO / m
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    total = 0
    for rel in MANIFEST:
        n = len(copy_entry(vault_root, rel))
        total += n
        print(f"  + {rel}  ({n} file{'s' if n != 1 else ''})")

    for dst_rel, tmpl_rel in WHOLESALE.items():
        dst = REPO / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / tmpl_rel, dst)
        print(f"  ~ {dst_rel}  (from {tmpl_rel})")

    print(f"\nCopied {total} files. Running final sanitization scan...")
    hits = final_scan()
    if hits:
        print(f"\n✗ FAIL-CLOSED: {len(hits)} sensitive token(s) remain:\n", file=sys.stderr)
        for h in hits[:50]:
            print("  " + h, file=sys.stderr)
        print("\nAdd a rule to SUBSTITUTIONS and re-run. Nothing was committed.", file=sys.stderr)
        return 1
    print("✓ Clean. Review with `git -C <repo> diff` then commit/push manually.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
