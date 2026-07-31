#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from remote_job_lib import (  # noqa: E402
    ValidationError,
    payload_hash,
    validate_request,
)

SHA = re.compile(r"^[0-9a-f]{64}$")


def validate_result(record: dict) -> None:
    required = {
        "schema_version",
        "job_id",
        "job_type",
        "requesting_authority",
        "assignment_id",
        "campaign_id",
        "outcome",
        "abstract_results",
        "opaque_contract_ids",
        "opaque_finding_ids",
        "required_regression_ids",
        "qualification_references",
        "proof_boundary",
        "external_gates_not_run",
        "disclosure_scan",
        "result_payload_sha256",
    }
    if set(record) != required:
        raise ValidationError("result fields are not canonical")
    if record["result_payload_sha256"] != payload_hash(
        record, "result_payload_sha256"
    ):
        raise ValidationError("result payload hash mismatch")
    if record["disclosure_scan"].get("status") != "PASS":
        raise ValidationError("result disclosure scan did not pass")


def validate_receipt(record: dict) -> None:
    required = {
        "schema_version",
        "job_id",
        "request_sha256",
        "input_manifest_sha256",
        "requesting_authority",
        "studio_host_identity",
        "studio_executor_identity",
        "job_type",
        "started_at",
        "ended_at",
        "entrypoint",
        "evidence_roots_accessed",
        "candidate_inputs_accessed",
        "outputs",
        "disclosure_policy_scan",
        "exit_status",
        "cleanup_status",
        "docker_container_ids",
        "codex_session_identifier",
        "authority_envelope",
        "proof_boundary",
        "receipt_payload_sha256",
    }
    if set(record) != required:
        raise ValidationError("receipt fields are not canonical")
    for field in ("request_sha256", "input_manifest_sha256", "receipt_payload_sha256"):
        if not SHA.fullmatch(record[field]):
            raise ValidationError(f"invalid {field}")
    if record["receipt_payload_sha256"] != payload_hash(
        record, "receipt_payload_sha256"
    ):
        raise ValidationError("receipt payload hash mismatch")
    if record["disclosure_policy_scan"].get("status") != "PASS":
        raise ValidationError("receipt disclosure scan did not pass")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("request", "result", "receipt"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--role", choices=("T1", "T10"))
    args = parser.parse_args()
    try:
        record = json.loads(args.path.read_text())
        if args.kind == "request":
            validate_request(record, args.role)
        elif args.kind == "result":
            validate_result(record)
        else:
            validate_receipt(record)
    except (ValidationError, json.JSONDecodeError, OSError) as exc:
        print(f"REMOTE_RECORD_FAIL: {exc}", file=sys.stderr)
        return 1
    print("REMOTE_RECORD_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
