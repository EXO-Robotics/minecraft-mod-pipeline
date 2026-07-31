#!/usr/bin/env python3
"""Create the independent append-only factory mailbox and prove one round trip."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads(
    (ROOT / "FACTORY_REPOSITORY_ALLOCATION_REGISTRY.json").read_text(encoding="utf-8")
)
TARGET = Path(REGISTRY["mailbox_repository"]["path"])
BRANCH = REGISTRY["mailbox_repository"]["ref"].removeprefix("refs/heads/")
SCHEMAS = ROOT / "mailboxes" / "schemas"
RECEIPT = ROOT / "SYNTHETIC_MAILBOX_ROUND_TRIP_RECEIPT.json"


def run(*args: str, cwd: Path = TARGET) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def commit(message: str) -> tuple[str, str]:
    run("git", "add", ".")
    run(
        "git",
        "-c",
        "user.name=Crazy Craft Factory Mailbox",
        "-c",
        "user.email=factory-mailbox@local.invalid",
        "commit",
        "-m",
        message,
    )
    return run("git", "rev-parse", "HEAD"), run("git", "show", "-s", "--format=%T", "HEAD")


def make_zip(path: Path, member: str, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    info = zipfile.ZipInfo(member, (1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(info, content)


def base(
    message_id: str,
    message_type: str,
    sender: str,
    recipient: str,
    parent: str | None,
    required_action: str,
    source_commit: str,
    source_tree: str,
    hashes: dict[str, str],
) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "message_id": message_id,
        "message_type": message_type,
        "pack_id": "synthetic-mailbox-fixture",
        "sender_role": sender,
        "recipient_role": recipient,
        "created_at": "2026-07-29T16:40:00Z",
        "source_authority_commit": source_commit,
        "source_authority_tree": source_tree,
        "candidate_generation": 1,
        "exact_artifact_hashes": hashes,
        "parent_message_id": parent,
        "required_action": required_action,
        "idempotency_key": hashlib.sha256(
            f"factory-roundtrip:{message_id}".encode("utf-8")
        ).hexdigest(),
        "proof_boundary": [
            "SYNTHETIC_MAILBOX_PROTOCOL_ONLY",
            "NO_PRODUCT_QUALIFICATION",
            "NO_BDS_EXECUTION",
            "NO_CAMPAIGN_AUTHORITY",
        ],
    }


def main() -> None:
    if TARGET.exists():
        raise SystemExit(f"mailbox target already exists; refusing rewrite: {TARGET}")
    TARGET.mkdir(parents=True)
    run("git", "init", "-b", BRANCH, str(TARGET), cwd=TARGET.parent)
    (TARGET / ".gitignore").write_text(".runtime/\n.DS_Store\n*.tmp\n", encoding="utf-8")
    (TARGET / "README.md").write_text(
        "# Crazy Craft pack-factory mailbox\n\n"
        "Messages are immutable Git records. Consumption cursors live under the "
        "ignored `.runtime/` directory and never modify a message.\n",
        encoding="utf-8",
    )
    for name in (
        "candidate_submissions",
        "tester_intake",
        "tester_results",
        "worker_repairs",
        "integration_intake",
        "final_decisions",
    ):
        directory = TARGET / name
        directory.mkdir()
        (directory / ".keep").write_text("", encoding="utf-8")
    shutil.copytree(SCHEMAS, TARGET / "schemas")

    fixture = TARGET / "fixtures" / "synthetic-mailbox-fixture"
    behavior = fixture / "synthetic-behavior.mcpack"
    resource = fixture / "synthetic-resource.mcpack"
    addon = fixture / "synthetic.mcaddon"
    make_zip(behavior, "NOT_A_PRODUCT.txt", b"synthetic behavior mailbox fixture\n")
    make_zip(resource, "NOT_A_PRODUCT.txt", b"synthetic resource mailbox fixture\n")
    make_zip(addon, "NOT_A_PRODUCT.txt", b"synthetic addon mailbox fixture\n")
    artifacts = {
        "behavior_pack": digest(behavior),
        "resource_pack": digest(resource),
        "mcaddon": digest(addon),
    }
    manifest = {
        "schema_version": "1.0.0",
        "fixture_only": True,
        "artifacts": [
            {"path": str(path.relative_to(TARGET)), "sha256": digest(path), "size_bytes": path.stat().st_size}
            for path in (behavior, resource, addon)
        ],
        "proof_boundary": "Synthetic protocol fixture; not a Bedrock candidate.",
    }
    write_json(fixture / "artifact-manifest.json", manifest)
    fixture_commit, fixture_tree = commit("test: freeze synthetic mailbox fixture")

    candidate = base(
        "MSG-SYNTH-000001",
        "CANDIDATE_SUBMISSION",
        "SYNTHETIC_PACK_WORKER",
        "T1_SUPERVISOR",
        None,
        "VERIFY_AND_ROUTE_TO_TESTER",
        fixture_commit,
        fixture_tree,
        artifacts,
    )
    candidate.update(
        {
            "production_commit": fixture_commit,
            "production_tree": fixture_tree,
            "behavior_pack": {"path": str(behavior.relative_to(TARGET)), "sha256": artifacts["behavior_pack"]},
            "resource_pack": {"path": str(resource.relative_to(TARGET)), "sha256": artifacts["resource_pack"]},
            "mcaddon": {"path": str(addon.relative_to(TARGET)), "sha256": artifacts["mcaddon"]},
            "artifact_manifest": {
                "path": str((fixture / "artifact-manifest.json").relative_to(TARGET)),
                "sha256": digest(fixture / "artifact-manifest.json"),
            },
            "tests": {"executed": ["mailbox_fixture_hashes"], "passed": ["mailbox_fixture_hashes"], "failed": []},
        }
    )
    write_json(TARGET / "candidate_submissions" / "synthetic-mailbox-fixture" / "MSG-SYNTH-000001.json", candidate)
    intake = base(
        "MSG-SYNTH-000002",
        "TESTER_INTAKE",
        "T1_SUPERVISOR",
        "PERSISTENT_TESTER",
        "MSG-SYNTH-000001",
        "RUN_SYNTHETIC_PROTOCOL_VALIDATION_ONLY",
        fixture_commit,
        fixture_tree,
        artifacts,
    )
    write_json(TARGET / "tester_intake" / "synthetic-mailbox-fixture" / "MSG-SYNTH-000002.json", intake)
    intake_commit, intake_tree = commit("test: publish synthetic candidate and tester intake")

    result = base(
        "MSG-SYNTH-000003",
        "TEST_PASS",
        "PERSISTENT_TESTER",
        "T1_SUPERVISOR",
        "MSG-SYNTH-000002",
        "ROUTE_SYNTHETIC_ACCEPTANCE",
        intake_commit,
        intake_tree,
        artifacts,
    )
    result.update(
        {
            "result": "TEST_PASS",
            "candidate_hash": artifacts["mcaddon"],
            "findings": [],
            "qualification_receipts": [
                {
                    "receipt_id": "SYNTHETIC_PROTOCOL_RECEIPT",
                    "status": "PASS",
                    "bds_executed": False,
                }
            ],
        }
    )
    write_json(TARGET / "tester_results" / "synthetic-mailbox-fixture" / "MSG-SYNTH-000003.json", result)
    integration = base(
        "MSG-SYNTH-000004",
        "INTEGRATION_INTAKE",
        "T1_SUPERVISOR",
        "SHARED_RUNTIME_INTEGRATION_WORKER",
        "MSG-SYNTH-000003",
        "VALIDATE_SYNTHETIC_ROUTING_ONLY",
        intake_commit,
        intake_tree,
        artifacts,
    )
    write_json(TARGET / "integration_intake" / "synthetic-mailbox-fixture" / "MSG-SYNTH-000004.json", integration)
    result_commit, result_tree = commit("test: publish synthetic tester result and integration intake")

    final = base(
        "MSG-SYNTH-000005",
        "PACK_ACCEPTED_AND_INTEGRATED",
        "T1_SUPERVISOR",
        "SYNTHETIC_PACK_WORKER",
        "MSG-SYNTH-000004",
        "CLOSE_SYNTHETIC_ROUND_TRIP_ONLY",
        result_commit,
        result_tree,
        artifacts,
    )
    final.update(
        {
            "standalone_authority": {"commit": fixture_commit, "tree": fixture_tree},
            "integration_authority": {"commit": result_commit, "tree": result_tree},
            "final_classification": "SYNTHETIC_MAILBOX_ROUND_TRIP_ONLY",
        }
    )
    write_json(TARGET / "final_decisions" / "synthetic-mailbox-fixture" / "MSG-SYNTH-000005.json", final)
    final_commit, final_tree = commit("test: close synthetic mailbox round trip")

    runtime = TARGET / ".runtime"
    runtime.mkdir()
    write_json(
        runtime / "consumed.json",
        {
            "ignored_runtime_state": True,
            "consumed_message_ids": [
                "MSG-SYNTH-000001",
                "MSG-SYNTH-000002",
                "MSG-SYNTH-000003",
                "MSG-SYNTH-000004",
                "MSG-SYNTH-000005",
            ],
        },
    )
    if run("git", "status", "--porcelain"):
        raise SystemExit("mailbox worktree not clean after ignored cursor write")
    if run("git", "remote"):
        raise SystemExit("mailbox repository unexpectedly has remotes")

    receipt = {
        "schema_version": "1.0.0",
        "record_type": "synthetic_mailbox_round_trip_receipt",
        "mailbox_repository": str(TARGET),
        "ref": REGISTRY["mailbox_repository"]["ref"],
        "fixture_authority": {"commit": fixture_commit, "tree": fixture_tree},
        "candidate_and_intake_authority": {"commit": intake_commit, "tree": intake_tree},
        "result_and_integration_authority": {"commit": result_commit, "tree": result_tree},
        "final_authority": {"commit": final_commit, "tree": final_tree},
        "message_chain": [
            "MSG-SYNTH-000001",
            "MSG-SYNTH-000002",
            "MSG-SYNTH-000003",
            "MSG-SYNTH-000004",
            "MSG-SYNTH-000005",
        ],
        "artifact_hashes": artifacts,
        "consumption_state_ignored_by_git": True,
        "campaign_work_resumed": False,
        "bds_executed": False,
        "status": "PASS",
        "proof_boundary": "Append-only mailbox routing and consumption-cursor mechanics only.",
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
