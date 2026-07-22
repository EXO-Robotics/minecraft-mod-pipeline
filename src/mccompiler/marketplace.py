from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .performance import audit_archive_performance
from .quality import validate_quality_record
from .rights import evaluate_marketplace_rights
from .validate import validate_output


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_marketplace_candidate(
    build_root: str | Path,
    *,
    plan: Mapping[str, Any],
    rights_manifest: Mapping[str, Any],
    quality_records: Sequence[dict[str, Any]],
    creator_tools_report: Mapping[str, Any] | None,
    performance_exceptions: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(build_root).resolve()
    archive = root / "converted-mod.mcaddon"
    static = validate_output(root, dict(plan), marketplace=True)
    rights = evaluate_marketplace_rights(rights_manifest)
    performance = audit_archive_performance(archive, approved_exceptions=performance_exceptions)

    quality_errors: list[str] = []
    quality_ids: set[str] = set()
    for record in quality_records:
        quality_errors.extend(validate_quality_record(record))
        if record.get("feature_id"):
            quality_ids.add(str(record["feature_id"]))
    planned_ids = {str(row.get("id")) for row in plan.get("features", []) if row.get("id")}
    missing_quality = sorted(planned_ids - quality_ids)
    if missing_quality:
        quality_errors.append("Missing quality records: " + ", ".join(missing_quality))

    creator_errors: list[str] = []
    creator = dict(creator_tools_report or {})
    raw_creator_body = creator.get("creator_tools")
    creator_body: Mapping[str, Any] = raw_creator_body if isinstance(raw_creator_body, Mapping) else {}
    if not creator:
        creator_errors.append("Official Minecraft Creator Tools evidence is missing")
    else:
        if not creator.get("passed"):
            creator_errors.append("Official Minecraft Creator Tools validation did not pass")
        if creator_body.get("marketplace_approval_implied") is not False:
            creator_errors.append("Creator Tools report must explicitly state marketplace_approval_implied=false")
        required = {"addon", "currentplatform"}
        if not required <= set(map(str, creator_body.get("suites", []))):
            creator_errors.append("Creator Tools report is missing required suites")
        if int(creator_body.get("errors", 1)) != 0:
            creator_errors.append("Creator Tools report contains errors")

    blockers = {
        "static": list(static.get("errors", [])),
        "rights": list(rights.get("errors", [])) + [f"Uncleared content: {item}" for item in rights.get("blocking_content_ids", [])],
        "quality": sorted(quality_errors),
        "performance": list(performance.get("errors", [])),
        "creator_tools": creator_errors,
    }
    passed = all(not rows for rows in blockers.values())
    artifacts = []
    if archive.is_file():
        artifacts.append({"path": str(archive), "sha256": _sha256(archive), "bytes": archive.stat().st_size})
    return {
        "schema_version": "1.0.0",
        "status": "MARKETPLACE_CANDIDATE" if passed else "VALID_MCADDON_NOT_MARKETPLACE_CANDIDATE",
        "passed": passed,
        "marketplace_approval_implied": False,
        "blockers": blockers,
        "static_validation": static,
        "rights": rights,
        "quality": {"feature_ids": sorted(quality_ids), "missing_feature_ids": missing_quality, "errors": sorted(quality_errors)},
        "performance": performance,
        "creator_tools": creator,
        "artifacts": artifacts,
    }


def write_candidate_report(path: str | Path, report: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
