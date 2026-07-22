from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


RIGHTS_STATUSES = frozenset({
    "UNKNOWN", "REVIEW_REQUIRED", "PERSONAL_USE_ONLY", "ATTRIBUTION_REQUIRED",
    "PERMISSION_REQUIRED", "MARKETPLACE_CLEARED", "EXCLUDE",
})
BLOCKING_STATUSES = RIGHTS_STATUSES - {"MARKETPLACE_CLEARED"}


def _attributable_human(decision: Mapping[str, Any]) -> bool:
    if decision.get("reviewer_type") != "human":
        return False
    if not all(isinstance(decision.get(key), str) and decision[key].strip() for key in ("reviewed_by", "reviewer_id", "reviewed_at")):
        return False
    try:
        datetime.fromisoformat(str(decision["reviewed_at"]).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def evaluate_marketplace_rights(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Fail-closed Marketplace rights evaluation.

    This validates authorization evidence, not the underlying legal conclusion.
    Only a named, attributable human review may clear an individual record.
    """
    errors: list[str] = []
    records = manifest.get("records")
    if manifest.get("schema_version") != "1.0.0":
        errors.append("Unsupported rights manifest schema_version")
    if not isinstance(records, list) or not records:
        errors.append("Rights manifest requires at least one record")
        records = []

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(records):
        if not isinstance(raw, Mapping):
            errors.append(f"Rights record {index} must be an object")
            continue
        content_id = str(raw.get("content_id") or "").strip()
        raw_decision = raw.get("decision")
        decision: Mapping[str, Any] = raw_decision if isinstance(raw_decision, Mapping) else {}
        status = str(decision.get("status") or "UNKNOWN")
        record_errors: list[str] = []
        if not content_id:
            record_errors.append("missing content_id")
        elif content_id in seen:
            record_errors.append("duplicate content_id")
        seen.add(content_id)
        if status not in RIGHTS_STATUSES:
            record_errors.append(f"invalid status {status}")
        if status == "MARKETPLACE_CLEARED":
            if not _attributable_human(decision):
                record_errors.append("MARKETPLACE_CLEARED requires an attributable human reviewer")
            if not raw.get("evidence"):
                record_errors.append("MARKETPLACE_CLEARED requires rights evidence")
        errors.extend(f"{content_id or f'record[{index}]'}: {message}" for message in record_errors)
        normalized.append({
            "content_id": content_id,
            "content_type": raw.get("content_type"),
            "status": status,
            "blocking": status in BLOCKING_STATUSES or bool(record_errors),
            "reviewed_by": decision.get("reviewed_by") if status == "MARKETPLACE_CLEARED" else None,
            "reviewer_id": decision.get("reviewer_id") if status == "MARKETPLACE_CLEARED" else None,
        })

    blockers = sorted(row["content_id"] for row in normalized if row["blocking"])
    return {
        "schema_version": "1.0.0",
        "marketplace_candidate_allowed": not errors and not blockers,
        "errors": sorted(errors),
        "blocking_content_ids": blockers,
        "records": sorted(normalized, key=lambda row: row["content_id"]),
        "legal_clearance_implied": False,
    }
