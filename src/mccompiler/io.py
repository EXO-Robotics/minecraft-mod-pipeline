from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def relaxed_json(text: str) -> Any:
    """Parse ordinary JSON and the common JSON-with-comments mod metadata form."""
    text = text.lstrip("\ufeff")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # This is intentionally conservative. It removes line comments only when
        # they occupy a line outside a quoted string, which covers common pack
        # metadata without attempting to be a general JSONC implementation.
        lines = []
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("//"):
                continue
            lines.append(line)
        return json.loads("\n".join(lines))


def read_json(path: Path) -> Any | None:
    try:
        return relaxed_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def version_list(value: Any, default: list[int] | None = None) -> list[int]:
    if isinstance(value, list):
        result: list[int] = []
        for item in value[:3]:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                return default or [0, 1, 0]
        return (result + [0, 0, 0])[:3]
    if isinstance(value, str):
        nums = re.findall(r"\d+", value)
        if nums:
            return (list(map(int, nums[:3])) + [0, 0, 0])[:3]
    return default or [0, 1, 0]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

