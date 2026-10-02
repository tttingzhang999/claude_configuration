#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Validate SDD artifacts and expose shared task progress and review fingerprints.

Default draft mode allows missing artifacts. Ready mode checks planning inputs,
not human approval, test results, or semantic correctness. No command writes files.
Task checkbox semantics follow OpenSpec v1.13.2 (db230978).
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re

import yaml

PROPOSE_TIERS = frozenset({"lint", "unit", "integration", "e2e", "e2e-live"})
STATUSES = frozenset({"proposed", "approved", "applying", "verifying", "reviewing", "verified", "delivered", "archived"})
TASK_TIERS = frozenset({"sonnet", "opus"})
REQUIRED_PROPOSAL = frozenset({"ticket", "title", "propose_tier", "status", "design_approved"})
TASK_LINE = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])\s*\[(?:\s*([^\]\s]?)\s*\](?![([])|\s+\])\s*(.*)")
MODEL_TAG = re.compile(r"\[(sonnet|opus|haiku)\]")
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---(?:\n|$)", re.S)
# Process metadata must not invalidate otherwise identical reviewed plans.
PROCESS_FIELDS = frozenset({"status", "design_approved", "pr", "spec_sync"})


@dataclass(frozen=True)
class Task:
    line: int
    done: bool
    text: str


def parse_tasks(text: str) -> tuple[Task, ...]:
    """Count every checkbox, including unknown one-character pending markers."""
    return tuple(
        Task(number, (match[1] or "").lower() == "x", match[2].strip())
        for number, line in enumerate(text.splitlines(), 1)
        if (match := TASK_LINE.match(line))
    )


def read_frontmatter(path: Path) -> dict:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{path.name}: 缺少完整 YAML frontmatter")
    value = yaml.safe_load(match[1])
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: frontmatter 必須是 mapping")
    return value


def prose_lines(text: str) -> tuple[str, ...]:
    """Blank fenced examples/comments before parsing Markdown structure."""
    clean = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    fence = ""
    output: tuple[str, ...] = ()
    for line in clean.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            if not fence:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = ""
            output += ("",)
        else:
            output += ("" if fence else line,)
    return output


def declared_capabilities(text: str) -> tuple[str, ...]:
    active = False
    names: tuple[str, ...] = ()
    for line in prose_lines(text):
        if line.startswith("## "):
            active = False
        if line.startswith("### "):
            active = line.strip() in {"### New Capabilities", "### Modified Capabilities"}
        if active and (match := re.match(r"^\s*[-*+]\s+`([^`]+)`", line)):
            names += (match[1],)
    return names


