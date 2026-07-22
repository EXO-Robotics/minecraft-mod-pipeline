from __future__ import annotations

from enum import StrEnum
from typing import Any, Iterable, Mapping


class PlatformStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


PLATFORMS = ("windows_local", "bds_diagnostic", "realm_windows", "ps4", "ps5", "xbox_one", "xbox_series")
VERIFIED_STATUS_BY_PLATFORM = {
    "windows_local": "LOCAL_WINDOWS_VERIFIED",
    "bds_diagnostic": "BDS_DIAGNOSTIC_VERIFIED",
    "realm_windows": "REALM_WINDOWS_VERIFIED",
    "ps4": "PS4_VERIFIED",
    "ps5": "PS5_VERIFIED",
    "xbox_one": "XBOX_ONE_VERIFIED",
    "xbox_series": "XBOX_SERIES_VERIFIED",
}


def new_platform_statuses() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "platforms": {
            platform: {"status": PlatformStatus.UNVERIFIED.value, "evidence_ids": []}
            for platform in PLATFORMS
        },
        "console_verified": False,
        "verification_statuses": ["MARKETPLACE_TARGETED", "UNVERIFIED"],
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
    physical = ("ps4", "ps5", "xbox_one", "xbox_series")
    result["console_verified"] = all(platforms[name]["status"] == PlatformStatus.PASSED.value for name in physical)
    verified = [VERIFIED_STATUS_BY_PLATFORM[name] for name in PLATFORMS if platforms[name]["status"] == PlatformStatus.PASSED.value]
    result["verification_statuses"] = ["MARKETPLACE_TARGETED", *(verified or ["UNVERIFIED"])]
    return result
