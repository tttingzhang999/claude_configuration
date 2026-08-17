#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Checkpoint store for cook-loop message digests.

State file: <skill>/state/digest_state.json
{
  "gmail": {"last_end": "2026-06-12T11:00:00+08:00"},
  "slack": {"last_end": "2026-06-12T11:00:00+08:00"},
  "brief": {"last_end": "2026-06-29T08:00:00+08:00"}
}

Usage:
  uv run digest_state.py get
  uv run digest_state.py set gmail <ISO-8601 timestamp>
  uv run digest_state.py set slack <ISO-8601 timestamp>
  uv run digest_state.py set brief <ISO-8601 timestamp>
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parents[1] / "state" / "digest_state.json"
SERVICES = ("gmail", "slack", "brief")


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=STATE_FILE.parent, suffix=".tmp", delete=False, encoding="utf-8"
    ) as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        tmp = Path(f.name)
    tmp.rename(STATE_FILE)


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["get"]:
        json.dump(load_state(), sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0
    if len(args) == 3 and args[0] == "set":
        service, raw_ts = args[1], args[2]
        if service not in SERVICES:
            print(f"unknown service: {service} (expected {SERVICES})", file=sys.stderr)
            return 1
        try:
            ts = datetime.fromisoformat(raw_ts)
        except ValueError:
            print(f"invalid ISO-8601 timestamp: {raw_ts}", file=sys.stderr)
            return 1
        if ts.tzinfo is None:
            print(f"timestamp must be timezone-aware: {raw_ts}", file=sys.stderr)
            return 1
        state = load_state()
        state = {**state, service: {"last_end": ts.isoformat(timespec="seconds")}}
        save_state(state)
        print(f"{service}.last_end = {ts.isoformat(timespec='seconds')}")
        return 0
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
