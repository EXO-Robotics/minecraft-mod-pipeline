#!/usr/bin/env python3
"""Validate cross-role identity, lane authority, and gate-ledger contracts."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
ROLE_CONTRACTS = {
    "evidence_analyst": ("analyze-java-mod-evidence", "EVIDENCE", False),
    "contract_steward": ("sanitize-java-bedrock-contracts", "CONTROL", False),
    "feature_producer": ("produce-bedrock-cleanroom-feature", "PRODUCTION", True),
    "visual_producer": ("produce-golden-blockbench-asset", "PRODUCTION", True),
    "segment_integrator": ("integrate-bedrock-subsystem", "INTEGRATION", True),
    "independent_auditor": ("audit-java-bedrock-cleanroom", "AUDIT", False),
    "visual_auditor": ("audit-golden-blockbench-asset", "AUDIT", False),
    "portfolio_auditor": ("audit-bedrock-portfolio-freeze", "AUDIT", False),
    "bds_qualifier": ("qualify-bedrock-candidate", "AUDIT", False),
    "observation_tester": ("observe-bedrock-factory-pack", "AUDIT", False),
}
ROLE_ALLOWED_GATES = {
    "evidence_analyst": {"EVIDENCE_RECORDED", "JAVA_PILOT_CANDIDATE_QUALIFIED"},
    "contract_steward": {
        "INTENT_DISTILLED",
        "CLEAN_ROOM_CONTRACTED",
        "PILOT_READY_FOR_CLEANROOM_PRODUCTION",
    },
    "feature_producer": {
        "IMPLEMENTED",
        "STATIC_QUALIFIED",
        "PLAYER_REACHABLE_FEATURE",
        "CANDIDATE_READY_FOR_INDEPENDENT_AUDIT",
    },
    "visual_producer": {
        "IMPLEMENTED",
        "STATIC_QUALIFIED",
        "BLOCKBENCH_AUTHORED",
        "CANDIDATE_READY_FOR_INDEPENDENT_AUDIT",
    },
    "segment_integrator": {
        "IMPLEMENTED",
        "STATIC_QUALIFIED",
        "PLAYER_REACHABLE_FEATURE",
        "INTEGRATED_CANDIDATE_FROZEN",
    },
    "independent_auditor": {
        "SEMANTIC_AUDIT",
        "ORIGINALITY_AUDIT",
        "ISOLATION_AUDIT",
        "LINEAGE_AUDIT",
        "TRANSLATION_LOOP_PROVEN",
        "TRANSLATION_LOOP_PROVEN_WITH_LIMITATIONS",
        "SEGMENT_TRANSLATION_LOOP_PROVEN_WITH_LIMITATIONS",
    },
    "visual_auditor": {
        "BLOCKBENCH_AUDIT",
        "ORIGINALITY_AUDIT",
        "STATIC_QUALIFIED",
    },
    "portfolio_auditor": {
        "INVENTORY_RECONCILED",
        "MUTATION_AUDIT",
        "PARTIAL_CANDIDATE_FROZEN",
        "PORTFOLIO_FREEZE_PROVEN_WITH_PLATFORM_LIMITATIONS",
    },
    "bds_qualifier": {
        "BDS_QUALIFIED",
        "STABLE_BDS",
        "PREVIEW_BDS",
        "RESTART_PERSISTENCE",
        "SIMULATED_ACTIVITY",
        "STRESS_CLEANUP",
    },
    "observation_tester": {
        "INSTRUMENTATION_CALIBRATION",
        "STABLE_NETWORK_PLAYER_OBSERVATION",
        "PREVIEW_NETWORK_PLAYER_OBSERVATION",
        "OBSERVATIONS_READY_FOR_T10",
        "ORACLE_INSUFFICIENT",
        "CLIENT_REQUIRED",
        "INCONCLUSIVE",
        "INFRASTRUCTURE_BLOCKED",
    },
}
GATE_STATUSES = {
    "PASSED",
    "FAILED",
    "BLOCKED",
    "PENDING",
    "NOT_APPLICABLE",
    "SUPERSEDED_ASSERTION",
}


def _string_array(value: Any, field: str, errors: list[str], *, nonempty: bool = True) -> None:
    valid = isinstance(value, list) and all(isinstance(row, str) and row for row in value)
    if not valid or (nonempty and not value):
        errors.append(f"{field} must be {'a non-empty' if nonempty else 'an'} string array")


def validate_assignment(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["assignment must be an object"]
    required = {
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
        "requires_activation_attestation",
    }
    missing = sorted(required - value.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
    if value.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if not isinstance(value.get("assignment_id"), str) or not value.get("assignment_id"):
        errors.append("assignment_id must be a non-empty string")
    role = value.get("role")
    contract = ROLE_CONTRACTS.get(role)
    if contract is None:
        errors.append(f"unsupported role: {role}")
    else:
        expected_skill, expected_lane, expected_attestation = contract
        if value.get("skill") != expected_skill:
            errors.append(f"role {role} requires skill {expected_skill}")
        if value.get("lane") != expected_lane:
            errors.append(f"role {role} requires lane {expected_lane}")
        if value.get("requires_activation_attestation") is not expected_attestation:
            errors.append(
                f"role {role} requires requires_activation_attestation={str(expected_attestation).lower()}"
            )
    if not isinstance(value.get("lane_root"), str) or not Path(value["lane_root"]).is_absolute():
        errors.append("lane_root must be absolute")
    for field in (
        "allowed_read_paths",
        "prohibited_paths",
        "output_artifacts",
        "required_checks",
        "stop_states",
        "gate_authority",
    ):
        _string_array(value.get(field), field, errors)
    authorities = value.get("gate_authority")
    if role in ROLE_ALLOWED_GATES and isinstance(authorities, list):
        unsupported = sorted(set(authorities) - ROLE_ALLOWED_GATES[role])
        if unsupported:
            errors.append(
                f"role {role} cannot claim gates: {', '.join(unsupported)}"
            )
    _string_array(value.get("allowed_write_paths"), "allowed_write_paths", errors, nonempty=False)
    artifacts = value.get("input_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("input_artifacts must be a non-empty array")
    else:
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                errors.append("input artifact must be an object")
                continue
            if not isinstance(artifact.get("path"), str) or not Path(artifact["path"]).is_absolute():
                errors.append("input artifact path must be absolute")
            if not SHA256.fullmatch(str(artifact.get("sha256", ""))):
                errors.append("input artifact sha256 must be lowercase SHA-256")
    if not isinstance(value.get("completion_state"), str) or not value.get("completion_state"):
        errors.append("completion_state must be a non-empty string")
    if not isinstance(value.get("requires_activation_attestation"), bool):
        errors.append("requires_activation_attestation must be boolean")
    return errors


def validate_gate_ledger(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict) or not value:
        return ["gate ledger must be a non-empty object"]
    for gate, record in value.items():
        prefix = f"gate {gate}"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        status = record.get("status")
        if status not in GATE_STATUSES:
            errors.append(f"{prefix} has unsupported status: {status}")
        if status == "PASSED":
            for field in ("authority", "receipt", "classification"):
                if not isinstance(record.get(field), str) or not record.get(field):
                    errors.append(f"{prefix} PASSED requires {field}")
            if not SHA256.fullmatch(str(record.get("artifact_sha256", ""))):
                errors.append(f"{prefix} PASSED requires lowercase artifact_sha256")
        elif status in {"PENDING", "BLOCKED"} and record.get("artifact_sha256") not in (None, ""):
            errors.append(f"{prefix} {status} cannot claim artifact_sha256 proof")
    return errors


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assignment", type=Path)
    parser.add_argument("--gate-ledger", type=Path)
    args = parser.parse_args()
    errors = validate_assignment(_load(args.assignment))
    if args.gate_ledger:
        errors.extend(validate_gate_ledger(_load(args.gate_ledger)))
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
