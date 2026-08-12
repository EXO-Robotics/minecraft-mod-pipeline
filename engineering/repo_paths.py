#!/usr/bin/env python3
"""Resolve the product repository and external Bedrock authority root.

Engineering evidence is intentionally runnable from detached Git worktrees.
Such worktrees do not retain ``bedrock-server`` in their lexical path, so
ancestor-name checks are insufficient.  The linked-worktree gitdir still
points at the primary checkout; use that pointer without consulting or
mutating product state.
"""

from __future__ import annotations

import os
from pathlib import Path


def find_repo(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "behavior_pack").is_dir() and (candidate / "engineering").is_dir():
            return candidate
    raise FileNotFoundError(f"Aionbound product repository not found from {start}")


def _gitdir(repo: Path) -> Path | None:
    dotgit = repo / ".git"
    if dotgit.is_dir():
        return dotgit.resolve()
    if dotgit.is_file():
        marker = dotgit.read_text(encoding="utf-8").strip()
        if marker.startswith("gitdir:"):
            raw = Path(marker.split(":", 1)[1].strip())
            return (repo / raw).resolve() if not raw.is_absolute() else raw.resolve()
    return None


def find_bedrock_root(repo: Path) -> Path:
    override = os.environ.get("AIONBOUND_BEDROCK_ROOT")
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override).expanduser().resolve())
    candidates.extend((repo.resolve(), *repo.resolve().parents))
    gitdir = _gitdir(repo)
    if gitdir is not None:
        candidates.extend((gitdir, *gitdir.parents))
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "program/crazycraft-pack-production-v1").is_dir():
            return candidate
    raise FileNotFoundError(
        "bedrock-server authority root not found; set AIONBOUND_BEDROCK_ROOT "
        "when running outside a linked Git worktree"
    )
