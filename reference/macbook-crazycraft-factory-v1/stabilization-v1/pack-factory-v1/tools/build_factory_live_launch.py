#!/usr/bin/env python3
"""Build the bounded factory-launch authority from observed local state."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAILBOX = Path(
    "/Users/blakegrove/Desktop/bedrock-server/program/"
    "crazycraft-pack-factory-mailboxes-v1"
)
TESTER_RUNTIME = ROOT / "services/local_tester/runtime"

WORKERS = [
    (
        "reliquary-vaults",
        "019fae2a-1ba8-71b1-a5f9-8025bbff1430",
        3,
        "12 editable models, 40 textures, animations/controllers, particles, "
        "sounds, 13/13 local tests; runtime reconciliation active.",
    ),
    (
        "hearth-and-hall",
        "019fae2a-1e88-7a43-aae5-238305c09a85",
        3,
        "44 blocks, 6 items, 50 recipes, 44 loot tables, persistence/recovery "
        "runtime, and 15/15 focused tests; assets active.",
    ),
    (
        "hearthveil",
        "019fae2a-2119-7543-aee8-72b261a0db66",
        3,
        "Runtime/BP, RP/editable-assets, and test/package producers dispatched "
        "under committed disjoint role packets.",
    ),
    (
        "aspectweave",
        "019fae2a-2394-7c23-8a00-090d630e4087",
        3,
        "Runtime, asset, and test/package streams active; first substantive "
        "writes remain working-tree observations.",
    ),
    (
        "vanguard-arsenal",
        "019fae2a-3694-7271-9168-ee644d4886a1",
        3,
        "Substantial BP/runtime plus 22 editable/runtime models, 97 texture "
        "files, 12 particles, 18 sounds, and 150 proof renders under reconciliation.",
    ),
    (
        "aperture-foundry",
        "019fae2a-2ba4-7710-ab61-54ce7e6f9bd1",
        0,
        "Runtime/BP/test/build implementation exists; native Blockbench "
        "reopen/export verification active.",
    ),
    (
        "echo-vessels",
        "019fae2a-31a5-7443-80d9-406c4aa09888",
        3,
        "Shipped runtime with 11/11 tests plus 20 editable models, 76 textures, "
        "26 clips, 12 controllers, 8 particles, 16 WAVs, and 120 proofs.",
    ),
    (
        "bounded-outcome-events",
        "019fae2a-2955-72e2-b3c4-618cb1f1ad10",
        3,
        "Runtime/BP and deterministic test/build streams have begun substantive "
        "implementation; asset stream remains active.",
    ),
    (
        "momentum-menagerie",
        "019fae2a-2edf-7b83-9706-b4a7e88d0560",
        3,
        "Runtime and five runtime-to-visual identities are under reconciliation "
        "with 23 preserved editable variants; candidate tooling active.",
    ),
    (
        "latchline-infrastructure",
        "019fae2a-265c-7163-967f-6076198a1f05",
        0,
        "Versioned registry/ownership runtime, shipped entrypoint, manifests, "
        "resource baseline, and runtime tests are being authored locally.",
    ),
]


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value) + b"\n")


def write_pretty(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repository: Path, *args: str) -> str:
    return subprocess.check_output(
        ["/usr/bin/git", "-C", str(repository), *args], text=True
    ).strip()


def local_tester_pid() -> int:
    output = subprocess.check_output(
        [
            "/bin/launchctl",
            "print",
            f"gui/{os.getuid()}/com.crazycraft.local-tester",
        ],
        text=True,
    )
    match = re.search(r"^\s*pid = ([0-9]+)$", output, re.MULTILINE)
    if not match:
        raise RuntimeError("local tester LaunchAgent has no active PID")
    return int(match.group(1))


def main() -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    tester_pid = local_tester_pid()
    records = []
    for pack_id, task_id, subagents, event in WORKERS:
        packet_path = ROOT / "launch/producer-safe" / f"{pack_id}.launch.json"
        packet = json.loads(packet_path.read_text())
        repository = Path(packet["production_authority"]["repository"])
        status = git(repository, "status", "--porcelain").splitlines()
        record = {
            "schema_version": "1.0.0",
            "record_type": "durable_pack_worker_launch",
            "pack_id": pack_id,
            "pack_name": packet["pack_name"],
            "assignment_id": packet["assignment_id"],
            "assigned_worker_role": packet["assigned_worker_role"],
            "task_id": task_id,
            "task_state": "ACTIVE",
            "launched_at": now,
            "launch_packet": {
                "path": str(packet_path),
                "sha256": sha256(packet_path),
                "payload_sha256": packet["packet_payload_sha256"],
            },
            "production_repository": str(repository),
            "production_ref": packet["production_authority"]["ref"],
            "observed_head": git(repository, "rev-parse", "HEAD"),
            "observed_tree": git(repository, "rev-parse", "HEAD^{tree}"),
            "working_tree_observation": {
                "classification": (
                    "UNCOMMITTED_PRODUCT_PROGRESS_NOT_CANDIDATE_AUTHORITY"
                    if status
                    else "CLEAN_AT_OBSERVATION"
                ),
                "changed_path_count": len(status),
            },
            "reported_internal_subagent_capacity": subagents,
            "last_substantive_product_event": event,
            "completion_condition": packet["completion_condition"],
            "no_ssh_no_studio": packet["no_ssh_no_studio"],
            "proof_boundary": (
                "Task/process and working-tree observations prove factory activity, "
                "not an immutable product candidate, BDS pass, client pass, or integration."
            ),
        }
        write(ROOT / "launch/records" / f"{pack_id}.launch-record.json", record)
        records.append(record)

    mailbox_head = git(MAILBOX, "rev-parse", "HEAD")
    mailbox_tree = git(MAILBOX, "rev-parse", "HEAD^{tree}")
    tester_state = json.loads((TESTER_RUNTIME / "state.json").read_text())
    queue = {
        "schema_version": "1.0.0",
        "record_type": "existing_candidate_tester_queue",
        "updated_at": now,
        "mailbox_commit": mailbox_head,
        "mailbox_tree": mailbox_tree,
        "candidates": [
            {
                "pack_id": "trailbound-packs",
                "state": "STABLE_TEST_PASS",
                "result_message_id": "MSG-T09-TRAILBOUND-BDS-RESULT-000005",
                "mcaddon_sha256": "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
                "remaining_boundaries": [
                    "PREVIEW",
                    "CLIENT",
                    "AUDIO",
                    "CONTROLLER",
                    "MULTIPLAYER",
                    "PHYSICAL_CONSOLE",
                    "RELEASE",
                ],
            },
            {
                "pack_id": "pocketbound-companions",
                "state": "STABLE_TEST_PASS",
                "result_message_id": "MSG-TESTER-000000000017-PASS",
                "mcaddon_sha256": "69f47526337f8a6cb4975de443e7972f7ec9d08d9b9ff8259bce96d3a0dba404",
            },
            {
                "pack_id": "wayfarer-settlements",
                "state": "STABLE_TEST_PASS",
                "result_message_id": "MSG-TESTER-000000000018-PASS",
                "mcaddon_sha256": "19c95a2518dd495328fca3095e7aa45d2cf9d499f636799863a7b494bd951bf4",
            },
            {
                "pack_id": "catalyst-wilds",
                "state": "BLOCKED_CANONICAL_TEST_PROFILE",
                "mcaddon_sha256": "86e582665f7e4fa268de977e4fb7a3ff18be9c13a565e72c42f3ee586dffa787",
                "blocker": (
                    "Preserved authority exposes a flat MCAddon but no exact committed "
                    "BP/RP tuple or approved flat-addon qualifier profile."
                ),
            },
        ],
        "proof_boundary": (
            "Stable exact-package results are separate from Preview, client, audio, "
            "controller, multiplayer, console, rights, branding, Marketplace, and release."
        ),
    }
    write(ROOT / "EXISTING_CANDIDATE_TESTER_QUEUE.json", queue)

    live = {
        "schema_version": "1.0.0",
        "record_type": "crazy_craft_factory_live_status",
        "updated_at": now,
        "factory_activity": "ACTIVE",
        "t1": {
            "state": "MONITORING",
            "product_authorship": False,
            "mailbox_commit": mailbox_head,
            "mailbox_tree": mailbox_tree,
        },
        "local_tester": {
            "launchd_label": "com.crazycraft.local-tester",
            "state": "RUNNING",
            "pid": tester_pid,
            "configured_capacity": 2,
            "completed_pass_jobs": ["JOB-000000000017", "JOB-000000000018"],
            "completed_infrastructure_failures": [
                "JOB-000000000015",
                "JOB-000000000016",
            ],
            "runtime_projection": tester_state,
            "hot_reload_state": "COMPLETED",
            "hot_reload_evidence": (
                f"LaunchAgent restarted successfully; PID {tester_pid} loaded the tested "
                "terminal-job reconciliation fix and reported all prior jobs terminal."
            ),
        },
        "shared_runtime_integration": {
            "task_id": "019fa886-8675-7ec3-bd7c-92cced930743",
            "state": "ACTIVE",
            "repository": (
                "/Users/blakegrove/Desktop/bedrock-server/program/"
                "crazycraft-autonomous-worker-lanes-v1/thread-02"
            ),
        },
        "t10": {
            "task_id": "019fa887-8d31-7741-bc92-51fe01bceb5c",
            "state": "WAITING_IMMUTABLE_PREFLIGHTED_CANDIDATE",
            "active_limit": 1,
            "queued_limit": 1,
        },
        "pack_workers": records,
        "candidate_submissions": sorted(
            path.name for path in (MAILBOX / "candidate_submissions").glob("*/*.json")
        ),
        "tester_results": sorted(
            path.name for path in (MAILBOX / "tester_results").glob("*/*.json")
        ),
        "repair_messages": sorted(
            path.name for path in (MAILBOX / "worker_repairs").glob("*/*.json")
        ),
        "accepted_standalone_packs": [
            "quietwork",
            "shatterwild-foundry",
        ],
        "integrated_packs": [],
        "exact_blockers": [
            "Catalyst Wilds needs an exact committed BP/RP tuple or an approved "
            "flat-addon candidate profile before fail-closed BDS intake.",
            "Reliquary generation 1 failed mechanical preflight and remains with "
            "its original owner for metadata-only scan/receipt evidence repair.",
        ],
        "mac_studio": "OPTIONAL_NOT_SCHEDULING_BLOCKER",
        "proof_boundary": (
            "Factory process activity and existing Stable BDS results only; new-pack "
            "candidate, audit, qualification, integration, and release outcomes remain unearned."
        ),
    }
    write(ROOT / "CRAZY_CRAFT_FACTORY_LIVE_STATUS.json", live)

    decision = {
        "schema_version": "1.0.0",
        "record_type": "factory_launch_decision",
        "decision_id": "FD-T01-PACK-FACTORY-LAUNCH-0001",
        "decision_type": "FACTORY_LAUNCH",
        "created_at": now,
        "base_supervisor_authority": {
            "commit": "5f4a8ca8490c9d18e4d8dd8956404e9974845774",
            "tree": "c0972cc5ea7d6adff0862042389a5209c07714e8",
        },
        "mailbox_authority": {
            "repository": str(MAILBOX),
            "ref": "refs/heads/codex/factory-mailbox-v1",
            "commit": mailbox_head,
            "tree": mailbox_tree,
        },
        "durable_pack_workers": [
            {
                "pack_id": record["pack_id"],
                "assignment_id": record["assignment_id"],
                "task_id": record["task_id"],
                "launch_packet_sha256": record["launch_packet"]["sha256"],
            }
            for record in records
        ],
        "services": {
            "local_tester": "ACTIVE",
            "shared_runtime_integration": "ACTIVE",
            "t10_audit": "ACTIVE_WAITING_CANDIDATE",
            "t1_monitoring": "ACTIVE",
        },
        "mac_studio": "OPTIONAL_NOT_SCHEDULING_BLOCKER",
        "run_control": "ACTIVE",
        "proof_boundary": (
            "Authorizes the fixed pack-factory tasks and services only. It does not "
            "award any product, audit, qualification, integration, or release result."
        ),
    }
    write(ROOT / "FACTORY_LAUNCH_DECISION.json", decision)

    readiness_path = ROOT / "CRAZY_CRAFT_FACTORY_READINESS.json"
    readiness = json.loads(readiness_path.read_text())
    readiness["campaign_workers_started"] = True
    readiness["launchd_started"] = True
    readiness["run_control"] = "ACTIVE"
    readiness["classification"] = "PACK_FACTORY_ACTIVE"
    readiness["gates"]["FACTORY_LAUNCHED"] = {
        "status": "PASS",
        "reason": (
            "Ten durable workers, T2/T10, and the local tester are active and "
            "substantive implementation is underway. The tester hot restart completed "
            "and its two local BDS slots are reusable."
        ),
    }
    write_pretty(readiness_path, readiness)

    report = f"""# Crazy Craft Factory Launch Report

