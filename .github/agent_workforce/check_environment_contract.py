#!/usr/bin/env python3
"""Fail when an active worker task lacks the required environment contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


GATED_STATUSES = {"working", "review", "pr", "verified"}


def clean(value: str):
    value = value.strip().rstrip(",")
    if value in {"null", "~", ""}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def task_blocks(content: str) -> list[dict]:
    section = re.search(r"^tasks:\s*\n(?P<body>.*?)(?=^[A-Za-z_][\w-]*:\s*(?:\n|$)|\Z)", content, re.MULTILINE | re.DOTALL)
    if not section:
        return []
    records = []
    for block in re.split(r"(?=^\s{2}-\s)", section.group("body"), flags=re.MULTILINE):
        if not re.match(r"^\s{2}-\s", block):
            continue
        record = {}
        if re.match(r"^\s{2}-\s*\{", block):
            for key in ("id", "status", "environment_attested", "environment_observed", "codespace_name", "environment_evidence", "environment_exception_approved", "environment_exception_decision"):
                match = re.search(rf"(?:\{{|,)\s*{key}:\s*([^,}}]+)", block)
                if match:
                    record[key] = clean(match.group(1))
        else:
            start = re.match(r"^\s{2}-\s+([\w-]+):\s*([^\n]*)", block)
            if start:
                record[start.group(1)] = clean(start.group(2))
            for match in re.finditer(r"^\s{4}([\w-]+):\s*(.*)$", block, re.MULTILINE):
                record[match.group(1)] = clean(match.group(2))
        if record.get("id") is not None:
            records.append(record)
    return records


def main() -> int:
    board = Path("project/TASK_BOARD.yaml")
    if not board.is_file():
        print(json.dumps({"status": "error", "error": "project/TASK_BOARD.yaml missing"}))
        return 2
    content = board.read_text(encoding="utf-8")
    required = bool(re.search(r"^environment_policy:\s*\n(?:^\s{2}.*\n)*?^\s{2}required:\s*[\"']?github_codespaces", content, re.MULTILINE))
    if not required:
        print(json.dumps({"status": "error", "error": "mandatory github_codespaces policy missing"}))
        return 2

    errors = []
    checked = []
    for task in task_blocks(content):
        if task.get("status") not in GATED_STATUSES:
            continue
        task_id = str(task.get("id"))
        checked.append(task_id)
        exception_ok = task.get("environment_exception_approved") is True and bool(task.get("environment_exception_decision"))
        if exception_ok:
            continue
        missing = []
        if task.get("environment_attested") is not True:
            missing.append("environment_attested=true")
        if task.get("environment_observed") != "github_codespaces":
            missing.append("environment_observed=github_codespaces")
        for key in ("codespace_name", "environment_evidence"):
            if not task.get(key):
                missing.append(key)
        if missing:
            errors.append({"task": task_id, "status": task.get("status"), "missing": missing})

    result = {"status": "fail" if errors else "ok", "checked": checked, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
