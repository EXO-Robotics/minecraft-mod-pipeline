from __future__ import annotations

from typing import Any

from .io import read_json
from pathlib import Path
from .patterns import match_patterns


CLASSES = ("DIRECT", "SCRIPTED_EQUIVALENT", "RECONSTRUCTED", "BEHAVIORAL_APPROXIMATION", "VISUAL_APPROXIMATION", "MANUAL_REDESIGN", "UNSUPPORTED")


def _database() -> dict[str, Any]:
    database = read_json(Path(__file__).with_name("capabilities.json")) or {"capabilities": {}}
    for identifier, capability in database.get("capabilities", {}).items():
        capability.setdefault("capability_id", identifier)
        capability.setdefault("bedrock_version", database.get("bedrock_version"))
        capability.setdefault("status", "stable" if capability.get("stable") else "experimental")
        capability.setdefault("approximation_strategies", [])
        capability.setdefault("required_modules", capability.get("modules", []))
        capability.setdefault("performance_implications", capability.get("performance", "unknown"))
        capability.setdefault("multiplayer_safety", capability.get("multiplayer_safe", False))
        capability.setdefault("persistence_support", capability.get("persistent", False))
        capability.setdefault("known_limitations", capability.get("limitations", []))
        capability.setdefault("reference_implementation", capability.get("reference"))
        capability.setdefault("deprecation", None)
    return database


def _scores(classification: str, confidence: float, capability: dict[str, Any]) -> dict[str, Any]:
    base = {"DIRECT": .98, "SCRIPTED_EQUIVALENT": .9, "RECONSTRUCTED": .78, "BEHAVIORAL_APPROXIMATION": .62, "VISUAL_APPROXIMATION": .48, "MANUAL_REDESIGN": .25, "UNSUPPORTED": 0}[classification]
    return {
        "extraction_confidence": round(confidence, 3), "technical_similarity": base,
        "gameplay_fidelity": min(1.0, base + (.08 if classification in {"SCRIPTED_EQUIVALENT", "BEHAVIORAL_APPROXIMATION"} else 0)),
        "visual_fidelity": 1.0 if classification == "DIRECT" else (.65 if classification != "UNSUPPORTED" else 0),
        "persistence_fidelity": base if capability.get("persistent") else min(base, .65),
        "multiplayer_fidelity": base if capability.get("multiplayer_safe") else 0,
        "performance_risk": {"low": .1, "medium": .4, "high": .75, "unknown": 1.0}.get(str(capability.get("performance")), .5),
        "human_review_required": classification not in {"DIRECT", "SCRIPTED_EQUIVALENT"} or confidence < .9,
    }


def plan_conversion(ir: dict[str, Any]) -> dict[str, Any]:
    db = _database()
    capabilities = db["capabilities"]
    features: list[dict[str, Any]] = []
    overrides = {o.get("target"): o for o in ir.get("applied_overrides", [])}
    conflicted = {d.get("feature") for d in ir.get("diagnostics", []) if d.get("code") == "identifier_conflict"}
    for content in ir.get("content", []):
        key = f"content.{content.get('kind')}"
        cap = capabilities.get(key, {})
        classification = cap.get("classification", "MANUAL_REDESIGN")
        if content.get("identifier") in conflicted:
            classification = "MANUAL_REDESIGN"
        override = overrides.get(content.get("identifier"))
        if override and override.get("strategy"): classification = override["strategy"]
        if any(f["id"] == content.get("identifier") and f["kind"] == key for f in features):
            continue
        features.append({"id": content.get("identifier"), "kind": key, "classification": classification, "scores": _scores(classification, 1.0, cap), "capability": cap, "evidence": content.get("evidence", []), "override": override, "diagnostic": "identifier_conflict" if content.get("identifier") in conflicted else None})
    for behavior in ir.get("behaviors", []):
        key = f"behavior.{behavior.get('trigger', {}).get('type')}"
        cap = capabilities.get(key, {})
        classification = cap.get("classification", "MANUAL_REDESIGN")
        if behavior.get("diagnostics"): classification = "UNSUPPORTED"
        override = overrides.get(behavior.get("id"))
        if override and override.get("strategy"): classification = override["strategy"]
        features.append({"id": behavior.get("id"), "kind": key, "classification": classification, "scores": _scores(classification, behavior.get("confidence", 0), cap), "capability": cap, "evidence": behavior.get("evidence", []), "fingerprint": behavior.get("fingerprint"), "override": override})
    for ui in ir.get("ui_intent", []):
        cap = capabilities.get("ui.form", {})
        features.append({"id": ui.get("id"), "kind": "ui.form", "classification": cap["classification"], "scores": _scores(cap["classification"], 1, cap), "capability": cap, "evidence": ui.get("evidence", [])})
    for intent in ir.get("networking_intent", []):
        cap = capabilities["networking.intent"]
        features.append({"id": intent.get("id"), "kind": "networking.intent", "classification": cap["classification"], "scores": _scores(cap["classification"], 1, cap), "capability": cap, "evidence": intent.get("evidence", []), "replacement_strategy": intent.get("replacement_strategy")})
    for diagnostic in ir.get("unsupported_hooks", []):
        cap = capabilities["unsupported.mixin"]
        features.append({"id": diagnostic.get("feature"), "kind": "unsupported.mixin", "classification": "UNSUPPORTED", "scores": _scores("UNSUPPORTED", 1, cap), "capability": cap, "evidence": diagnostic.get("evidence", [])})
    counts = {name: sum(1 for f in features if f["classification"] == name) for name in CLASSES}
    numeric = [f["scores"] for f in features]
    summary = {key: round(sum(x[key] for x in numeric) / len(numeric), 3) if numeric else 0 for key in ("extraction_confidence", "technical_similarity", "gameplay_fidelity", "visual_fidelity", "persistence_fidelity", "multiplayer_fidelity", "performance_risk")}
    return {"schema_version": "1.0.0", "capability_database_version": db.get("schema_version"), "target": ir.get("target"), "features": features, "patterns": match_patterns(ir), "strategy_counts": counts, "scores": summary, "constraints": ["Every downgrade is explicit.", "Runtime validation determines completion; static validity alone is insufficient."]}
