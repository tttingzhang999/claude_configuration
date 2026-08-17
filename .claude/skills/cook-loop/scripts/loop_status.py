#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Detect pending cook tasks for the cook-loop orchestrator.

Scans ~/.claude/projects/ transcripts and the vault, outputs a JSON todo list:

{
  "generated_at": "...",
  "vault_root": "...",
  "checked_dates": ["YYYY-MM-DD", ...],      # yesterday back N days (today excluded)
  "promptlingo_pending": ["YYYY-MM-DD"],     # transcripts exist, report missing
  "meetings_pending": ["<vault-relative path>"],  # raw, uncooked, mtime > 2h
  "progress_stale": [{"project": "...", "last_updated": "...", "days_stale": N}],
  "progress_checked": [{"project": "...", "checked": N}],  # WIP has `- [x]` → sweep to Done
  "digest": {                                # message digest windows (gmail + slack)
    "now": "...", "is_work_window": true,
    "gmail": {"due": true, "window_start_iso": "...", "window_end_iso": "...",
              "window_start_epoch": N, "window_end_epoch": N, "gmail_query": "..."},
    "slack": {"due": true, "window_start_iso": "...", "window_end_iso": "...",
              "window_start_epoch": N, "window_end_epoch": N}
  }
}

Window semantics: [start, end), checkpoint = end of last successful digest.
All time math lives here — the SKILL only consumes ready-made values.

Usage: uv run loop_status.py [--days 7] [--meeting-quiet-hours 2] [--stale-days 7]
"""

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[4]
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"
TAIPEI = timezone(timedelta(hours=8))
TS_RE = re.compile(r'"timestamp"\s*:\s*"([^"]+)"')


def parse_ts(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def jsonl_ts_range(path: Path) -> tuple[datetime, datetime] | None:
    """First and last timestamp in a session JSONL, reading only head and tail."""
    first = last = None
    try:
        with path.open("rb") as f:
            for _ in range(50):
                line = f.readline()
                if not line:
                    break
                m = TS_RE.search(line.decode("utf-8", errors="ignore"))
                if m and (ts := parse_ts(m.group(1))):
                    first = ts
                    break
            size = path.stat().st_size
            f.seek(max(0, size - 65536))
            tail = f.read().decode("utf-8", errors="ignore")
        for line in reversed(tail.splitlines()):
            m = TS_RE.search(line)
            if m and (ts := parse_ts(m.group(1))):
                last = ts
                break
    except OSError:
        return None
    if first is None or last is None:
        return None
    return (first, last)


def active_dates(window: set[date]) -> set[date]:
    """Dates (Asia/Taipei) with actual Claude Code turn timestamps, restricted to window."""
    found: set[date] = set()
    lo, hi = min(window), max(window)
    for jsonl in CLAUDE_PROJECTS.glob("*/*.jsonl"):
        mtime = datetime.fromtimestamp(jsonl.stat().st_mtime, tz=TAIPEI).date()
        if mtime < lo:
            continue
        # Scan actual timestamps instead of interpolating the head→tail range.
        # Reads up to ~400 lines (head + mid + tail sample) to catch multi-day sessions
        # without marking every day in between as "active".
        try:
            with jsonl.open("rb") as f:
                raw = f.read(32768)                     # head ~100 lines
                size = jsonl.stat().st_size
                if size > 32768:
                    f.seek(max(0, size - 32768))
                    raw += f.read()                     # tail ~100 lines
        except OSError:
            continue
        for line in raw.splitlines():
            m = TS_RE.search(line.decode("utf-8", errors="ignore"))
            if not m:
                continue
            ts = parse_ts(m.group(1))
            if ts is None:
                continue
            d = ts.astimezone(TAIPEI).date()
            if lo <= d <= hi:
                found.add(d)
    return found


def frontmatter(path: Path) -> str:
    """Raw frontmatter block, or '' if none."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[:end] if end != -1 else ""


def pending_meetings(quiet_hours: float) -> list[str]:
    now = datetime.now(tz=TAIPEI)
    out = []
    for f in sorted(VAULT_ROOT.glob("01 Work/projects/*/meetings/*.md")):
        fm = frontmatter(f)
        if re.search(r"^cooked:\s*true\b", fm, re.M | re.I):
            continue  # already cooked
        age = now - datetime.fromtimestamp(f.stat().st_mtime, tz=TAIPEI)
        if age < timedelta(hours=quiet_hours):
            continue  # possibly still being written
        out.append(str(f.relative_to(VAULT_ROOT)))
    return out


STATE_FILE = Path(__file__).resolve().parents[1] / "state" / "digest_state.json"
WORK_START_HOUR = 9
WORK_END_HOUR = 20
DIGEST_MAX_LOOKBACK = timedelta(days=7)
DIGEST_MIN_SPAN = timedelta(minutes=5)


def _digest_window(source: str, state: dict, now: datetime,
                   is_work_window: bool, today_midnight: datetime) -> dict:
    """Per-source [start, end) window from that source's checkpoint."""
    last_end = None
    if raw := state.get(source, {}).get("last_end"):
        try:
            last_end = datetime.fromisoformat(raw).astimezone(TAIPEI)
        except ValueError:
            last_end = None
    start = last_end if last_end is not None else today_midnight
    start = max(start, now - DIGEST_MAX_LOOKBACK)
    return {
        "due": is_work_window and (now - start) >= DIGEST_MIN_SPAN,
        "window_start_iso": start.isoformat(timespec="seconds"),
        "window_end_iso": now.isoformat(timespec="seconds"),
        "window_start_epoch": int(start.timestamp()),
        "window_end_epoch": int(now.timestamp()),
    }


