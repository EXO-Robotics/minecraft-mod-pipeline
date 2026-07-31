#!/usr/bin/env python3
"""Validate a hash-bound Java-to-Bedrock subagent assignment packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from validate_role_contract import validate_assignment

ROLES = {
    "evidence_analyst",
    "contract_steward",
    "feature_producer",
    "visual_producer",
    "segment_integrator",
    "independent_auditor",
    "visual_auditor",
    "portfolio_auditor",
    "bds_qualifier",
}
REQUIRED = {
    "schema_version",
    "assignment_id",
    "role",
    "skill",
    "lane",
    "lane_root",
    "allowed_read_paths",
    "allowed_write_paths",
    "prohibited_paths",
    "input_artifacts",
    "output_artifacts",
    "required_checks",
    "stop_states",
    "completion_state",
    "gate_authority",
    "requires_process_receipt",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PRODUCTION_ROLES = {"feature_producer", "visual_producer", "segment_integrator"}
PRODUCTION_PROCESS_REQUIRED = {
    "sandbox_profile_sha256",
    "environment_manifest_sha256",
    "launcher_sha256",
    "process_receipt_path",
    "lane_home",
    "lane_tmp",
    "lane_cache",
    "lane_logs",
    "network_policy",
    "negative_access_checks",
}
PRODUCTION_FORBIDDEN_TEXT = (
    "evidence-vault",
    "/evidence/",
    "semantic-oracle.private",
    "private-oracle",
    "source-manifest",
    "java-source",
    "working-analysis-copy",
    "hidden-canary",
)
VISUAL_PRODUCER_REQUIRED = {
    "typed_visual_contract_sha256",
    "class_profile_sha256",
    "proof_render_contract_sha256",
    "clip_inventory",
    "proof_view_inventory",
    "toolchain",
    "deterministic_archive",
    "candidate_output_root",
    "bds_targets",
}
VISUAL_AUDITOR_REQUIRED = {
    "candidate_commit",
    "candidate_package_sha256",
    "originality_policy_sha256",
    "audit_scratch_root",
    "finding_output_path",
    "toolchain",
    "required_mutations",
}


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--verify-files", action="store_true")
    args = parser.parse_args()

    findings: list[dict[str, str]] = []
    try:
        raw = args.packet.read_bytes()
        packet = json.loads(raw)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "findings": [{"code": "PACKET_INVALID", "detail": str(exc)}]}))
        return 1

    missing = sorted(REQUIRED - set(packet))
    if missing:
        findings.append({"code": "REQUIRED_FIELDS_MISSING", "detail": ", ".join(missing)})
    for detail in validate_assignment(packet):
        findings.append({"code": "ROLE_CONTRACT_INVALID", "detail": detail})

    role = packet.get("role")
    if role not in ROLES:
        findings.append({"code": "ROLE_INVALID", "detail": str(role)})
    role_required = (
        VISUAL_PRODUCER_REQUIRED
        if role == "visual_producer"
        else VISUAL_AUDITOR_REQUIRED
        if role == "visual_auditor"
        else set()
    )
    role_missing = sorted(role_required - set(packet))
    if role_missing:
        findings.append({"code": "ROLE_FIELDS_MISSING", "detail": ", ".join(role_missing)})

    lane_value = packet.get("lane_root", "")
    lane_root = Path(lane_value) if isinstance(lane_value, str) else Path("")
    if not lane_root.is_absolute():
        findings.append({"code": "LANE_ROOT_NOT_ABSOLUTE", "detail": str(lane_value)})

    for field in ("allowed_read_paths", "allowed_write_paths", "prohibited_paths"):
        values = packet.get(field, [])
        if not isinstance(values, list):
            findings.append({"code": "PATH_LIST_INVALID", "detail": field})
            continue
        for value in values:
            path = Path(value) if isinstance(value, str) else Path("")
            if not path.is_absolute():
                findings.append({"code": "PATH_NOT_ABSOLUTE", "detail": f"{field}: {value}"})
            if field == "allowed_write_paths" and lane_root.is_absolute() and not is_within(path, lane_root):
                findings.append({"code": "WRITE_ESCAPES_LANE", "detail": str(value)})

    for field in ("candidate_output_root", "audit_scratch_root", "finding_output_path"):
        value = packet.get(field)
        if value is None:
            continue
        path = Path(value) if isinstance(value, str) else Path("")
        if not path.is_absolute():
            findings.append({"code": "ROLE_PATH_NOT_ABSOLUTE", "detail": f"{field}: {value}"})
        elif lane_root.is_absolute() and not is_within(path, lane_root):
            findings.append({"code": "ROLE_WRITE_ESCAPES_LANE", "detail": f"{field}: {value}"})

    for field in (
        "typed_visual_contract_sha256",
        "class_profile_sha256",
        "proof_render_contract_sha256",
        "candidate_package_sha256",
        "originality_policy_sha256",
    ):
        value = packet.get(field)
        if value is not None and (not isinstance(value, str) or not HEX64.fullmatch(value)):
            findings.append({"code": "ROLE_HASH_INVALID", "detail": field})

    for artifact in packet.get("input_artifacts", []):
        if not isinstance(artifact, dict):
            findings.append({"code": "INPUT_ARTIFACT_INVALID", "detail": repr(artifact)})
            continue
        path_text = artifact.get("path")
        digest = artifact.get("sha256")
        if not isinstance(path_text, str) or not Path(path_text).is_absolute():
            findings.append({"code": "INPUT_PATH_INVALID", "detail": str(path_text)})
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            findings.append({"code": "INPUT_HASH_INVALID", "detail": str(path_text)})
        elif args.verify_files and isinstance(path_text, str):
            path = Path(path_text)
            if not path.is_file():
                findings.append({"code": "INPUT_NOT_FOUND", "detail": path_text})
            else:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != digest:
                    findings.append({"code": "INPUT_HASH_MISMATCH", "detail": path_text})

    if role in PRODUCTION_ROLES:
        process_missing = sorted(PRODUCTION_PROCESS_REQUIRED - set(packet))
        if process_missing:
            findings.append({"code": "PROCESS_FIELDS_MISSING", "detail": ", ".join(process_missing)})
        for field in ("sandbox_profile_sha256", "environment_manifest_sha256", "launcher_sha256"):
            value = packet.get(field)
            if value is not None and (not isinstance(value, str) or not HEX64.fullmatch(value)):
                findings.append({"code": "PROCESS_HASH_INVALID", "detail": field})
        for field in ("process_receipt_path", "lane_home", "lane_tmp", "lane_cache", "lane_logs"):
            value = packet.get(field)
            path = Path(value) if isinstance(value, str) else Path("")
            if not path.is_absolute():
                findings.append({"code": "PROCESS_PATH_NOT_ABSOLUTE", "detail": f"{field}: {value}"})
            elif lane_root.is_absolute() and not is_within(path, lane_root):
                findings.append({"code": "PROCESS_PATH_ESCAPES_LANE", "detail": f"{field}: {value}"})
        if packet.get("repair_of") is not None:
            parent = packet.get("parent_process_receipt_sha256")
            if not isinstance(parent, str) or not HEX64.fullmatch(parent):
                findings.append({"code": "REPAIR_PARENT_RECEIPT_INVALID", "detail": "parent_process_receipt_sha256"})
        lowered = raw.decode("utf-8", errors="replace").lower()
        for needle in PRODUCTION_FORBIDDEN_TEXT:
            if needle in lowered:
                findings.append({"code": "PRODUCTION_BOUNDARY_LEAK", "detail": needle})

    result = {
        "schema_version": "1.0.0",
        "packet": str(args.packet),
        "packet_sha256": hashlib.sha256(raw).hexdigest(),
        "role": role,
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
