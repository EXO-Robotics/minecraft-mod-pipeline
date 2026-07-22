from __future__ import annotations

from enum import StrEnum
from typing import Any, Iterable, Mapping


class PlatformStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


PLATFORMS = ("windows_local", "realm_windows", "playstation", "xbox")


def new_platform_statuses() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "platforms": {
            platform: {"status": PlatformStatus.UNVERIFIED.value, "evidence_ids": []}
            for platform in PLATFORMS
        },
        "console_verified": False,
        "marketplace_approval_implied": False,
    }


def evaluate_platform_statuses(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    result = new_platform_statuses()
    platforms: dict[str, dict[str, Any]] = result["platforms"]
    errors: list[str] = []
    seen: set[str] = set()
    for record in records:
        platform = record.get("platform")
        if platform not in PLATFORMS:
            errors.append(f"unknown platform: {platform}")
            continue
        if platform in seen:
            errors.append(f"duplicate platform record: {platform}")
            continue
        seen.add(str(platform))
        status_value = record.get("status")
        try:
            status = PlatformStatus(status_value) if isinstance(status_value, str) else None
        except (ValueError, TypeError):
            status = None
        if status is None:
            errors.append(f"invalid platform status: {platform}")
            continue
        evidence_ids = record.get("evidence_ids", [])
        if not isinstance(evidence_ids, list) or not all(isinstance(item, str) and item for item in evidence_ids):
            errors.append(f"invalid evidence IDs for platform: {platform}")
            continue
        if status in {PlatformStatus.PASSED, PlatformStatus.FAILED} and not evidence_ids:
            errors.append(f"{status.value} platform status requires evidence: {platform}")
            continue
        platforms[str(platform)] = {"status": status.value, "evidence_ids": sorted(set(evidence_ids))}
    result["errors"] = errors
    result["valid"] = not errors
    result["console_verified"] = (
        platforms["playstation"]["status"] == PlatformStatus.PASSED.value
        and platforms["xbox"]["status"] == PlatformStatus.PASSED.value
    )
    return result
