#!/usr/bin/env python3
"""Build the linked, unchanged Trailbound Stable BDS qualifier-v2 retry."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REMOTE = REPO / "stabilization-v1/remote-execution"
OUTPUT_ROOT = (
    REPO
    / "stabilization-v1/pack-factory-v1/exact-package-qualifier-repair"
)
TRAILBOUND = Path(
    "/Users/blakegrove/Desktop/bedrock-server/program/"
    "crazycraft-autonomous-worker-lanes-v1/thread-09/"
    "trailbound-golden-repair-v2/candidate"
)
QUALIFIER = REMOTE / "exact-package-qualifier/qualify_exact_package.py"
IMAGE_DIGEST = (
    "crazycraft-exact-package-qualifier@sha256:"
    "c3adfe3f7cad7c174d23db52dd14da6937901b1df7f9be853c65167086ed811f"
)


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_hash(record: dict, field: str) -> str:
    value = dict(record)
    value.pop(field, None)
    return hashlib.sha256(canonical(value)).hexdigest()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value) + b"\n")


def main() -> None:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--job-id", default="JOB-000000000013")
    args = parser.parse_args()
    if not re.fullmatch(r"JOB-[0-9]{12}", args.job_id):
        raise RuntimeError("invalid job ID")
    sequence = int(args.job_id.removeprefix("JOB-"))
    output = OUTPUT_ROOT / args.job_id
    if output.exists():
        raise RuntimeError(f"job output already exists: {output}")
    port = 19188 + (2 * sequence)
    if port > 29998:
        raise RuntimeError("derived port outside allowed range")
    container_name = f"factory-trailbound-stable-job-{sequence}"
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / "inputs"
    inputs.mkdir(exist_ok=True)
    source = {
        "behavior.mcpack": TRAILBOUND / "trailbound-packs-behavior.mcpack",
        "resource.mcpack": TRAILBOUND / "trailbound-packs-resource.mcpack",
        "candidate.mcaddon": TRAILBOUND / "trailbound-packs.mcaddon",
    }
    expected = {
        "behavior.mcpack": (
            33229,
            "f26e9daddfd7ba8893f6ccd5934b45ec0f88e1380b3e02038c13051d71fad8f3",
        ),
        "resource.mcpack": (
            65207,
            "14fcdba454ab5ca85381628d71845dadc80b9c255eb812b7aaebea84814ef7af",
        ),
        "candidate.mcaddon": (
            84791,
            "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
        ),
    }
    for name, path in source.items():
        size, digest = expected[name]
        if path.stat().st_size != size or sha(path) != digest:
            raise RuntimeError(f"immutable candidate mismatch: {name}")
        destination = inputs / name
        shutil.copyfile(path, destination)
        destination.chmod(0o400)
    request = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": args.job_id,
        "job_type": "BDS_QUALIFICATION",
        "requesting_authority": "T1",
        "assignment_id": "PA-04-TRAILBOUND-PACKS-V1",
        "campaign_id": "trailbound-packs",
        "exact_input_authorities": [
            {
                "authority_type": "GIT_BUNDLE_SOURCE",
                "repository": (
                    "/Users/blakegrove/Desktop/bedrock-server/program/"
                    "crazycraft-autonomous-worker-lanes-v1/thread-09"
                ),
                "ref": "refs/heads/main",
                "bundle_sha256": "64ef65c1a6d5b90ac55af7f4aa05a951574e055966287ec7912eb01aa706be72",
                "commit": "d2d737c5b7110c1c596ce429649fb002efdf9049",
                "tree": "47d8d3e409b8cc1b6de49654456f6cee5ddfb201",
            },
            {
                "authority_type": "PUBLICATION_COMMIT",
                "commit": "3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5",
                "tree": "f4dfc5db028a709bc89b588b57719ad78b215d8b",
            },
            {
                "authority_type": "TESTER_INFRASTRUCTURE_RETRY",
                "original_job_id": "JOB-000000000011",
                "original_intake_message_id": "MSG-T09-TRAILBOUND-BDS-000001",
                "failed_result_message_id": "MSG-T09-TRAILBOUND-BDS-RESULT-000001",
                "failed_receipt_sha256": "de44597b25794be5ef3538c9487cd15c4edf2c5579afc08a0ab57f3d40947b62",
                "reason": "QUALIFICATION_INFRASTRUCTURE_REPAIRED",
                "candidate_generation": 2,
            },
            {
                "authority_type": "QUALIFIER_IMAGE",
                "image_digest": IMAGE_DIGEST,
                "qualifier_sha256": sha(QUALIFIER),
                "platform": "linux/amd64",
            },
        ],
        "permitted_evidence_roots": [],
        "permitted_candidate_paths": [
            "behavior.mcpack",
            "resource.mcpack",
            "candidate.mcaddon",
            "request.json",
        ],
        "permitted_output_directory": "artifacts",
        "prohibited_disclosure_classes": [
            "CREDENTIALS",
            "DECOMPILED_TEXT",
            "HIDDEN_CASES",
            "PRIVATE_ORACLE_VALUES",
            "RAW_JAVA",
            "SOURCE_ASSETS",
            "SOURCE_EXPRESSION",
            "SOURCE_IDENTIFIERS",
            "SOURCE_PATHS",
        ],
        "timeout_seconds": 900,
        "termination_policy": "TERMINATE_AND_RECEIPT",
        "requested_result_schema": "trailbound-stable-exact-package-v1",
        "bds": {
            "candidate_repository": (
                "/Users/blakegrove/Desktop/bedrock-server/program/"
                "crazycraft-autonomous-worker-lanes-v1/thread-09"
            ),
            "candidate_ref": "refs/heads/main",
            "content_commit": "d2d737c5b7110c1c596ce429649fb002efdf9049",
            "content_tree": "47d8d3e409b8cc1b6de49654456f6cee5ddfb201",
            "metadata_commit": "3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5",
            "metadata_tree": "f4dfc5db028a709bc89b588b57719ad78b215d8b",
            "behavior_pack_path": "behavior.mcpack",
            "behavior_pack_size": expected["behavior.mcpack"][0],
            "behavior_pack_sha256": expected["behavior.mcpack"][1],
            "resource_pack_path": "resource.mcpack",
            "resource_pack_size": expected["resource.mcpack"][0],
            "resource_pack_sha256": expected["resource.mcpack"][1],
            "mcaddon_path": "candidate.mcaddon",
            "mcaddon_size": expected["candidate.mcaddon"][0],
            "mcaddon_sha256": expected["candidate.mcaddon"][1],
            "image_digest": IMAGE_DIGEST,
            "image_platform": "linux/amd64",
            "qualifier_sha256": sha(QUALIFIER),
            "bds_channel": "STABLE",
            "bds_version": "1.26.33.2",
            "bds_binary_sha256": "978ea655c418f112a33b80043d676712ad080724382fafda9509825910fa4043",
            "base_world_sha256": "061501b67b0886296ad2765f1b7c5246efbe38d64b9494303a05b9ee81a58d9a",
            "fixture_set": "TRAILBOUND_EXACT_PACKAGE_LOAD_RESTART_V1",
            "candidate_profile": {
                "schema_version": "crazycraft-bds-candidate-profile-v1",
                "behavior_pack": {
                    "manifest_uuid": "7c428986-b20f-548d-84ae-1c56029426b2",
                    "version": [1, 1, 0],
                    "install_directory": "trailbound-packs",
                },
                "resource_pack": {
                    "manifest_uuid": "565a3efe-77ac-5533-8097-3098881e17d0",
                    "version": [1, 1, 0],
                    "install_directory": "trailbound-packs",
                },
                "addon": {
                    "behavior_member": "trailbound-packs-behavior.mcpack",
                    "resource_member": "trailbound-packs-resource.mcpack",
                },
                "script": {
                    "entry_path": "scripts/main.js",
                    "expected_marker": "[trailbound] runtime initialized",
                },
                "expected_pack_marker": "Trailbound Packs Behavior",
                "world_name": "Trailbound Exact Package",
                "fixture_id": "TRAILBOUND_EXACT_PACKAGE_LOAD_RESTART_V1",
            },
            "expected_gates": [
                "EXACT_PACKAGE_HASH",
                "PACK_LOAD",
                "SHIPPED_ENTRYPOINT",
                "WORLD_RESTART",
                "WORLD_REOPEN",
                "CLEAN_SHUTDOWN",
            ],
            "port": port,
            "container_name": container_name,
            "cpus": 2,
            "memory_mb": 4096,
        },
        "request_payload_sha256": "",
    }
    request["request_payload_sha256"] = payload_hash(
        request, "request_payload_sha256"
    )
    write(output / "request.json", request)
    (output / "request.sha256").write_text(sha(output / "request.json") + "\n")
    manifest = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": request["job_id"],
        "entries": [
            {
                "relative_path": name,
                "sha256": expected[name][1],
                "size_bytes": expected[name][0],
                "content_role": "EXACT_TRAILBOUND_BEDROCK_PACKAGE",
            }
            for name in sorted(source)
        ],
        "manifest_payload_sha256": "",
    }
    manifest["manifest_payload_sha256"] = payload_hash(
        manifest, "manifest_payload_sha256"
    )
    write(output / "input-manifest.json", manifest)


if __name__ == "__main__":
    main()
