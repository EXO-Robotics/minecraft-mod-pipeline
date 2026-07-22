from __future__ import annotations

from typing import Any

from mccompiler.project.store import ProjectStore

from .envelope import OperationError


def write_custom_implementation(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    if expected_revision is None:
        raise OperationError("EXPECTED_REVISION_REQUIRED", "Protected edits require expected_revision")
    relative = parameters.get("path")
    author = parameters.get("author")
    reason = parameters.get("reason")
    if not isinstance(relative, str) or not relative:
        raise OperationError("INVALID_PARAMETERS", "path must be a non-empty project-relative path")
    if not isinstance(author, str) or not isinstance(reason, str):
        raise OperationError("INVALID_PARAMETERS", "author and reason are required")
    if "content" not in parameters:
        raise OperationError("INVALID_PARAMETERS", "content is required")
    revision = store.commit_protected(relative, parameters["content"], expected_revision=expected_revision, author=author, reason=reason)
    return {"path": relative, "revision": revision, "protected": True}, store, [{"path": relative, "kind": "protected_custom_implementation"}]


def _append_decision(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None, *, path: str, key: str, record_key: str) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    record = parameters.get("record")
    provenance = parameters.get("provenance")
    if not isinstance(record, dict) or not isinstance(provenance, dict):
        raise OperationError("INVALID_PARAMETERS", "record and provenance objects are required")
    if not provenance.get("author") or not provenance.get("reason"):
        raise OperationError("INVALID_PROVENANCE", "author and reason are required")
    identifier = record.get(record_key)
    if not isinstance(identifier, str) or not identifier:
        raise OperationError("INVALID_PARAMETERS", f"record.{record_key} is required")
    document = store.read(path, {"schema_version": "1.0.0", key: []})
    rows = list(document.get(key, [])) if isinstance(document, dict) else []
    if any(row.get(record_key) == identifier for row in rows if isinstance(row, dict)):
        raise OperationError("DUPLICATE_RECORD", f"Record already exists: {identifier}")
    rows.append({**record, "provenance": provenance})
    updated = {"schema_version": "1.0.0", key: rows}
    revision = store.commit({path: updated}, expected_revision=expected_revision)
    return {"record": rows[-1], "revision": revision}, store, [{"path": path, "kind": key}]


def add_project_pattern(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _append_decision(store, parameters, expected_revision, path="decisions/custom-patterns.json", key="patterns", record_key="id")


def resolve_mapping(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _append_decision(store, parameters, expected_revision, path="decisions/mappings.json", key="mappings", record_key="source_id")


def register_custom_behavior_handler(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    return _append_decision(store, parameters, expected_revision, path="decisions/custom-handlers.json", key="handlers", record_key="behavior_id")


def add_rights_evidence(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    record = parameters.get("record")
    if not isinstance(record, dict):
        raise OperationError("INVALID_PARAMETERS", "record is required")
    decision = record.get("decision")
    if isinstance(decision, dict) and decision.get("status") == "MARKETPLACE_CLEARED" and decision.get("reviewed_by_type") != "human":
        raise OperationError("HUMAN_REVIEW_REQUIRED", "Only an accountable human may record MARKETPLACE_CLEARED")
    return _append_decision(store, parameters, expected_revision, path="rights/rights-manifest.yaml", key="records", record_key="content_id")


def patch_ir_with_provenance(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    section = parameters.get("section")
    identifier = parameters.get("id")
    patch = parameters.get("patch")
    provenance = parameters.get("provenance")
    allowed = {"content": "content", "behaviors": "behaviors", "state": "state", "presentation": "presentation", "ui-intent": "ui_intent", "networking-intent": "networking_intent"}
    if section not in allowed or not isinstance(identifier, str) or not isinstance(patch, dict) or not isinstance(provenance, dict):
        raise OperationError("INVALID_PARAMETERS", "valid section, id, patch, and provenance are required")
    if not provenance.get("author") or not provenance.get("reason") or not provenance.get("evidence_ids"):
        raise OperationError("INVALID_PROVENANCE", "IR patches require author, reason, and evidence_ids")
    path = f"ir/{section}.json"
    key = allowed[section]
    document = store.read(path, {"schema_version": "1.0.0", key: []})
    rows = list(document.get(key, [])) if isinstance(document, dict) else []
    matches = [index for index, row in enumerate(rows) if isinstance(row, dict) and (row.get("id") == identifier or row.get("identifier") == identifier)]
    if len(matches) != 1:
        raise OperationError("IR_TARGET_NOT_UNIQUE", f"Expected exactly one IR record for {identifier}, found {len(matches)}")
    index = matches[0]
    rows[index] = {**rows[index], **patch, "review": provenance}
    updated = {"schema_version": "1.0.0", key: rows}
    revision = store.commit({path: updated}, expected_revision=expected_revision)
    return {"record": rows[index], "revision": revision}, store, [{"path": path, "kind": "provenance_ir_patch"}]
