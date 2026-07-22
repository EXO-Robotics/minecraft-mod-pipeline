from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mccompiler.project.store import ProjectError, ProjectStore
from mccompiler.scan import scan_path


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _evidence_index(ir: dict[str, Any]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    collections = [ir.get("content", []), ir.get("behaviors", []), ir.get("state", []), ir.get("registries", []), ir.get("diagnostics", []), ir.get("unsupported_hooks", [])]
    for collection in collections:
        for owner in collection:
            for evidence in owner.get("evidence", []):
                identifier = f"evidence:{_digest(evidence)[:24]}"
                records.setdefault(identifier, {"id": identifier, **evidence})
    for mod in ir.get("mods", []):
        for evidence in mod.get("metadata_evidence", []):
            row = evidence if isinstance(evidence, dict) else {"resource_path": str(evidence), "source_mode": "metadata"}
            identifier = f"evidence:{_digest(row)[:24]}"
            records.setdefault(identifier, {"id": identifier, **row})
    return [records[key] for key in sorted(records)]


def _scan_documents(ir: dict[str, Any]) -> dict[str, Any]:
    evidence = _evidence_index(ir)
    source_files = sorted({str(row.get("source_file")) for row in evidence if row.get("source_file")})
    return {
        "analysis/modir.json": ir,
        "analysis/inventory.json": {"schema_version": "1.0.0", "mods": ir.get("mods", []), "content": ir.get("content", []), "assets": ir.get("assets", []), "aggregate": ir.get("aggregate", {})},
        "analysis/dependency-graph.json": {"schema_version": "1.0.0", **ir.get("dependency_graph", {"nodes": [], "edges": []})},
        "analysis/registrations.json": {"schema_version": "1.0.0", "registrations": ir.get("registries", [])},
        "analysis/evidence/index.json": {"schema_version": "1.0.0", "evidence": evidence},
        "analysis/diagnostics/index.json": {"schema_version": "1.0.0", "diagnostics": ir.get("diagnostics", [])},
        "analysis/source-index/files.json": {"schema_version": "1.0.0", "files": [{"path": path} for path in source_files]},
        "ir/content.json": {"schema_version": "1.0.0", "content": ir.get("content", [])},
        "ir/behaviors.json": {"schema_version": "1.0.0", "behaviors": ir.get("behaviors", [])},
        "ir/state.json": {"schema_version": "1.0.0", "state": ir.get("state", [])},
        "ir/presentation.json": {"schema_version": "1.0.0", "presentation": ir.get("presentation_requirements", [])},
        "ir/ui-intent.json": {"schema_version": "1.0.0", "ui_intent": ir.get("ui_intent", [])},
        "ir/networking-intent.json": {"schema_version": "1.0.0", "networking_intent": ir.get("networking_intent", [])},
    }


def scan_mod(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    input_path = parameters.get("input")
    if not isinstance(input_path, str) or not input_path.strip():
        raise ProjectError("INVALID_PARAMETERS", "scan_mod requires a non-empty input path")
    resolved = Path(input_path).expanduser().resolve()
    ir = scan_path(resolved, parameters.get("bedrock_server"))
    documents = _scan_documents(ir)
    revision = store.commit(documents, expected_revision=expected_revision, manifest_updates={"input": {"path": str(resolved), "sha256": ir.get("input", {}).get("sha256"), "kind": ir.get("input", {}).get("kind")}, "analysis_revision": store.revision + 1})
    result = {"revision": revision, "input": ir.get("input"), "mod_count": len(ir.get("mods", [])), "content_count": len(ir.get("content", [])), "behavior_count": len(ir.get("behaviors", [])), "diagnostic_count": len(ir.get("diagnostics", [])), "errors": ir.get("errors", [])}
    artifacts = [{"path": path, "kind": "analysis" if path.startswith("analysis/") else "ir"} for path in sorted(documents)]
    return result, store, artifacts


def list_mods(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    inventory = store.read("analysis/inventory.json", {"mods": []})
    return {"mods": inventory.get("mods", [])}, store, []


def list_content(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    rows = store.read("ir/content.json", {"content": []}).get("content", [])
    if parameters.get("kind"):
        rows = [row for row in rows if row.get("kind") == parameters["kind"]]
    return {"content": rows}, store, []


def _require_identifier(parameters: dict[str, Any], operation: str) -> str:
    identifier = parameters.get("id") or parameters.get("identifier")
    if not isinstance(identifier, str) or not identifier:
        raise ProjectError("INVALID_PARAMETERS", f"{operation} requires id")
    return identifier


def _inspect_rows(store: ProjectStore, parameters: dict[str, Any], *, operation: str, path: str, field: str, kind: str | None = None, keys: tuple[str, ...] = ("id", "identifier")) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    identifier = _require_identifier(parameters, operation)
    rows = store.read(path, {field: []}).get(field, [])
    matches = [row for row in rows if (kind is None or row.get("kind") == kind) and any(row.get(key) == identifier for key in keys)]
    if not matches:
        label = kind or field.rstrip("_")
        raise ProjectError(f"{label.upper()}_NOT_FOUND", f"{label.replace('_', ' ').title()} not found: {identifier}")
    return {field: matches}, store, []


def inspect_mod(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _inspect_rows(store, parameters, operation="inspect_mod", path="analysis/inventory.json", field="mods")


def inspect_content(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None, *, kind: str | None = None, operation: str = "inspect_content") -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _inspect_rows(store, parameters, operation=operation, path="ir/content.json", field="content", kind=kind)


def inspect_item(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return inspect_content(store, parameters, kind="item", operation="inspect_item")


def inspect_block(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return inspect_content(store, parameters, kind="block", operation="inspect_block")


def inspect_entity(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return inspect_content(store, parameters, kind="entity", operation="inspect_entity")


def inspect_recipe(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return inspect_content(store, parameters, kind="recipe", operation="inspect_recipe")


def inspect_structure(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return inspect_content(store, parameters, kind="structure", operation="inspect_structure")


def inspect_state(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _inspect_rows(store, parameters, operation="inspect_state", path="ir/state.json", field="state")


def inspect_asset(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    identifier = parameters.get("id") or parameters.get("identifier") or parameters.get("kind")
    if not isinstance(identifier, str) or not identifier:
        raise ProjectError("INVALID_PARAMETERS", "inspect_asset requires id or kind")
    assets = store.read("analysis/inventory.json", {"assets": []}).get("assets", [])
    matches = [row for row in assets if identifier in {row.get("id"), row.get("identifier"), row.get("kind")}]
    if not matches:
        raise ProjectError("ASSET_NOT_FOUND", f"Asset not found: {identifier}")
    return {"assets": matches}, store, []


def _inspect_intent(store: ProjectStore, parameters: dict[str, Any], *, operation: str, path: str, field: str) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    if parameters.get("id") or parameters.get("identifier"):
        return _inspect_rows(store, parameters, operation=operation, path=path, field=field)
    return {field: store.read(path, {field: []}).get(field, [])}, store, []


def inspect_gui(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _inspect_intent(store, parameters, operation="inspect_gui", path="ir/ui-intent.json", field="ui_intent")


def inspect_packet(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _inspect_intent(store, parameters, operation="inspect_packet", path="ir/networking-intent.json", field="networking_intent")


def inspect_worldgen(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    rows = (store.read("analysis/modir.json", {}) or {}).get("world_requirements", [])
    if parameters.get("id"):
        rows = [row for row in rows if row.get("id") == parameters["id"]]
        if not rows:
            raise ProjectError("WORLDGEN_NOT_FOUND", f"Worldgen requirement not found: {parameters['id']}")
    return {"world_requirements": rows}, store, []


def list_unsupported_operations(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    hooks = (store.read("analysis/modir.json", {}) or {}).get("unsupported_hooks", [])
    return {"unsupported_operations": hooks, "count": len(hooks)}, store, []


def _ambiguous(ir: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for behavior in ir.get("behaviors", []):
        diagnostics = behavior.get("diagnostics", [])
        confidence = behavior.get("confidence", 1.0)
        if confidence < 1.0 or diagnostics:
            rows.append({"id": behavior.get("id"), "confidence": confidence, "diagnostics": diagnostics, "reason": "confidence_below_one" if confidence < 1.0 else "behavior_diagnostics"})
    return sorted(rows, key=lambda row: str(row.get("id")))


def list_ambiguous_behaviors(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    rows = _ambiguous(store.read("analysis/modir.json", {}) or {})
    return {"ambiguous_behaviors": rows, "count": len(rows)}, store, []


def trace_dependency(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    identifier = _require_identifier(parameters, "trace_dependency")
    graph = store.read("analysis/dependency-graph.json", {"nodes": [], "edges": []})
    direction = parameters.get("direction", "both")
    if direction not in {"incoming", "outgoing", "both"}:
        raise ProjectError("INVALID_PARAMETERS", "direction must be incoming, outgoing, or both")
    nodes = [row for row in graph.get("nodes", []) if row.get("id") == identifier]
    incoming = [edge for edge in graph.get("edges", []) if edge.get("to") == identifier] if direction in {"incoming", "both"} else []
    outgoing = [edge for edge in graph.get("edges", []) if edge.get("from") == identifier] if direction in {"outgoing", "both"} else []
    if not nodes and not incoming and not outgoing:
        raise ProjectError("DEPENDENCY_NOT_FOUND", f"Dependency not found: {identifier}")
    return {"id": identifier, "nodes": nodes, "incoming": incoming, "outgoing": outgoing}, store, []


def inspect_unsupported(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None, *, prefix: str | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    hooks = (store.read("analysis/modir.json", {}) or {}).get("unsupported_hooks", [])
    identifier = parameters.get("id") or parameters.get("feature")
    if identifier:
        hooks = [row for row in hooks if identifier in {row.get("id"), row.get("feature")}]
    if prefix:
        hooks = [row for row in hooks if prefix in str(row.get("feature", "")).lower() or prefix in str(row.get("code", "")).lower()]
    if not hooks:
        raise ProjectError("UNSUPPORTED_HOOK_NOT_FOUND", f"Unsupported hook not found: {identifier or prefix}")
    return {"unsupported_hooks": hooks}, store, []


def inspect_mixin(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return inspect_unsupported(store, parameters, prefix="mixin")


def inspect_coremod(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return inspect_unsupported(store, parameters, prefix="coremod")


def inspect_behavior(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    identifier = parameters.get("id")
    rows = store.read("ir/behaviors.json", {"behaviors": []}).get("behaviors", [])
    matches = [row for row in rows if row.get("id") == identifier]
    if not matches:
        raise ProjectError("BEHAVIOR_NOT_FOUND", f"Behavior not found: {identifier}")
    evidence_index = store.read("analysis/evidence/index.json", {"evidence": []}).get("evidence", [])
    ids_by_digest = {_digest({k: v for k, v in row.items() if k != "id"}): row["id"] for row in evidence_index}
    behavior = matches[0]
    evidence_ids = [ids_by_digest.get(_digest(row)) for row in behavior.get("evidence", [])]
    return {"behavior": behavior, "evidence_ids": [value for value in evidence_ids if value]}, store, []


def show_evidence(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    identifier = parameters.get("id")
    evidence = store.read("analysis/evidence/index.json", {"evidence": []}).get("evidence", [])
    direct = [row for row in evidence if row.get("id") == identifier]
    if direct:
        return {"evidence": direct}, store, []
    ir = store.read("analysis/modir.json", {}) or {}
    owners = list(ir.get("behaviors", [])) + list(ir.get("content", [])) + list(ir.get("unsupported_hooks", []))
    matching = [row for row in owners if row.get("id") == identifier or row.get("identifier") == identifier or row.get("feature") == identifier]
    if not matching:
        raise ProjectError("EVIDENCE_NOT_FOUND", f"Evidence or owner not found: {identifier}")
    wanted = {_digest(row) for owner in matching for row in owner.get("evidence", [])}
    return {"evidence": [row for row in evidence if _digest({k: v for k, v in row.items() if k != "id"}) in wanted]}, store, []
