from __future__ import annotations

from typing import Any

from .store import ProjectStore


def blocking_failures(store: ProjectStore) -> list[dict[str, Any]]:
    ir = store.read("analysis/modir.json", {}) or {}
    failures = [{"code": "SCAN_ERROR", "message": str(message)} for message in ir.get("errors", [])]
    for diagnostic in ir.get("diagnostics", []):
        if diagnostic.get("severity") == "error":
            failures.append({"code": diagnostic.get("code", "DIAGNOSTIC"), "message": diagnostic.get("message") or diagnostic.get("feature") or "Blocking diagnostic", "diagnostic": diagnostic})
    return failures


def unresolved_work(store: ProjectStore) -> list[dict[str, Any]]:
    ir = store.read("analysis/modir.json", {}) or {}
    strategies = store.read("decisions/strategies.yaml", {"strategies": []}).get("strategies", [])
    decided = {row.get("target") for row in strategies}
    work: list[dict[str, Any]] = []
    for content in ir.get("content", []):
        if content.get("identifier") not in decided:
            work.append({"kind": "content_strategy", "target": content.get("identifier"), "content_kind": content.get("kind"), "reason": "No reconstruction strategy has been selected"})
    for behavior in ir.get("behaviors", []):
        if behavior.get("id") not in decided:
            work.append({"kind": "behavior_strategy", "target": behavior.get("id"), "reason": "No reconstruction strategy has been selected"})
    for hook in ir.get("unsupported_hooks", []):
        target = hook.get("feature") or hook.get("id")
        if target not in decided:
            work.append({"kind": "unsupported_review", "target": target, "reason": hook.get("code", "Unsupported hook requires review")})
    return work


def project_status(store: ProjectStore) -> dict[str, Any]:
    manifest = store.manifest
    scanned = (store.root / "analysis/modir.json").is_file()
    unresolved = unresolved_work(store) if scanned else []
    blocking = blocking_failures(store) if scanned else []
    decisions = {
        "strategies": len(store.read("decisions/strategies.yaml", {"strategies": []}).get("strategies", [])),
        "approvals": len(store.read("decisions/approvals.yaml", {"approvals": []}).get("approvals", [])),
        "redesigns": len(store.read("decisions/redesigns.yaml", {"redesigns": []}).get("redesigns", [])),
        "overrides": len(store.read("decisions/overrides.yaml", {"overrides": []}).get("overrides", [])),
    }
    return {
        "name": manifest.get("name"), "target_profile": manifest.get("target_profile"),
        "revision": store.revision, "analysis_revision": manifest.get("analysis_revision", 0),
        "scanned": scanned, "input": manifest.get("input"),
        "unresolved_count": len(unresolved), "blocking_count": len(blocking),
        "decision_counts": decisions,
        "state": "blocked" if blocking else "needs_scan" if not scanned else "needs_decisions" if unresolved else "ready",
    }


def next_task(store: ProjectStore) -> dict[str, Any] | None:
    status = project_status(store)
    if not status["scanned"]:
        return {"operation": "scan_mod", "reason": "Project has not been scanned"}
    failures = blocking_failures(store)
    if failures:
        return {"operation": "list_blocking_failures", "reason": "Resolve blocking analysis failures", "failure": failures[0]}
    unresolved = unresolved_work(store)
    if unresolved:
        item = unresolved[0]
        operation = "inspect_behavior" if item["kind"] == "behavior_strategy" else "show_evidence"
        return {"operation": operation, "parameters": {"id": item["target"]}, "reason": item["reason"]}
    return {"operation": "get_project_status", "reason": "No unresolved milestone work remains"}
