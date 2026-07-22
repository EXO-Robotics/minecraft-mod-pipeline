from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .model import CheckClassification, CheckStatus, RuntimeEvidenceError
from .required_checks import required_checks


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise RuntimeEvidenceError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeEvidenceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise RuntimeEvidenceError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class EvidenceExpectation:
    pack_hash: str
    build_hash: str
    runtime_id: str
    world_id: str
    test_id: str
    now: datetime
    max_age_seconds: int = 86400
    profile: str = "MARKETPLACE_ADDON_STABLE"

    def __post_init__(self) -> None:
        for field in ("pack_hash", "build_hash"):
            value = getattr(self, field)
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ValueError(f"{field} must be a lowercase SHA-256 digest")
        for field in ("runtime_id", "world_id", "test_id"):
            if not getattr(self, field):
                raise ValueError(f"{field} cannot be empty")
        if self.now.tzinfo is None:
            raise ValueError("Expectation time must include a timezone")
        if self.max_age_seconds < 0:
            raise ValueError("max_age_seconds cannot be negative")


def validate_runtime_evidence(
    evidence: Mapping[str, Any],
    expectation: EvidenceExpectation,
    *,
    raw_log: bytes | str | None = None,
    required: Mapping[str, CheckClassification | str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if evidence.get("schema_version") != "1.0.0":
        errors.append("unsupported runtime evidence schema")
    for field in ("pack_hash", "build_hash", "runtime_id", "world_id", "test_id"):
        expected = getattr(expectation, field)
        if evidence.get(field) != expected:
            errors.append(f"{field} does not match the expected build or test identity")

    try:
        started = _timestamp(evidence.get("started_at"), "started_at")
        ended = _timestamp(evidence.get("ended_at"), "ended_at")
        now = expectation.now.astimezone(timezone.utc)
        if ended < started:
            errors.append("ended_at precedes started_at")
        if ended > now:
            errors.append("runtime evidence is dated in the future")
        if (now - ended).total_seconds() > expectation.max_age_seconds:
            errors.append("runtime evidence is stale")
    except RuntimeEvidenceError as exc:
        errors.append(str(exc))

    log_hash = evidence.get("log_hash")
    if not isinstance(log_hash, str) or len(log_hash) != 64:
        errors.append("log_hash must be a SHA-256 digest")
    if raw_log is not None:
        payload = raw_log.encode("utf-8") if isinstance(raw_log, str) else raw_log
        if hashlib.sha256(payload).hexdigest() != log_hash:
            errors.append("log_hash does not match the supplied runtime log")

    checks = evidence.get("checks")
    checks = checks if isinstance(checks, list) else []
    if not isinstance(evidence.get("checks"), list):
        errors.append("checks must be an array")
    by_id: dict[str, Mapping[str, Any]] = {}
    for check in checks:
        if not isinstance(check, Mapping) or not isinstance(check.get("check_id"), str):
            errors.append("every check must have a check_id")
            continue
        check_id = str(check["check_id"])
        if check_id in by_id:
            errors.append(f"duplicate check evidence: {check_id}")
        by_id[check_id] = check

    required_map = dict(required or required_checks(expectation.profile))
    classifications: dict[str, str] = {}
    for check_id, expected_classification_value in required_map.items():
        expected_classification = CheckClassification(expected_classification_value)
        check = by_id.get(check_id)
        if check is None:
            errors.append(f"missing required check: {check_id}")
            continue
        classification_value = check.get("classification")
        try:
            actual_classification = CheckClassification(classification_value) if isinstance(classification_value, str) else None
        except (ValueError, TypeError):
            actual_classification = None
        if actual_classification is None:
            errors.append(f"invalid classification for check: {check_id}")
            continue
        classifications[check_id] = actual_classification.value
        if actual_classification != expected_classification:
            errors.append(f"wrong classification for check: {check_id}")
        status_value = check.get("status")
        try:
            status = CheckStatus(status_value) if isinstance(status_value, str) else None
        except (ValueError, TypeError):
            status = None
        if status is None:
            errors.append(f"invalid status for check: {check_id}")
            continue
        if status != CheckStatus.PASSED:
            errors.append(f"required check did not pass: {check_id} ({status.value})")

    return {
        "schema_version": "1.0.0",
        "valid": not errors,
        "errors": errors,
        "required_check_count": len(required_map),
        "observed_required_check_count": len(set(required_map) & set(by_id)),
        "classifications": classifications,
        "marketplace_approval_implied": False,
    }
