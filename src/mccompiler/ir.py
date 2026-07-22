from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceUnit:
    path: str
    kind: str
    sha256: str | None = None
    entries: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def empty_ir(input_path: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "tool": {"name": "minecraft-compiler-baseline", "version": "0.1.0"},
        "input": {"path": input_path},
        "target": None,
        "modpack": None,
        "mods": [],
        "dependency_graph": {"nodes": [], "edges": []},
        "aggregate": {
            "content_counts": {},
            "asset_counts": {},
            "risk_flags": [],
            "source_signals": {},
        },
        "evidence_policy": "Every extracted fact should retain a relative source path.",
    }

