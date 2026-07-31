#!/usr/bin/env python3
"""Validate a clean-room worker receipt without reading credentials."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_KEYS = {
    "token", "access_token", "refresh_token", "credential", "credentials",
    "auth_value", "installation_id_value", "session_contents",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def walk_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                fail(f"forbidden credential-bearing key: {key}")
            walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            walk_keys(child)


def require_bool(mapping: dict, key: str, expected: bool) -> None:
    if mapping.get(key) is not expected:
        fail(f"{key} must be {str(expected).lower()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    data = json.loads(args.receipt.read_text(encoding="utf-8"))
    walk_keys(data)

    if data.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    for key in ("worker_id", "role", "production_repository", "production_commit"):
        if not isinstance(data.get(key), str) or not data[key]:
            fail(f"missing non-empty {key}")
    for key in ("assignment_sha256", "sanitized_contract_sha256"):
        if not HEX64.fullmatch(str(data.get(key, ""))):
            fail(f"{key} must be lowercase SHA-256")

    launcher = data.get("launcher")
    auth = data.get("authentication")
    cleanup = data.get("cleanup")
    probes = data.get("negative_access")
    if not isinstance(launcher, dict) or not HEX64.fullmatch(str(launcher.get("command_sha256", ""))):
        fail("launcher.command_sha256 is invalid")
    require_bool(launcher, "started", True)
    if launcher.get("exit_code") not in (0, None):
        fail("launcher exit_code must be zero or null")
    if not isinstance(auth, dict):
        fail("authentication object missing")
    for key, expected in (
        ("explicitly_authorized", True),
        ("used_for_startup_only", True),
        ("values_logged", False),
        ("values_hashed", False),
        ("copied_into_repository", False),
        ("temporary_copies_remaining", False),
    ):
        require_bool(auth, key, expected)
    if not isinstance(probes, list) or not probes:
        fail("negative_access must contain probes")
    if any(not isinstance(row, dict) or row.get("denied") is not True for row in probes):
        fail("every negative-access probe must be denied")
    if not isinstance(cleanup, dict):
        fail("cleanup object missing")
    require_bool(cleanup, "startup_temp_scanned", True)
    require_bool(cleanup, "production_root_scanned", True)
    if cleanup.get("credential_files_found") != 0 or cleanup.get("canaries_found") != 0:
        fail("cleanup found forbidden material")
    print("PASS clean-room worker receipt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
