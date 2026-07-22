from __future__ import annotations

from typing import Any

from mccompiler.overrides import ALLOWED_STRATEGIES
from mccompiler.project.store import ProjectError, ProjectStore


def set_strategy(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    target, strategy, provenance = parameters.get("target"), parameters.get("strategy"), parameters.get("provenance")
    if not isinstance(target, str) or not target:
        raise ProjectError("INVALID_PARAMETERS", "set_strategy requires target")
    if strategy not in ALLOWED_STRATEGIES:
        raise ProjectError("INVALID_STRATEGY", f"Unsupported strategy: {strategy}")
    if not isinstance(provenance, dict) or not provenance.get("author") or not provenance.get("reason"):
        raise ProjectError("INVALID_PROVENANCE", "set_strategy requires provenance.author and provenance.reason")
    behaviors = store.read("ir/behaviors.json", {"behaviors": []}).get("behaviors", [])
    content = store.read("ir/content.json", {"content": []}).get("content", [])
    unsupported = (store.read("analysis/modir.json", {}) or {}).get("unsupported_hooks", [])
    known = {row.get("id") for row in behaviors} | {row.get("identifier") for row in content} | {row.get("feature") or row.get("id") for row in unsupported}
    if target not in known:
        raise ProjectError("TARGET_NOT_FOUND", f"Strategy target not found: {target}")
    document = store.read("decisions/strategies.yaml", {"schema_version": "1.0.0", "strategies": []})
    decision = {"target": target, "strategy": strategy, "provenance": dict(provenance)}
    if parameters.get("recorded_at"):
        decision["recorded_at"] = parameters["recorded_at"]
    rows = [row for row in document.get("strategies", []) if row.get("target") != target]
    rows.append(decision)
    document["strategies"] = sorted(rows, key=lambda row: str(row.get("target")))
    revision = store.commit({"decisions/strategies.yaml": document}, expected_revision=expected_revision)
    return {"decision": decision, "revision": revision}, store, [{"path": "decisions/strategies.yaml", "kind": "decision"}]
