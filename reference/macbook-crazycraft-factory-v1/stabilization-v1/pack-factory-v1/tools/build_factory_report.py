#!/usr/bin/env python3
"""Build the exact paused-factory readiness matrix and organization report."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    pack_map = json.loads((ROOT / "CRAZY_CRAFT_FINAL_PACK_MAP.json").read_text())
    reconciliation = json.loads((ROOT / "CRAZY_CRAFT_SOURCE_TO_PACK_RECONCILIATION.json").read_text())
    repositories = json.loads((ROOT / "FACTORY_REPOSITORY_ALLOCATION_REGISTRY.json").read_text())
    budgets = json.loads((ROOT / "FACTORY_RUNTIME_PERFORMANCE_BUDGET_REGISTRY.json").read_text())
    validation = json.loads((ROOT / "FACTORY_VALIDATION_REPORT.json").read_text())
    route = json.loads((ROOT / "EXISTING_CANDIDATE_DOCKER_BDS_ROUTE_VERIFICATION.json").read_text())
    synthetic = json.loads((ROOT / "SYNTHETIC_MAILBOX_ROUND_TRIP_RECEIPT.json").read_text())

    checks = {row["check"]: row["status"] for row in validation["checks"]}
    gates = {
        "ALL_52_ARTIFACTS_RECONCILED": {"status": "PASS" if checks["all_52_artifacts_exact_once"] == "PASS" else "FAIL"},
        "FINAL_PACK_MAP_FROZEN": {"status": "PASS" if checks["pack_count_and_identity"] == "PASS" else "FAIL"},
        "EXISTING_PACK_AUTHORITIES_PRESERVED": {"status": "PASS" if checks["existing_authorities_preserved"] == "PASS" else "FAIL"},
        "EVERY_PACK_HAS_COMPLETE_SCOPE": {"status": "PASS" if checks["durable_assignment_packets"] == "PASS" else "FAIL"},
        "EVERY_PACK_HAS_ASSET_MANIFEST": {"status": "PASS" if checks["every_pack_asset_manifest"] == "PASS" else "FAIL"},
        "EVERY_PACK_HAS_NAMESPACE_AND_UUIDS": {
            "status": "PASS" if checks["namespace_collision_free"] == checks["uuid_collision_free"] == "PASS" else "FAIL"
        },
        "EVERY_PACK_HAS_PRODUCTION_REPOSITORY": {"status": "PASS" if checks["every_pack_production_repository"] == "PASS" else "FAIL"},
        "EVERY_PACK_HAS_RUNTIME_BUDGET": {"status": "PASS" if checks["combined_budget_within_ceiling"] == "PASS" else "FAIL"},
        "EVERY_PACK_HAS_DURABLE_OWNER": {"status": "PASS" if checks["durable_owner_unique"] == "PASS" else "FAIL"},
        "MAILBOX_SCHEMAS_READY": {"status": "PASS" if checks["mailbox_round_trip_schema_and_chain"] == "PASS" else "FAIL"},
        "MAILBOX_ROUND_TRIP_PROVEN": {
            "status": synthetic["status"],
            "receipt_sha256": digest(ROOT / "SYNTHETIC_MAILBOX_ROUND_TRIP_RECEIPT.json"),
        },
        "TESTER_ASSIGNMENT_READY": {"status": "PASS" if checks["persistent_service_assignments"] == "PASS" else "FAIL"},
        "DOCKER_BDS_ROUTE_PROVEN": {
            "status": "BLOCKED",
            "route_status": route["status"],
            "job_id": route["remote_job"]["job_id"],
            "receipt_sha256": route["remote_job"]["receipt_sha256"],
            "reason": route["exact_blocker"],
        },
        "INTEGRATION_ASSIGNMENT_READY": {"status": "PASS" if checks["persistent_service_assignments"] == "PASS" else "FAIL"},
        "T1_ROUTING_READY": {"status": "PASS" if checks["persistent_service_assignments"] == "PASS" else "FAIL"},
        "FACTORY_READY_TO_RESUME": {
            "status": "BLOCKED",
            "reason": "The exact-package tester reached the Studio Docker daemon with verified hashes, but the pinned image lacks the allowlisted BDS qualifier entrypoint; no pack worker may be restarted until that persistent service route executes.",
        },
    }
    readiness = {
        "schema_version": "1.0.0",
        "record_type": "crazy_craft_factory_readiness",
        "run_control": "PAUSED",
        "pack_count": len(pack_map["packs"]),
        "source_artifact_count": reconciliation["source_artifact_count"],
        "gates": gates,
        "classification": "PACK_FACTORY_STRUCTURALLY_READY_TESTER_EXECUTION_BLOCKED",
        "campaign_workers_started": False,
        "launchd_started": False,
        "proof_boundary": "Factory control authority and route validation only; no new pack, BDS pass, audit, integration, client, console, rights, or release claim.",
    }
    write_json(ROOT / "CRAZY_CRAFT_FACTORY_READINESS.json", readiness)

    repo_by_pack = {row["pack_id"]: row for row in repositories["pack_repositories"]}
    lines = [
        "# Crazy Craft fixed pack-production factory",
        "",
        "## Executive result",
        "",
        "The paused ten-section accounting model has been converted into **16 durable pack production units**. "
        "All 52 frozen source artifacts are assigned exactly once to a named pack, a shared-platform requirement, "
        "an existing authority, or a no-standalone disposition. No campaign worker was restarted and launchd remains stopped.",
        "",
        "The control structure is complete, but factory launch is **blocked** by one tester-service defect: the exact "
        "Trailbound tuple reached the Mac Studio, passed remote input hashing and disclosure checks, and invoked Docker, "
        "but the pinned image does not contain `/opt/crazycraft/bin/qualify-exact-package`. This is infrastructure failure, "
        "not a Trailbound defect; the candidate remains unchanged.",
        "",
        "## Final pack portfolio",
        "",
        "| # | Pack | Frozen source responsibility | State | Durable owner | Repository |",
        "|---:|---|---|---|---|---|",
    ]
    for pack in pack_map["packs"]:
        sources = ", ".join(Path(item).name.removesuffix(".jar") for item in pack["source_paths"]) or "Reference authority; no new 52-artifact claim"
        repository = repo_by_pack[pack["pack_id"]]
        lines.append(
            f"| {pack['pack_sequence']} | **{pack['name']}** (`{pack['pack_id']}`) | {sources} | "
            f"`{pack['lifecycle_classification']}` | `{pack['owner']}` | `{repository['path']}` |"
        )

    lines += [
        "",
        "## Shared-platform and no-standalone dispositions",
        "",
    ]
    for row in reconciliation["records"]:
        if row["final_target"].startswith(("shared-platform:", "no-standalone:")):
            lines.append(
                f"- `{Path(row['path']).name}` → `{row['final_target']}` (`{row['final_disposition']}`)."
            )

    lines += [
        "",
        "## Existing authorities preserved",
        "",
        "| Pack | Classification | Content or publication authority | MCAddon SHA-256 |",
        "|---|---|---|---|",
    ]
    for pack in pack_map["packs"]:
        authority = pack.get("existing_authority")
        if not authority:
            continue
        commit = authority.get("artifact_commit", authority["content_commit"])
        tree = (
            authority["metadata_tree"]
            if authority.get("artifact_commit")
            else authority["content_tree"]
        )
        addon = authority["artifacts"]["mcaddon"]
        lines.append(
            f"| {pack['name']} | `{pack['lifecycle_classification']}` | `{commit}` / "
            f"`{tree}` | `{addon['sha256']}` |"
        )

    lines += [
        "",
        "## Asset workload",
        "",
        "Every assignment includes all required asset classes: `HERO`, `REUSABLE_COMPLEX`, `ROUTINE_MODEL`, "
        "`ICON`, `PARTICLE`, `SOUND`, and `NOT_REQUIRED`. Planned packs carry explicit output counts for editable "
        "`.bbmodel` sources, models, textures, icons, animations, controllers, particles, sounds, UI, localization, "
        "and proof renders. Existing authorities are preserved and classified for closure rather than rebuilt.",
        "",
        "| Pack | Hero | Reusable | Routine | Icons | Particles | Sounds | Editable models |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pack in pack_map["packs"]:
        inventory = pack["asset_authority"]["inventory"]
        classes = inventory["class_counts"]
        editable = inventory.get("expected_outputs", {}).get(
            "editable_bbmodel_files", inventory.get("editable_bbmodel_files", 0)
        )
        lines.append(
            f"| {pack['name']} | {classes['HERO']} | {classes['REUSABLE_COMPLEX']} | "
            f"{classes['ROUTINE_MODEL']} | {classes['ICON']} | {classes['PARTICLE']} | "
            f"{classes['SOUND']} | {editable} |"
        )

    mailbox = repositories["mailbox_repository"]
    lines += [
        "",
        "## Mailboxes and durable services",
        "",
        f"- Mailbox repository: `{mailbox['path']}`",
        f"- Authority ref: `{mailbox['ref']}`",
        f"- Current commit/tree: `{mailbox['commit']}` / `{mailbox['tree']}`",
        "- Paths: `candidate_submissions/`, `tester_intake/`, `tester_results/`, `worker_repairs/`, "
        "`integration_intake/`, and `final_decisions/`.",
        "- Consumption state is ignored runtime data; immutable messages are never edited.",
        "- The initial synthetic-only mailbox attempt with noncanonical idempotency keys is preserved at "
        "`crazycraft-pack-factory-mailboxes-v1.quarantine-invalid-synthetic-v1` and is not authority.",
        "- Persistent tester assignment: `services/PERSISTENT_TESTER_ASSIGNMENT.json`.",
        "- Shared-runtime/integration assignment: `services/SHARED_RUNTIME_INTEGRATION_ASSIGNMENT.json`.",
        "- Pack consumers bind frozen Platform v1 commit `aba740f136dce5781e68d34e1c7aaa2a0a3d8671` / "
        "tree `2d5c123c9cbc6d4cdaac2ff922916450b5282d08`; the registered Thread 2 integration candidate "
        "`1230f8c7bb2e7d1699373c60c34f168f5ae66bc8` remains non-promoted.",
        "- T1 routing assignment: `services/T1_SUPERVISOR_MAILBOX_ROUTING_ASSIGNMENT.json`.",
        "",
        "The synthetic chain published candidate → tester intake → tester result → integration intake → final decision "
        "with exact parent IDs and a Git-ignored consumption cursor.",
        "",
        "## Runtime allocation",
        "",
        "The 16 pack reservation targets plus the shared-runtime reserve fit every frozen ceiling. These are integration "
        "targets, not retroactive proof that existing standalone candidates already meet them.",
        "",
        "| Budget | Pack total | Platform reserve | Combined | Ceiling |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in budgets["combined_target_check"].items():
        lines.append(
            f"| `{name}` | {row['pack_total']} | {row['platform_reserve']} | {row['combined']} | {row['ceiling']} |"
        )

    lines += [
        "",
        "## Real tester-route verification",
        "",
        f"- Studio job: `{route['remote_job']['job_id']}`",
        f"- Exact candidate: Trailbound `{route['candidate']['mcaddon_sha256']}`",
        f"- Receipt SHA-256: `{route['remote_job']['receipt_sha256']}`",
        "- Passed: mailbox routing, exact input hashes, Studio transfer, disclosure scan, Docker invocation, cleanup receipt.",
        "- Blocked: Stable BDS runtime because the pinned image lacks the allowlisted exact-package qualifier.",
        "- Candidate disposition: preserved unchanged; no product repair is authorized.",
        "",
        "## Readiness matrix",
        "",
        "| Gate | Result |",
        "|---|---|",
    ]
    for name, row in gates.items():
        lines.append(f"| `{name}` | **{row['status']}** |")

    lines += [
        "",
        "## Exact next action",
        "",
        "Repair or replace the digest-pinned tester image so it contains the allowlisted exact-package qualifier, "
        "then retry the unchanged Trailbound candidate through the existing tester intake. After that receipt proves "
        "the real Stable BDS path, regenerate only the readiness decision and perform the separate controlled factory launch.",
        "",
        "No pack worker, tester service, integration worker, audit worker, or qualification campaign is running as a result of this organization pass.",
    ]
    (ROOT / "CRAZY_CRAFT_FACTORY_ORGANIZATION_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
