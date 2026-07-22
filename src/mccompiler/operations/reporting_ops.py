from __future__ import annotations

import html
import json
from typing import Any

from mccompiler.console_evidence import evaluate_platform_statuses
from mccompiler.project.status import blocking_failures, project_status, unresolved_work
from mccompiler.project.store import ProjectStore
from mccompiler.rights import evaluate_marketplace_rights
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
    rights_manifest = store.read("rights/rights-manifest.yaml", {"schema_version": "1.0.0", "records": []})
    if isinstance(rights_manifest, dict) and "records" not in rights_manifest:
        rights_manifest = {**rights_manifest, "records": rights_manifest.get("content", [])}
    rights_report = evaluate_marketplace_rights(rights_manifest if isinstance(rights_manifest, dict) else {})
    fidelity = store.read("reports/fidelity.json", {"schema_version": "1.0.0", "mechanics": [], "status": "NOT_EVALUATED"})
    performance = store.read("reports/performance-report.json", {"schema_version": "1.0.0", "status": "NOT_EVALUATED", "runtime_measurements": []})
    validation = store.read("reports/validation-report.json", {"schema_version": "1.0.0", "status": "NOT_EVALUATED", "checks": []})
    platform_records = store.read("console/platform-evidence.json", {"records": []})
    records = platform_records.get("records", []) if isinstance(platform_records, dict) else []
    console = evaluate_platform_statuses(records if isinstance(records, list) else [])
    provenance = {
        "schema_version": "1.0.0",
        "input": status.get("input"),
        "analysis_revision": status.get("analysis_revision"),
        "project_revision": store.revision + 1,
        "source_evidence_preserved_in_consumer_archive": False,
    }
    report["gates"] = {
        "rights": rights_report["marketplace_candidate_allowed"],
        "runtime": False,
        "console": console["console_verified"],
        "marketplace_approval_implied": False,
    }
    documents = {
        "reports/conversion-project-report.json": report,
        "dist/reports/conversion-report.json": report,
        "dist/reports/provenance.json": provenance,
        "dist/reports/fidelity.json": fidelity,
        "dist/reports/rights-report.json": rights_report,
        "dist/reports/validation-report.json": validation,
        "dist/reports/performance-report.json": performance,
        "dist/reports/console-evidence.json": console,
    }
    revision = store.commit(documents, expected_revision=expected_revision)
    rendered = html.escape(json.dumps(report, indent=2, sort_keys=True))
    store.write_text("dist/reports/conversion-report.html", f"<!doctype html><html><head><meta charset=\"utf-8\"><title>Conversion report</title></head><body><h1>Conversion report</h1><pre>{rendered}</pre></body></html>\n")
    artifacts = [{"path": path, "kind": "report"} for path in documents]
    artifacts.append({"path": "dist/reports/conversion-report.html", "kind": "report"})
    return {"report": report, "revision": revision, "reports": sorted(path for path in documents if path.startswith("dist/reports/")) + ["dist/reports/conversion-report.html"]}, store, artifacts