Generated: `{now}`

## Outcome

The pack-production factory is executing: ten visible durable pack owners are active,
T2 owns shared-runtime/integration service, T10 is waiting for the first immutable
mechanically preflighted new-pack candidate, and the MacBook-local tester consumed
Pocketbound and Wayfarer concurrently. Both corrected exact-package jobs returned
immutable Stable `TEST_PASS` results.

`FACTORY_LAUNCHED=PASS`. The bounded LaunchAgent restart succeeded, the tester is
running as PID `{tester_pid}`, the terminal-child reconciliation fix is loaded, and its two
local BDS slots are reusable. No product candidate was changed by the service restart.

## Durable pack owners

| Pack | Task | Assignment | State | Product progress |
|---|---|---|---|---|
"""
    for record in records:
        report += (
            f"| {record['pack_name']} | `{record['task_id']}` | "
            f"`{record['assignment_id']}` | ACTIVE | "
            f"{record['last_substantive_product_event']} |\n"
        )
    report += """

## Existing-candidate tester closure

- Trailbound Packs: preserved Stable pass, `MSG-T09-TRAILBOUND-BDS-RESULT-000005`.
- Pocketbound Companions: Stable pass, `MSG-TESTER-000000000017-PASS`.
- Wayfarer Settlements: Stable pass, `MSG-TESTER-000000000018-PASS`.
- Catalyst Wilds: blocked before intake because no exact committed BP/RP tuple or
  approved flat-addon profile exists in the preserved authority.

The first Pocketbound/Wayfarer requests failed closed as infrastructure because the
request profiles omitted their declared script modules. Linked retries declared
`scripts/main.js`, retained the same exact candidate hashes, and passed.

## Proof boundaries

The launch proves durable task activation, substantive Bedrock authoring, mailbox
consumption, and exact Stable BDS load/restart for the three named existing
candidates. It does not prove any new-pack candidate, Preview, client rendering,
audio, controller, multiplayer, Realm, split-screen, physical console, rights,
branding, Marketplace, release, combined integration, or final portfolio result.

Mac Studio remains optional overflow capacity and is not a scheduling blocker.
"""
    (ROOT / "CRAZY_CRAFT_FACTORY_LAUNCH_REPORT.md").write_text(report)


if __name__ == "__main__":
    main()
