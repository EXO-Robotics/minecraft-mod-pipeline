from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TargetProfile:
    identifier: str
    production: bool
    scripts: bool
    stable_scripts_only: bool
    external_services: bool
    bds_only_modules: bool
    experiments: bool
    debug_content: bool


PROFILES: dict[str, TargetProfile] = {
    "MARKETPLACE_ADDON_STABLE": TargetProfile(
        "MARKETPLACE_ADDON_STABLE", True, True, True, False, False, False, False
    ),
    "LOCAL_WINDOWS_DEVELOPMENT": TargetProfile(
        "LOCAL_WINDOWS_DEVELOPMENT", False, True, False, False, False, True, True
    ),
    "REALM_CONSOLE_BENCHMARK": TargetProfile(
        "REALM_CONSOLE_BENCHMARK", False, True, True, False, False, False, False
    ),
    "DATA_ONLY_FALLBACK": TargetProfile(
        "DATA_ONLY_FALLBACK", False, False, True, False, False, False, False
    ),
    "BDS_DIAGNOSTIC": TargetProfile(
        "BDS_DIAGNOSTIC", False, True, False, True, True, True, True
    ),
    "UNSUPPORTED": TargetProfile(
        "UNSUPPORTED", False, False, True, False, False, False, False
    ),
}


DEFAULT_TARGET = "MARKETPLACE_ADDON_STABLE"


def get_target(identifier: str | None) -> TargetProfile:
    name = identifier or DEFAULT_TARGET
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"unknown target profile: {name}") from exc

