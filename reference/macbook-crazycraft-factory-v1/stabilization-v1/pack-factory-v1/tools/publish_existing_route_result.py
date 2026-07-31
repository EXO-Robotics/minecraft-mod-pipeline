#!/usr/bin/env python3
"""Publish the exact Trailbound tester infrastructure result without product blame."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORIES = json.loads(
    (ROOT / "FACTORY_REPOSITORY_ALLOCATION_REGISTRY.json").read_text(encoding="utf-8")
)
MAILBOX = Path(REPOSITORIES["mailbox_repository"]["path"])
REMOTE_RESULT = ROOT / "route-verification" / "JOB-000000000011-result"
OUTPUT = ROOT / "EXISTING_CANDIDATE_DOCKER_BDS_ROUTE_VERIFICATION.json"
MESSAGE_ID = "MSG-T09-TRAILBOUND-BDS-RESULT-000001"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(MAILBOX), *args], text=True).strip()


def main() -> None:
    receipt = json.loads((REMOTE_RESULT / "receipt.json").read_text())
    result = json.loads((REMOTE_RESULT / "result.json").read_text())
    if receipt["job_id"] != "JOB-000000000011" or result["campaign_id"] != "trailbound-packs":
        raise SystemExit("remote result binding mismatch")
    if receipt["disclosure_policy_scan"]["status"] != "PASS":
        raise SystemExit("remote result disclosure scan failed")
    target = MAILBOX / "tester_results" / "trailbound-packs" / f"{MESSAGE_ID}.json"
    if target.exists():
        raise SystemExit(f"result already published: {target}")
    message = {
        "schema_version": "1.0.0",
        "message_id": MESSAGE_ID,
        "message_type": "TEST_FAIL_INFRASTRUCTURE",
        "pack_id": "trailbound-packs",
        "sender_role": "PERSISTENT_TESTER",
        "recipient_role": "T1_PORTFOLIO_SUPERVISOR",
        "created_at": "2026-07-29T17:05:00Z",
        "source_authority_commit": git("rev-parse", "HEAD"),
        "source_authority_tree": git("show", "-s", "--format=%T", "HEAD"),
        "candidate_generation": 2,
        "exact_artifact_hashes": {
            "behavior_pack": "f26e9daddfd7ba8893f6ccd5934b45ec0f88e1380b3e02038c13051d71fad8f3",
            "resource_pack": "14fcdba454ab5ca85381628d71845dadc80b9c255eb812b7aaebea84814ef7af",
            "mcaddon": "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
        },
        "parent_message_id": "MSG-T09-TRAILBOUND-BDS-000001",
        "required_action": "REPAIR_OR_REPLACE_EXACT_PACKAGE_QUALIFIER_IMAGE_THEN_RETRY_UNCHANGED_CANDIDATE",
        "idempotency_key": hashlib.sha256(
            b"factory:trailbound:stable-route:job-11:infrastructure-result"
        ).hexdigest(),
        "proof_boundary": [
            "REMOTE_TRANSFER_AND_EXACT_INPUT_HASH_PASS",
            "DOCKER_INVOCATION_PASS",
            "BDS_RUNTIME_NOT_RUN",
            "PRODUCT_CANDIDATE_NOT_INVALIDATED",
            "CLIENT_AUDIO_CONTROLLER_MULTIPLAYER_AND_RELEASE_NOT_RUN",
        ],
        "result": "TEST_FAIL_INFRASTRUCTURE",
        "candidate_hash": "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
        "findings": [
            {
                "finding_id": "INFRA-BDS-ENTRYPOINT-001",
                "severity": "BLOCKING_INFRASTRUCTURE",
                "abstract_defect": "Digest-pinned tester image lacks the allowlisted exact-package qualification entrypoint.",
                "allowed_repair_scope": ["tester image or allowlisted qualifier entrypoint only"],
                "required_regression_gates": [
                    "REMOTE_RECEIPT_VALIDATION",
                    "EXACT_PACKAGE_HASH",
                    "STABLE_BDS_LOAD_RESTART",
                ],
            }
        ],
        "qualification_receipts": [
            {
                "job_id": receipt["job_id"],
                "request_sha256": receipt["request_sha256"],
                "receipt_sha256": digest(REMOTE_RESULT / "receipt.json"),
                "result_sha256": digest(REMOTE_RESULT / "result.json"),
                "status": "FAILED_INFRASTRUCTURE",
                "candidate_mutated": False,
            }
        ],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(message, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    git("add", str(target.relative_to(MAILBOX)))
    subprocess.check_call(
        [
            "git",
            "-C",
            str(MAILBOX),
            "-c",
            "user.name=Crazy Craft Factory Mailbox",
            "-c",
            "user.email=factory-mailbox@local.invalid",
            "commit",
            "-m",
            "test: record Trailbound BDS tester infrastructure blocker",
        ]
    )
    verification = {
        "schema_version": "1.0.0",
        "record_type": "existing_candidate_docker_bds_route_verification",
        "pack_id": "trailbound-packs",
        "candidate": {
            "publication_commit": "3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5",
            "publication_tree": "f4dfc5db028a709bc89b588b57719ad78b215d8b",
            "behavior_pack_sha256": message["exact_artifact_hashes"]["behavior_pack"],
            "resource_pack_sha256": message["exact_artifact_hashes"]["resource_pack"],
            "mcaddon_sha256": message["exact_artifact_hashes"]["mcaddon"],
        },
        "mailbox_result": {
            "message_id": MESSAGE_ID,
            "message_sha256": digest(target),
            "commit": git("rev-parse", "HEAD"),
            "tree": git("show", "-s", "--format=%T", "HEAD"),
        },
        "remote_job": {
            "job_id": receipt["job_id"],
            "request_sha256": receipt["request_sha256"],
            "input_manifest_sha256": receipt["input_manifest_sha256"],
            "receipt_sha256": digest(REMOTE_RESULT / "receipt.json"),
            "result_sha256": digest(REMOTE_RESULT / "result.json"),
            "studio_host_identity": receipt["studio_host_identity"],
            "disclosure_scan": receipt["disclosure_policy_scan"]["status"],
            "cleanup_status": receipt["cleanup_status"],
            "exit_status": receipt["exit_status"],
        },
        "subgates": {
            "MAILBOX_TO_STUDIO_ROUTE": "PASS",
            "EXACT_INPUT_HASH_VALIDATION": "PASS",
            "REMOTE_DISCLOSURE_SCAN": "PASS",
            "DOCKER_INVOCATION": "PASS",
            "EXACT_BDS_QUALIFIER_ENTRYPOINT": "FAIL",
            "STABLE_BDS_RUNTIME": "BLOCKED",
        },
        "classification": "TEST_FAIL_INFRASTRUCTURE",
        "candidate_validity": "PRESERVED_UNCHANGED",
        "status": "BLOCKED",
        "exact_blocker": "Pinned image crazycraft-python-test@sha256:420388... lacks /opt/crazycraft/bin/qualify-exact-package.",
        "proof_boundary": "Proves immutable mailbox routing, exact remote input validation, Docker invocation, receipt return, and disclosure scan. Does not prove any BDS runtime gate.",
    }
    OUTPUT.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
