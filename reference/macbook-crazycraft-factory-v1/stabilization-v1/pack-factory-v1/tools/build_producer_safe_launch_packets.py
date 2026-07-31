#!/usr/bin/env python3
"""Build producer-safe projections of the durable PA-07 through PA-16 assignments."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENTS = ROOT / "assignments"
OUTPUT = ROOT / "launch" / "producer-safe"
BOOTSTRAP = json.loads((ROOT / "FACTORY_REPOSITORY_BOOTSTRAP_RECEIPT.json").read_text())
BASELINES = {entry["pack_id"]: entry for entry in BOOTSTRAP["results"]}
PACK_IDS = [
    "reliquary-vaults",
    "hearth-and-hall",
    "hearthveil",
    "aspectweave",
    "vanguard-arsenal",
    "aperture-foundry",
    "echo-vessels",
    "bounded-outcome-events",
    "momentum-menagerie",
    "latchline-infrastructure",
]
PLATFORM_WORKTREE = (
    "/Users/blakegrove/Desktop/bedrock-server/"
    ".derivedData/worktrees/crazycraft-program-v1/compiler"
)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    os.replace(temporary, path)


def main() -> None:
    for pack_id in PACK_IDS:
        assignment_path = ASSIGNMENTS / f"{pack_id}.assignment.json"
        assignment = json.loads(assignment_path.read_text())
        baseline = BASELINES[pack_id]
        packet = {
            "schema_version": "1.0.0",
            "record_type": "producer_safe_durable_pack_launch",
            "assignment_id": assignment["assignment_id"],
            "control_assignment_sha256": file_digest(assignment_path),
            "pack_id": assignment["pack_id"],
            "pack_name": assignment["pack_name"],
            "assigned_worker_role": assignment["assigned_worker_role"],
            "producer_input_policy": {
                "only": "SANITIZED_PRODUCTION_CONTRACT_AND_THIS_PACKET",
                "source_artifact_names_paths_hashes": "FORBIDDEN",
                "java_or_decompiled_material": "FORBIDDEN",
                "private_oracle": "FORBIDDEN",
                "source_assets": "FORBIDDEN",
            },
            "producer_safe_input": assignment["producer_safe_input"],
            "identity": assignment["identity"],
            "product_scope": assignment["product_scope"],
            "asset_workload": assignment["asset_workload"],
            "technical_allocation": assignment["technical_allocation"],
            "required_outputs": assignment["required_outputs"],
            "mailbox_contract": assignment["mailbox_contract"],
            "publication_rules": assignment["publication_rules"],
            "completion_condition": assignment["completion_condition"],
            "internal_subagent_roles": assignment["internal_subagent_roles"],
            "worker_mission": assignment["worker_mission"],
            "no_ssh_no_studio": assignment["no_ssh_no_studio"],
            "production_authority": {
                "repository": baseline["repository"],
                "ref": baseline["ref"],
                "baseline_commit": baseline["commit"],
                "baseline_tree": baseline["tree"],
                "independent_git_object_store": baseline["independent_git_object_store"],
                "remotes": baseline["remotes"],
                "exclusive_write_scope": baseline["repository"],
            },
            "frozen_platform_input": {
                "worktree": PLATFORM_WORKTREE,
                "access": "READ_ONLY",
                "commit": "aba740f136dce5781e68d34e1c7aaa2a0a3d8671",
                "tree": "2d5c123c9cbc6d4cdaac2ff922916450b5282d08",
                "aggregate_sha256": "84e79568550d800717798858c254498e682d452ec4ab6b95e6320d1a79397f57",
                "manifest_sha256": "b7de7329fd78b451994b367e0ac226099e8d260bd21309f3f5753b3830c42630",
            },
            "process_rules": {
                "candidate_bound_isolation_receipt": "REQUIRED",
                "restricted_identifier_scan": "REQUIRED",
                "restricted_git_object_scan": "REQUIRED",
                "working_tree_candidate": "REJECTED",
                "mailbox_publication": "APPEND_ONLY_EXPECTED_PARENT_WITH_SHARED_LOCK",
                "substantive_progress_required": [
                    "runtime implementation",
                    "BP or RP content",
                    "editable asset source",
                    "deterministic package",
                    "executed qualification evidence",
                ],
            },
            "run_control": "AUTHORIZED_FOR_FACTORY_LAUNCH",
        }
        packet["packet_payload_sha256"] = digest(packet)
        write_json(OUTPUT / f"{pack_id}.launch.json", packet)


if __name__ == "__main__":
    main()
