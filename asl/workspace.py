"""Workspace helpers for versioned paper projects."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "untitled-paper"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def next_version(project_dir: Path) -> int:
    versions = []
    for child in project_dir.iterdir() if project_dir.exists() else []:
        if child.is_dir() and re.fullmatch(r"v\d+", child.name):
            versions.append(int(child.name[1:]))
    return max(versions, default=0) + 1


def latest_version(project_dir: Path) -> Path | None:
    versions = []
    for child in project_dir.iterdir() if project_dir.exists() else []:
        if child.is_dir() and re.fullmatch(r"v\d+", child.name):
            versions.append((int(child.name[1:]), child))
    if not versions:
        return None
    return sorted(versions)[-1][1]