def spec_errors(path: Path) -> tuple[str, ...]:
    lines = prose_lines(path.read_text(encoding="utf-8"))
    text = "\n".join(lines)
    sections = tuple(re.finditer(r"^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\s*$", text, re.M))
    errors: tuple[str, ...] = ()
    if not sections:
        return (f"{path.name}: 缺 delta Requirements 區段",)
    for index, section in enumerate(sections):
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        body = text[section.end():end]
        kind = section[1]
        if kind == "RENAMED":
            pairs = re.findall(r"^\s*(?:[-*+]\s*)?(FROM|TO):\s*`?### Requirement:\s*([^\n`]+)`?\s*$", body, re.M)
            if not pairs or tuple(pair[0] for pair in pairs) != ("FROM", "TO") * (len(pairs) // 2):
                errors += (f"{path.name}: RENAMED 需要成對 FROM/TO",)
            continue
        requirements = tuple(re.finditer(r"^### Requirement:\s*(.+)$", body, re.M))
        if not requirements:
            errors += (f"{path.name}: {kind} 缺 Requirement",)
        for number, requirement in enumerate(requirements):
            stop = requirements[number + 1].start() if number + 1 < len(requirements) else len(body)
            block = body[requirement.end():stop]
            label = f"{path.name}: {requirement[1]}"
            if kind == "REMOVED":
                if not all(re.search(rf"\*\*{field}\*\*:\s*\S", block) for field in ("Reason", "Migration")):
                    errors += (f"{label}: REMOVED 需要 Reason/Migration",)
            else:
                scenarios = re.findall(r"^#### Scenario:\s*[^\n]+\n(.*?)(?=^#{2,4} |\Z)", block, re.M | re.S)
                if not scenarios or any(not all(re.search(rf"^\s*(?:[-*+]\s*)?(?:\*\*)?{clause}(?:\*\*)?(?:\s*:)?[ \t]+\S", item, re.M) for clause in ("WHEN", "THEN")) for item in scenarios):
                    errors += (f"{label}: 需要有 WHEN/THEN 內容的 #### Scenario",)
    return errors


def validate_folder(folder: Path, mode: str = "draft") -> tuple[tuple[str, ...], tuple[str, ...]]:
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    if not folder.is_dir():
        return (f"不是資料夾: {folder}",), ()
    try:
        fm = read_frontmatter(folder / "proposal.md")
        missing = REQUIRED_PROPOSAL - fm.keys()
        if missing:
            errors += (f"proposal.md: 缺必填欄 {sorted(missing)}",)
        if fm.get("type") != "proposal":
            errors += ("proposal.md: 需 type: proposal",)
        for field, choices in (("propose_tier", PROPOSE_TIERS), ("status", STATUSES)):
            if not isinstance(fm.get(field), str) or fm[field] not in choices:
                errors += (f"proposal.md: 無效 {field}",)
        if not isinstance(fm.get("design_approved"), bool):
            errors += ("proposal.md: design_approved 必須是 boolean",)
        skip = fm.get("skip_specs", False)
        if not isinstance(skip, bool):
            errors += ("proposal.md: skip_specs 必須是 boolean",)
        reason = fm.get("skip_specs_reason")
        if skip is True and (not isinstance(reason, str) or not reason.strip()):
            errors += ("proposal.md: skip_specs 需要 skip_specs_reason",)
        if not fm.get("jira") or str(fm["jira"]).upper() == "TBD" or "your-org" in str(fm["jira"]):
            warnings += ("proposal.md: jira 是 placeholder / 未填",)
        specs = tuple(sorted((folder / "specs").rglob("*.md")))
        capabilities = declared_capabilities((folder / "proposal.md").read_text(encoding="utf-8"))
        if skip is True and (specs or capabilities):
            errors += ("skip_specs 與 capabilities/specs 矛盾；經 update 處理，不得忽略",)
        if mode == "ready":
            for name in ("design.md", "tasks.md"):
                path = folder / name
                if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                    errors += (f"缺少非空的 {name}",)
            if skip is not True:
                if not specs or not capabilities:
                    errors += ("需要 capabilities 及對應 specs，或明確 skip_specs",)
                for capability in capabilities:
                    relative = Path(capability)
                    if relative.is_absolute() or ".." in relative.parts:
                        errors += (f"不合法 capability path: {capability}",)
                    elif not (folder / "specs" / f"{capability}.md").is_file():
                        errors += (f"缺 specs/{capability}.md",)
                for spec in specs:
                    name = spec.relative_to(folder / "specs").with_suffix("").as_posix()
                    if name not in capabilities:
                        errors += (f"未宣告 capability: {name}",)
                    errors += spec_errors(spec)
        tasks_path = folder / "tasks.md"
        if tasks_path.exists():
            tasks = parse_tasks(tasks_path.read_text(encoding="utf-8"))
            if not tasks:
                errors += ("tasks.md: 找不到 checkbox task",)
            for task in tasks:
                tiers = frozenset(MODEL_TAG.findall(task.text))
                if len(tiers) != 1 or not tiers <= TASK_TIERS:
                    errors += (f"tasks.md:L{task.line}: task 需單一 [sonnet|opus] tier",)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        errors += (f"無法驗證: {error}",)
    return errors, warnings


def plan_fingerprint(folder: Path) -> str:
    """Hash semantic planning inputs, excluding lifecycle fields and checkmarks."""
    paths = tuple(folder / name for name in ("proposal.md", "design.md", "tasks.md")) + tuple(sorted((folder / "specs").rglob("*.md"))) + tuple(sorted((folder / "baseline").rglob("*.md")))
    entries: tuple[tuple[str, str], ...] = ()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if path == folder / "proposal.md":
            metadata = {key: value for key, value in read_frontmatter(path).items() if key not in PROCESS_FIELDS}
            text = yaml.safe_dump(metadata, sort_keys=True) + FRONTMATTER.sub("", text, count=1)
        if path == folder / "tasks.md":
            text = "\n".join(f"- [ ] {match[2].strip()}" if (match := TASK_LINE.match(line)) else line for line in text.splitlines())
        entries += ((path.relative_to(folder).as_posix(), text.strip()),)
    return hashlib.sha256(json.dumps(entries, ensure_ascii=False).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--mode", choices=("draft", "ready"), default="draft")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--tasks-json", action="store_true")
    action.add_argument("--fingerprint", action="store_true")
    action.add_argument("--approval", action="store_true")
    args = parser.parse_args()
    try:
        if args.approval:
            approved = read_frontmatter(args.folder / "proposal.md").get("design_approved") is True
            print("true" if approved else "false")
            return 0 if approved else 1
        if args.tasks_json:
            tasks = parse_tasks((args.folder / "tasks.md").read_text(encoding="utf-8"))
            print(json.dumps({"tasks": tuple(asdict(task) for task in tasks), "total": len(tasks), "completed": sum(task.done for task in tasks)}))
            return 0
        errors, warnings = validate_folder(args.folder, args.mode)
        if args.fingerprint:
            if errors:
                print("\n".join(f"ERROR {error}" for error in errors))
                return 1
            print(plan_fingerprint(args.folder))
            return 0
        for warning in warnings:
            print(f"WARN  {warning}")
        for error in errors:
            print(f"ERROR {error}")
        print(f"{args.folder.name}: {len(errors)} error(s), {len(warnings)} warning(s), mode={args.mode}")
        return 1 if errors else 0
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        print(f"ERROR {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
