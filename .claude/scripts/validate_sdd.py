#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Validate an SDD change folder's four-pack against the M2 schema.

Usage:
    uv run .claude/scripts/validate_sdd.py <path-to-SDD-change-folder>

Checks proposal.md frontmatter (propose_tier / status / required fields) and
tasks.md per-task task tier. Exits non-zero on any ERROR so a gate hook can
block on it. Shared by the propose/apply skills and the gate hook (one source).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

PROPOSE_TIERS = {"lint", "unit", "integration", "e2e", "e2e-live"}
STATUSES = {"proposed", "approved", "applying", "verifying", "reviewing", "verified", "delivered", "archived"}
TASK_TIERS = {"sonnet", "opus"}  # haiku 已停用；舊 tasks.md 的 [haiku] 不溯及既往，只在新提案禁用
REQUIRED_PROPOSAL = {"ticket", "title", "propose_tier", "status", "design_approved"}
TASK_LINE = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*(.*)$")
MODEL_TAG = re.compile(r"[`\[]\s*([a-z0-9-]+)\s*[`\]]")


def read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path.name}: 缺 YAML frontmatter")
    _, fm, _ = text.split("---", 2)
    return yaml.safe_load(fm) or {}


def validate_proposal(path: Path, errors: list, warnings: list) -> None:
    fm = read_frontmatter(path)
    missing = REQUIRED_PROPOSAL - fm.keys()
    if missing:
        errors.append(f"proposal.md: 缺必填欄 {sorted(missing)}")
    if fm.get("type") != "proposal":
        errors.append("proposal.md: 需 type: proposal（tickets.base 靠它過濾）")
    tier = fm.get("propose_tier")
    if tier is not None and tier not in PROPOSE_TIERS:
        errors.append(f"proposal.md: propose_tier '{tier}' 不在 {sorted(PROPOSE_TIERS)}")
    status = fm.get("status")
    if status is not None and status not in STATUSES:
        errors.append(f"proposal.md: status '{status}' 不在 {sorted(STATUSES)}")
    if not isinstance(fm.get("design_approved"), bool):
        errors.append("proposal.md: design_approved 必須是 boolean")
    jira = str(fm.get("jira", ""))
    if not jira or "your-org" in jira or jira.upper() == "TBD":
        warnings.append("proposal.md: jira 是 placeholder / 未填（提供真實票號前先容忍）")


def validate_tasks(path: Path, errors: list) -> None:
    n = 0
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = TASK_LINE.match(line)
        if not m:
            continue
        n += 1
        found = set(MODEL_TAG.findall(m.group(1)))
        if not found & TASK_TIERS:
            if "haiku" in found:
                errors.append(f"tasks.md:L{i}: [haiku] 已停用，改標 [sonnet]")
            else:
                errors.append(f"tasks.md:L{i}: task 缺 task tier 標記 [sonnet|opus]")
    if n == 0:
        errors.append("tasks.md: 找不到任何 `- [ ]` task")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    folder = Path(sys.argv[1])
    if not folder.is_dir():
        print(f"ERROR: 不是資料夾: {folder}")
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    proposal = folder / "proposal.md"
    tasks = folder / "tasks.md"
    if proposal.exists():
        validate_proposal(proposal, errors, warnings)
    else:
        errors.append("缺 proposal.md")
    if tasks.exists():
        validate_tasks(tasks, errors)
    # design.md / specs 存在性是線性鏈的「下一步」指標，非硬錯，故不擋。

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n✗ {folder.name}: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"✓ {folder.name}: schema OK ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