def digest_windows() -> dict:
    """Gmail + Slack digest windows [start, end), each from its own checkpoint."""
    now = datetime.now(tz=TAIPEI).replace(microsecond=0)
    is_work_window = (
        now.weekday() < 5 and WORK_START_HOUR <= now.hour < WORK_END_HOUR
    )
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}

    today_midnight = now.replace(hour=0, minute=0, second=0)
    out: dict = {
        "now": now.isoformat(timespec="seconds"),
        "is_work_window": is_work_window,
    }

    gmail = _digest_window("gmail", state, now, is_work_window, today_midnight)
    # Gmail after:/before: with epoch seconds → [start, end)
    gmail["gmail_query"] = (
        f"in:inbox after:{gmail['window_start_epoch']}"
        f" before:{gmail['window_end_epoch']}"
    )
    out["gmail"] = gmail

    # Slack uses the raw epochs to build its two search queries in the skill.
    out["slack"] = _digest_window("slack", state, now, is_work_window, today_midnight)
    return out


def _wip_open_items(max_per_project: int = 5) -> list[dict]:
    """Unchecked action items per project, for the morning brief surfacing."""
    out = []
    for f in sorted(VAULT_ROOT.glob("01 Work/projects/*/Action Items - WIP.md")):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        items = re.findall(r"^\s*- \[ \]\s+(.+?)\s*$", text, re.M)
        if not items:
            continue
        out.append({
            "project": f.parent.name,
            "open": len(items),
            "items": items[:max_per_project],
        })
    return out


def _wip_checked_projects() -> list[dict]:
    """Projects whose WIP has checked `- [x]` items — a cook-loop sweep candidate.
    Detection only; the sweep (classify + move to Done) is LLM work in the skill."""
    out = []
    for f in sorted(VAULT_ROOT.glob("01 Work/projects/*/Action Items - WIP.md")):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        checked = len(re.findall(r"^\s*- \[x\]", text, re.M | re.I))
        if checked:
            out.append({"project": f.parent.name, "checked": checked})
    return out


def _resurface(now: datetime) -> dict | None:
    """Pick one evergreen wiki note to re-expose. Stateless daily rotation
    (day-ordinal % N) so the pick advances each day without a state file."""
    candidates = sorted(
        p for p in VAULT_ROOT.glob("02 Knowledge/**/*.md")
        if p.name != "index.md" and "templates" not in p.parts
    )
    if not candidates:
        return None
    pick = candidates[now.toordinal() % len(candidates)]
    return {"path": str(pick.relative_to(VAULT_ROOT)), "title": pick.stem}


def brief_status() -> dict:
    """Morning brief: due once per day (checkpoint date != today), plus the
    read-side payload (open WIP items + one resurfaced note). Calendar is
    surfaced by the SKILL via MCP at runtime, not here."""
    now = datetime.now(tz=TAIPEI).replace(microsecond=0)
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    last_run = state.get("brief", {}).get("last_end")
    last_date = None
    if last_run:
        try:
            last_date = datetime.fromisoformat(last_run).astimezone(TAIPEI).date()
        except ValueError:
            last_date = None
    return {
        "due": last_date != now.date(),
        "last_run": last_run,
        "now_iso": now.isoformat(timespec="seconds"),
        "wip": _wip_open_items(),
        "resurface": _resurface(now),
    }


def stale_progress(stale_days: int) -> list[dict]:
    today = datetime.now(tz=TAIPEI).date()
    out = []
    for f in sorted(VAULT_ROOT.glob("01 Work/projects/*/Action Items - WIP.md")):
        m = re.search(r"^last_updated:\s*(\d{4}-\d{2}-\d{2})", frontmatter(f), re.M)
        if not m:
            continue
        updated = date.fromisoformat(m.group(1))
        days = (today - updated).days
        if days > stale_days:
            out.append({
                "project": f.parent.name,
                "last_updated": m.group(1),
                "days_stale": days,
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="lookback window (yesterday inclusive)")
    ap.add_argument("--meeting-quiet-hours", type=float, default=2.0)
    ap.add_argument("--stale-days", type=int, default=7)
    args = ap.parse_args()

    today = datetime.now(tz=TAIPEI).date()
    window = {today - timedelta(days=i) for i in range(1, args.days + 1)}
    active = active_dates(window)

    promptlingo_pending = []
    for d in sorted(active):
        iso = d.isoformat()
        report = VAULT_ROOT / "04 English Learning" / "reports" / f"{iso} English Daily.md"
        if not report.exists():
            promptlingo_pending.append(iso)

    result = {
        "generated_at": datetime.now(tz=TAIPEI).isoformat(timespec="seconds"),
        "vault_root": str(VAULT_ROOT),
        "checked_dates": sorted(d.isoformat() for d in window),
        "active_dates": sorted(d.isoformat() for d in active),
        "promptlingo_pending": promptlingo_pending,
        "meetings_pending": pending_meetings(args.meeting_quiet_hours),
        "progress_stale": stale_progress(args.stale_days),
        "progress_checked": _wip_checked_projects(),
        "digest": digest_windows(),
        "brief": brief_status(),
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
