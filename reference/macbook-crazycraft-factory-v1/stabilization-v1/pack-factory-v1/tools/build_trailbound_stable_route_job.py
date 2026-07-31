#!/usr/bin/env python3
"""Build one exact, hash-bound Trailbound Stable-BDS route verification job."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REMOTE = ROOT.parent / "remote-execution"
sys.path.insert(0, str(REMOTE))
from remote_job_lib import (  # noqa: E402
    PROHIBITED_DISCLOSURE_CLASSES,
    payload_hash,
    sha256_file,
    write_json,
)

JOB_ID = "JOB-000000000011"
BUNDLE = ROOT / "route-verification" / JOB_ID
TRAILBOUND = (
    Path("/Users/blakegrove/Desktop/bedrock-server/program/")
    / "crazycraft-autonomous-worker-lanes-v1/thread-09/trailbound-golden-repair-v2/candidate"
)


def main() -> None:
    if BUNDLE.exists():
        raise SystemExit(f"job bundle already exists: {BUNDLE}")
    inputs = BUNDLE / "inputs"
    inputs.mkdir(parents=True)
    source_files = {
        "behavior.mcpack": TRAILBOUND / "trailbound-packs-behavior.mcpack",
        "resource.mcpack": TRAILBOUND / "trailbound-packs-resource.mcpack",
        "candidate.mcaddon": TRAILBOUND / "trailbound-packs.mcaddon",
    }
    for name, source in source_files.items():
        shutil.copyfile(source, inputs / name)

    expected = {
        "behavior.mcpack": "f26e9daddfd7ba8893f6ccd5934b45ec0f88e1380b3e02038c13051d71fad8f3",
        "resource.mcpack": "14fcdba454ab5ca85381628d71845dadc80b9c255eb812b7aaebea84814ef7af",
        "candidate.mcaddon": "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
    }
    for name, expected_hash in expected.items():
        observed = sha256_file(inputs / name)
        if observed != expected_hash:
            raise SystemExit(f"exact Trailbound input mismatch: {name}")

    request = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": JOB_ID,
        "job_type": "BDS_QUALIFICATION",
        "requesting_authority": "T1",
        "assignment_id": "PA-04-TRAILBOUND-PACKS-V1",
        "campaign_id": "trailbound-packs",
        "exact_input_authorities": [
            {
                "authority_type": "GIT_BUNDLE_SOURCE",
                "commit": "d2d737c5b7110c1c596ce429649fb002efdf9049",
                "tree": "47d8d3e409b8cc1b6de49654456f6cee5ddfb201",
                "bundle_sha256": "64ef65c1a6d5b90ac55af7f4aa05a951574e055966287ec7912eb01aa706be72",
            },
            {
                "authority_type": "PUBLICATION_COMMIT",
                "commit": "3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5",
                "tree": "f4dfc5db028a709bc89b588b57719ad78b215d8b",
            },
            {
                "authority_type": "FACTORY_TESTER_INTAKE",
                **json.loads((ROOT / "EXISTING_CANDIDATE_TESTER_ROUTE_INTAKE.json").read_text()),
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
        "prohibited_disclosure_classes": sorted(PROHIBITED_DISCLOSURE_CLASSES),
        "timeout_seconds": 900,
        "termination_policy": "TERMINATE_AND_RECEIPT",
        "requested_result_schema": "trailbound-stable-exact-package-v1",
        "bds": {
            "candidate_repository": "trailbound-golden-repair-v2.bundle",
            "candidate_commit": "d2d737c5b7110c1c596ce429649fb002efdf9049",
            "candidate_tree": "47d8d3e409b8cc1b6de49654456f6cee5ddfb201",
            "behavior_pack_sha256": expected["behavior.mcpack"],
            "resource_pack_sha256": expected["resource.mcpack"],
            "mcaddon_sha256": expected["candidate.mcaddon"],
            "image_digest": "crazycraft-python-test@sha256:4203883759408bd6904fc20a974b4c16094b5c8e605a1cbbaaa87e139e8fbebe",
            "bds_channel": "STABLE",
            "bds_version": "ENTRYPOINT_AUTHORITY_UNRESOLVED",
            "fixture_set": "TRAILBOUND_EXACT_PACKAGE_LOAD_RESTART_V1",
            "expected_gates": [
                "EXACT_PACKAGE_HASH",
                "PACK_LOAD",
                "SHIPPED_ENTRYPOINT",
                "WORLD_RESTART",
                "PERSISTENCE_RECOVERY",
                "CLEAN_SHUTDOWN",
            ],
            "port": 19211,
            "container_name": "factory-trailbound-stable-job-11",
            "cpus": 2,
            "memory_mb": 2048,
        },
        "request_payload_sha256": "",
    }
    request["request_payload_sha256"] = payload_hash(request, "request_payload_sha256")
    write_json(BUNDLE / "request.json", request)
    (BUNDLE / "request.sha256").write_text(sha256_file(BUNDLE / "request.json") + "\n")
    shutil.copyfile(BUNDLE / "request.json", inputs / "request.json")
    entries = [
        {
            "relative_path": path.name,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "content_role": (
                "EXACT_TRAILBOUND_REQUEST"
                if path.name == "request.json"
                else "EXACT_TRAILBOUND_BEDROCK_PACKAGE"
            ),
        }
        for path in sorted(inputs.iterdir())
    ]
    manifest = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": JOB_ID,
        "entries": entries,
        "manifest_payload_sha256": "",
    }
    manifest["manifest_payload_sha256"] = payload_hash(
        manifest, "manifest_payload_sha256"
    )
    write_json(BUNDLE / "input-manifest.json", manifest)
    print(BUNDLE)


if __name__ == "__main__":
    main()
