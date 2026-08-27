#!/usr/bin/env python3
"""Manage a private, evidence-gated memory for Code Health Review.

The memory is intentionally stored outside the skill package. The skill package
contains the protocol; this store contains local review feedback and lessons.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("~/.codex/code-health-memory").expanduser()
STATUSES = {"candidate", "validated", "global-rule", "superseded", "invalidated"}
BLOCKED_STATUSES = {"superseded", "invalidated"}
SUSPICIOUS_SECRET = re.compile(
    r"(?:github_pat_|ghp_|sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{24,})"
)


def today() -> str:
    return dt.date.today().isoformat()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def paths(root: Path) -> tuple[Path, Path, Path]:
    return root / "index.md", root / "memories", root / "audit.log"


def ensure_root(root: Path) -> tuple[Path, Path, Path]:
    index, memories, audit = paths(root)
    root.mkdir(parents=True, exist_ok=True)
    memories.mkdir(parents=True, exist_ok=True)
    if not index.exists():
        write_index(index, [])
    if not audit.exists():
        audit.touch()
    return index, memories, audit


def read_index(index: Path) -> list[dict[str, Any]]:
    if not index.exists():
        return []
    text = index.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if not match:
        raise ValueError(f"invalid memory index: JSON block not found: {index}")
    payload = json.loads(match.group(1))
    memories = payload.get("memories", [])
    if not isinstance(memories, list):
        raise ValueError("invalid memory index: memories is not a list")
    return [item for item in memories if isinstance(item, dict)]


def write_index(index: Path, memories: list[dict[str, Any]]) -> None:
    payload = {
        "memories": sorted(
            memories,
            key=lambda item: (str(item.get("updated_at", "")), str(item.get("id", ""))),
            reverse=True,
        )
    }
    text = "---\ntitle: Code Health Review Memory Index\nupdated_at: " + today() + "\n---\n\n"
    text += "```json\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```\n"
    index.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=index.parent, delete=False) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(index)


def audit(audit_path: Path, action: str, detail: str) -> None:
    safe_detail = re.sub(r"[\r\n\t]+", " ", detail).strip()
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{now()} {action} {safe_detail}\n")


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [str(item).strip() for item in values if str(item).strip()]


def safe_text(value: Any) -> str:
    text = str(value or "").strip()
    if SUSPICIOUS_SECRET.search(text):
        raise ValueError("memory contains a credential-like value; remove it before recording")
    return text


def safe_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    if not normalized:
        raise ValueError("memory id must contain letters, digits, or hyphens")
    return normalized[:100]


def memory_body(record: dict[str, Any]) -> str:
    sections = [f"# {safe_text(record['title'])}", ""]
    fields = [
        ("What was missed", "what_was_missed"),
        ("Evidence", "evidence"),
        ("Missed signal", "missed_signal"),
        ("Root cause", "root_cause"),
        ("Detection rule", "detection_rule"),
        ("Required test", "required_test"),
        ("Negative control", "negative_control"),
        ("Scope and notes", "notes"),
    ]
    for heading, key in fields:
        value = record.get(key, []) if key not in {"what_was_missed", "missed_signal", "root_cause", "detection_rule", "required_test", "negative_control", "notes"} else record.get(key, "")
        if isinstance(value, list):
            if not value:
                continue
            content = "\n".join(f"- {safe_text(item)}" for item in value)
        else:
            content = safe_text(value)
        if content:
            sections.extend([f"## {heading}", content, ""])
    return "\n".join(sections).rstrip() + "\n"


def record_memory(root: Path, input_path: Path, replace: bool) -> None:
    index, memories_dir, audit_path = ensure_root(root)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("record input must be a JSON object")
    for required in ("id", "title", "missed_signal", "root_cause", "detection_rule", "required_test"):
        if not safe_text(payload.get(required)):
            raise ValueError(f"missing required field: {required}")

    memory_id = safe_id(str(payload["id"]))
    existing = read_index(index)
    if any(str(item.get("id")) == memory_id for item in existing) and not replace:
        raise ValueError(f"memory already exists: {memory_id}; use --replace to update it")

    record: dict[str, Any] = {
        "id": memory_id,
        "title": safe_text(payload["title"]),
        "status": safe_text(payload.get("status") or "candidate"),
        "confidence": safe_text(payload.get("confidence") or "medium"),
        "created_at": safe_text(payload.get("created_at") or today()),
        "updated_at": today(),
        "repo": safe_text(payload.get("repo")),
        "review_id": safe_text(payload.get("review_id")),
        "source": safe_text(payload.get("source")),
        "services": [safe_text(item) for item in as_list(payload.get("services"))],
        "task_types": [safe_text(item) for item in as_list(payload.get("task_types"))],
        "symptoms": [safe_text(item) for item in as_list(payload.get("symptoms"))],
        "tags": [safe_text(item) for item in as_list(payload.get("tags"))],
        "supersedes": [safe_text(item) for item in as_list(payload.get("supersedes"))],
        "superseded_by": safe_text(payload.get("superseded_by")),
        "what_was_missed": safe_text(payload["missed_signal"]),
        "evidence": [safe_text(item) for item in as_list(payload.get("evidence"))],
        "missed_signal": safe_text(payload["missed_signal"]),
        "root_cause": safe_text(payload["root_cause"]),
        "detection_rule": safe_text(payload["detection_rule"]),
        "required_test": safe_text(payload["required_test"]),
        "negative_control": safe_text(payload.get("negative_control")),
        "regression_test": safe_text(payload.get("regression_test")),
        "notes": safe_text(payload.get("notes")),
    }
    if record["status"] not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(STATUSES))}")
    if record["status"] in {"validated", "global-rule"} and not record["evidence"]:
        raise ValueError("validated memories require evidence; record as candidate first")

    body_path = memories_dir / f"{memory_id}.md"
    body_path.write_text(memory_body(record), encoding="utf-8")
    entry = {key: value for key, value in record.items() if key not in {"what_was_missed", "missed_signal", "root_cause", "detection_rule", "negative_control", "notes"}}
    entry["file"] = body_path.name
    entry["action"] = record["detection_rule"]
    entry["evidence"] = record["evidence"]
    updated = [item for item in existing if str(item.get("id")) != memory_id]
    updated.append(entry)
    write_index(index, updated)
    audit(audit_path, "WRITE", f"record id={memory_id} status={record['status']}")
    print(f"recorded {memory_id} ({record['status']}) at {body_path}")


def haystack(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False).lower()


def select_memories(root: Path, args: argparse.Namespace) -> None:
    index, memories_dir, audit_path = ensure_root(root)
    items = read_index(index)
    queries = {
        "repo": [item.lower() for item in args.repo],
        "services": [item.lower() for item in args.service],
        "symptoms": [item.lower() for item in args.symptom],
        "tags": [item.lower() for item in args.tag],
        "task_types": [item.lower() for item in args.task_type],
    }
    weights = {"repo": 8, "services": 8, "symptoms": 6, "tags": 4, "task_types": 5}
    ranked: list[tuple[int, dict[str, Any]]] = []
    status_bonus = {"global-rule": 12, "validated": 8, "candidate": 2}
    for item in items:
        if str(item.get("status")) in BLOCKED_STATUSES:
            continue
        text = haystack(item)
        score = status_bonus.get(str(item.get("status")), 0)
        matched = False
        for field, terms in queries.items():
            for term in terms:
                if term and term in text:
                    score += weights[field]
                    matched = True
        if any(queries.values()) and not matched:
            continue
        ranked.append((score, item))
    ranked.sort(key=lambda row: (row[0], str(row[1].get("updated_at", ""))), reverse=True)
    selected = ranked[: max(1, min(args.limit, 8))]
    audit(audit_path, "READ", f"select count={len(selected)}")
    if not selected:
        print("Applied: none")
        return
    print("## Code Health memory candidates")
    for rank, (score, item) in enumerate(selected, 1):
        print(f"\n{rank}. {item.get('id', 'unknown')} — {item.get('title', '')}")
        print(f"   status={item.get('status', 'unknown')}; confidence={item.get('confidence', 'unknown')}; score={score}; file={item.get('file', '')}")
        print(f"   detection_rule: {item.get('action', '')}")
        evidence = item.get("evidence", [])
        if evidence:
            print("   evidence:")
            for line in evidence[:4]:
                print(f"   - {line}")
        body_path = memories_dir / str(item.get("file", ""))
        if body_path.is_file():
            body = body_path.read_text(encoding="utf-8")
            match = re.search(r"(?ms)^##\s+(?:Detection rule|Required test)\s*\n(.*?)(?=^##\s|\Z)", body)
            if match:
                excerpt = re.sub(r"\n{2,}", "\n", match.group(1)).strip()
                if len(excerpt) > args.max_chars:
                    excerpt = excerpt[: args.max_chars].rstrip() + "…"
                print(f"   strategy: {excerpt}")


def update_status(root: Path, memory_id: str, target: str, approved_by: str, cross_project: list[str]) -> None:
    index, _, audit_path = ensure_root(root)
    items = read_index(index)
    match = next((item for item in items if str(item.get("id")) == memory_id), None)
    if match is None:
        raise ValueError(f"memory not found: {memory_id}")
    current = str(match.get("status", "candidate"))
    if target == "validated" and current not in {"candidate", "validated"}:
        raise ValueError(f"cannot promote {current} to validated")
    if target == "global-rule" and current != "validated":
        raise ValueError("global-rule promotion requires a validated memory")
    if not approved_by:
        raise ValueError("promotion requires --approved-by")
    evidence = match.get("evidence", [])
    if not evidence:
        raise ValueError("promotion requires recorded evidence")
    if target == "validated" and not (match.get("regression_test") or match.get("required_test")):
        raise ValueError("validated promotion requires a regression test or required test")
    if target == "global-rule" and len(set(cross_project)) < 2:
        raise ValueError("global-rule promotion requires --cross-project for at least two contexts")
    match["status"] = target
    match["updated_at"] = today()
    match["approved_by"] = approved_by
    if cross_project:
        match["cross_project"] = cross_project
    write_index(index, items)
    audit(audit_path, "WRITE", f"promote id={memory_id} to={target} approved_by={approved_by}")
    print(f"promoted {memory_id}: {current} -> {target}")


def supersede(root: Path, memory_id: str, replacement: str, approved_by: str) -> None:
    index, _, audit_path = ensure_root(root)
    items = read_index(index)
    match = next((item for item in items if str(item.get("id")) == memory_id), None)
    if match is None:
        raise ValueError(f"memory not found: {memory_id}")
    match["status"] = "superseded"
    match["superseded_by"] = replacement
    match["updated_at"] = today()
    write_index(index, items)
    audit(audit_path, "WRITE", f"supersede id={memory_id} by={replacement} approved_by={approved_by or 'unspecified'}")
    print(f"superseded {memory_id} with {replacement}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="private memory root")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="initialize the private memory store")

    record = sub.add_parser("record", help="record a candidate or validated lesson from JSON")
    record.add_argument("--input", type=Path, required=True)
    record.add_argument("--replace", action="store_true")

    select = sub.add_parser("select", help="select relevant memories")
    select.add_argument("--repo", action="append", default=[])
    select.add_argument("--service", action="append", default=[])
    select.add_argument("--symptom", action="append", default=[])
    select.add_argument("--tag", action="append", default=[])
    select.add_argument("--task-type", action="append", default=[])
    select.add_argument("--limit", type=int, default=3)
    select.add_argument("--max-chars", type=int, default=1200)

    promote = sub.add_parser("promote", help="promote after evidence and approval")
    promote.add_argument("id")
    promote.add_argument("--to", choices=("validated", "global-rule"), required=True)
    promote.add_argument("--approved-by", required=True)
    promote.add_argument("--cross-project", action="append", default=[])

    replace = sub.add_parser("supersede", help="mark an older lesson as superseded")
    replace.add_argument("id")
    replace.add_argument("--by", required=True, dest="replacement")
    replace.add_argument("--approved-by", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.expanduser().resolve()
    try:
        if args.command == "init":
            index, memories, audit_path = ensure_root(root)
            audit(audit_path, "WRITE", "init")
            print(f"initialized {root} (index={index}, memories={memories})")
        elif args.command == "record":
            record_memory(root, args.input.expanduser().resolve(), args.replace)
        elif args.command == "select":
            select_memories(root, args)
        elif args.command == "promote":
            update_status(root, safe_id(args.id), args.to, args.approved_by, args.cross_project)
        elif args.command == "supersede":
            supersede(root, safe_id(args.id), safe_id(args.replacement), args.approved_by)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"review memory failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
