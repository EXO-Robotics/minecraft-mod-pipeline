from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import read_json


def _capabilities() -> dict[str, Any]:
    return read_json(Path(__file__).with_name("capabilities.json")) or {"capabilities": {}}


def _patterns() -> list[dict[str, Any]]:
    return read_json(Path(__file__).with_name("patterns.json")) or []


def _feature_plan(kind: str, count: int, capabilities: dict[str, Any], evidence: list[str] | None = None) -> dict[str, Any]:
    cap = capabilities.get(kind) or capabilities.get("manifest") or {"strategy": "manual", "technical": 0.1, "gameplay": 0.2}
    return {"feature": kind, "count": count, "strategy": cap["strategy"], "technical_fidelity": cap["technical"], "gameplay_fidelity": cap["gameplay"], "evidence": evidence or [], "status": "scaffolded" if cap["strategy"] != "unsupported" else "unsupported"}


def plan_conversion(ir: dict[str, Any]) -> dict[str, Any]:
    capabilities = _capabilities().get("capabilities", {})
    aggregate = ir.get("aggregate", {})
    counts = aggregate.get("content_counts", {})
    signals = aggregate.get("source_signals", {})
    flags = set(aggregate.get("risk_flags", []))
    features: list[dict[str, Any]] = []
    for kind, count in sorted(counts.items()):
        if count:
            features.append(_feature_plan(kind, count, capabilities))
    for signal, kind in (("item_interactions", "item_use"), ("damage_hooks", "entity_hit"), ("tick_hooks", "server_tick"), ("network_hooks", "network_packets"), ("mixin_injections", "mixins"), ("ui_hooks", "custom_gui"), ("tile_entities", "tile_entities")):
        if signals.get(signal):
            features.append(_feature_plan(kind, signals[signal], capabilities, [f"aggregate.source_signals.{signal}"]))
    if "client_rendering" in flags and not any(f["feature"] == "models" for f in features):
        features.append(_feature_plan("client_rendering", 1, capabilities, ["aggregate.risk_flags.client_rendering"]))
    patterns = []
    available = {name for name, value in signals.items() if value} | {name for name, value in counts.items() if value} | flags
    for pattern in _patterns():
        matched = sorted(set(pattern.get("when", [])) & available)
        if matched:
            patterns.append({"id": pattern["id"], "description": pattern["description"], "strategy": pattern["strategy"], "matched_signals": matched})
    if not features:
        features.append({"feature": "unknown_behavior", "count": 1, "strategy": "manual", "technical_fidelity": 0.1, "gameplay_fidelity": 0.2, "evidence": ["No recognized content or source signals"], "status": "needs_review"})
    technical = sum(f["technical_fidelity"] * f["count"] for f in features) / sum(f["count"] for f in features)
    gameplay = sum(f["gameplay_fidelity"] * f["count"] for f in features) / sum(f["count"] for f in features)
    strategy_counts: dict[str, int] = {}
    for feature in features:
        strategy_counts[feature["strategy"]] = strategy_counts.get(feature["strategy"], 0) + feature["count"]
    return {
        "schema_version": "0.1.0",
        "target": ir.get("target"),
        "features": features,
        "patterns": patterns,
        "strategy_counts": strategy_counts,
        "scores": {"technical_fidelity": round(technical, 3), "gameplay_fidelity": round(gameplay, 3), "confidence": "inventory-level"},
        "constraints": [
            "Path inventory is not proof of runtime behavior.",
            "Custom GUI, mixins, packets, and custom rendering require intent review.",
            "Generated output is a scaffold until Bedrock runtime tests pass.",
        ],
    }
