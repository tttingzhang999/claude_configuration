#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Compute sha256 of a markdown file's body (frontmatter stripped, trailing whitespace trimmed).

Usage: uv run content_hash.py <path-to-md>
"""
import hashlib
import re
import sys
from pathlib import Path


def body_hash(md_text: str) -> str:
    if md_text.startswith("---\n"):
        m = re.match(r"^---\n.*?\n---\n", md_text, re.DOTALL)
        body = md_text[m.end():] if m else md_text
    else:
        body = md_text
    body = "\n".join(line.rstrip() for line in body.splitlines()).strip() + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: content_hash.py <path-to-md>", file=sys.stderr)
        sys.exit(2)
    print(body_hash(Path(sys.argv[1]).read_text()))
