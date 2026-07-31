#!/usr/bin/env python3
"""Validate proof that a production or repair agent ran inside its sandbox."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = {
    "schema_version", "receipt_id", "assignment_id", "role", "repo_root",
    "object_store_identity", "baseline_commit", "transferred_inputs",
    "sandbox_profile_sha256", "environment_manifest_sha256", "launcher_sha256",
    "prompt_context_sha256", "process", "preflight", "outputs",
    "candidate_commit", "candidate_tree", "package_hashes", "cleanup",
}
PROCESS_REQUIRED = {
    "pid", "command", "agent_identity", "tool_hashes", "started_at_utc",
    "ended_at_utc", "exit_status",
}
PREFLIGHT_PASS = {
    "approved_inputs_readable": "YES",
    "production_write": "ALLOWED",
    "runtime_write": "ALLOWED",
    "temp_write": "ALLOWED",
    "cache_write": "ALLOWED",
    "evidence_denied": "YES",
    "control_denied": "YES",
    "private_oracle_denied": "YES",
    "canary_denied": "YES",
    "restricted_identifiers": "NO_MATCH",
    "restricted_hashes": "NO_MATCH",
    "remotes": "NONE",
    "alternates": "NONE",
    "hardlinks": "NONE",
    "cross_lane_symlinks": "NONE",
    "restricted_git_objects": "UNAVAILABLE",
    "restricted_env": "NONE",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    findings: list[dict[str, str]] = []
    try:
        packet = json.loads(args.receipt.read_text())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "findings": [{"code": "RECEIPT_INVALID", "detail": str(exc)}]}))
        return 1

    missing = sorted(REQUIRED - set(packet))
    if missing:
        findings.append({"code": "REQUIRED_FIELDS_MISSING", "detail": ", ".join(missing)})
    if packet.get("role") not in {"feature_producer", "visual_producer", "segment_integrator", "repair_agent"}:
        findings.append({"code": "ROLE_INVALID", "detail": str(packet.get("role"))})
    for field in ("sandbox_profile_sha256", "environment_manifest_sha256", "launcher_sha256", "prompt_context_sha256"):
        if not HEX64.fullmatch(str(packet.get(field, ""))):
            findings.append({"code": "HASH_INVALID", "detail": field})

    process = packet.get("process", {})
    process_missing = sorted(PROCESS_REQUIRED - set(process)) if isinstance(process, dict) else sorted(PROCESS_REQUIRED)
    if process_missing:
        findings.append({"code": "PROCESS_FIELDS_MISSING", "detail": ", ".join(process_missing)})
    if not isinstance(process, dict) or not isinstance(process.get("pid"), int) or process.get("pid", 0) <= 0:
        findings.append({"code": "PID_INVALID", "detail": str(process.get("pid") if isinstance(process, dict) else None)})
    if not isinstance(process, dict) or process.get("exit_status") != 0:
        findings.append({"code": "PROCESS_NOT_SUCCESSFUL", "detail": str(process.get("exit_status") if isinstance(process, dict) else None)})
    if not isinstance(process, dict) or not isinstance(process.get("command"), list) or not process.get("command"):
        findings.append({"code": "COMMAND_INVALID", "detail": "command must be a nonempty argv array"})
    for digest in (process.get("tool_hashes", {}) if isinstance(process, dict) else {}).values():
        if not HEX64.fullmatch(str(digest)):
            findings.append({"code": "TOOL_HASH_INVALID", "detail": str(digest)})

    preflight = packet.get("preflight", {})
    for field, expected in PREFLIGHT_PASS.items():
        actual = preflight.get(field) if isinstance(preflight, dict) else None
        if actual != expected:
            findings.append({"code": "PREFLIGHT_FAILED", "detail": f"{field}: expected {expected}, got {actual}"})
    if not isinstance(preflight, dict) or preflight.get("network") not in {"DENIED", "ALLOWLISTED"}:
        findings.append({"code": "NETWORK_POLICY_INVALID", "detail": str(preflight.get("network") if isinstance(preflight, dict) else None)})

    result = {"schema_version": "1.0.0", "receipt": str(args.receipt),
              "status": "PASS" if not findings else "FAIL", "findings": findings}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
