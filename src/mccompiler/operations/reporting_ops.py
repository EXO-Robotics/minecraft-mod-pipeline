from __future__ import annotations

from typing import Any

from mccompiler.project.status import blocking_failures, project_status, unresolved_work
from mccompiler.project.store import ProjectStore
from mccompiler.schema import validate_ir as validate_ir_document


def validate_ir(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    document = store.read("analysis/modir.json")
    if not isinstance(document, dict):
        return {"valid": False, "errors": ["Project has not been scanned"], "error_count": 1}, store, []
    errors = validate_ir_document(document)
    return {"valid": not errors, "errors": errors, "error_count": len(errors)}, store, []


def generate_conversion_report(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
    ir = store.read("analysis/modir.json", {}) or {}
    status = project_status(store)
    project = {key: status.get(key) for key in ("name", "target_profile", "revision", "analysis_revision", "state")}
    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "project": project,
        "input": status.get("input"),
        "inventory": {
            "mods": len(ir.get("mods", [])), "content": len(ir.get("content", [])),
            "behaviors": len(ir.get("behaviors", [])), "state": len(ir.get("state", [])),
            "assets": len(ir.get("assets", [])), "ui_intent": len(ir.get("ui_intent", [])),
            "networking_intent": len(ir.get("networking_intent", [])), "unsupported_hooks": len(ir.get("unsupported_hooks", [])),
        },
        "decisions": {
            "strategies": store.read("decisions/strategies.yaml", {"strategies": []}).get("strategies", []),
            "approvals": store.read("decisions/approvals.yaml", {"approvals": []}).get("approvals", []),
            "redesigns": store.read("decisions/redesigns.yaml", {"redesigns": []}).get("redesigns", []),
            "overrides": store.read("decisions/overrides.yaml", {"overrides": []}).get("overrides", []),
        },
        "unresolved_work": unresolved_work(store),
        "blocking_failures": blocking_failures(store),
        "claims": {"marketplace_approval_implied": False, "runtime_verified": False, "console_verified": False},
    }
    project["revision"] = store.revision + 1
    revision = store.commit({"reports/conversion-project-report.json": report}, expected_revision=expected_revision)
    return {"report": report, "revision": revision}, store, [{"path": "reports/conversion-project-report.json", "kind": "report"}]
