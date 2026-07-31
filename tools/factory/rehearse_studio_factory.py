#!/usr/bin/env python3
"""Run an offline synthetic worker/tester/repair cycle for a Studio factory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mccompiler.orchestration.dispatch import ThreadDispatchOutbox
from mccompiler.orchestration.overseer import POOL_LANES, OverseerRuntime
from mccompiler.orchestration.planner import write_factory_plan
from mccompiler.orchestration.store import OrchestrationStore


CAMPAIGN_ID = "studio-factory-synthetic-v1"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    os.replace(temporary, path)


def rehearse(factory_root: Path, source: Path) -> dict[str, Any]:
    factory_root = factory_root.expanduser().resolve()
    config_path = factory_root / "factory-config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("overseer_interface") != "CODEX_TASK":
        raise ValueError("factory is not configured for the Codex task overseer")

    campaign_root = factory_root / "campaigns" / CAMPAIGN_ID
    plan_path = write_factory_plan(
        source,
        campaign_root,
        inspection_authority="studio-synthetic-rehearsal",
        authorization_overrides={
            "STATIC_ANALYSIS_AUTHORIZED": {
                "status": "PERMITTED_FOR_PRIVATE_TECHNICAL_EVALUATION",
                "authority": "studio-synthetic-rehearsal",
            },
            "ABSTRACT_BEHAVIOR_EXTRACTION_AUTHORIZED": {
                "status": "PERMITTED_FOR_PRIVATE_TECHNICAL_EVALUATION",
                "authority": "studio-synthetic-rehearsal",
            },
            "PRIVATE_REIMPLEMENTATION_AUTHORIZED": {
                "status": "PERMITTED_FOR_PRIVATE_TECHNICAL_EVALUATION",
                "authority": "studio-synthetic-rehearsal",
            },
            "PRODUCTION_AUTHORIZED": {
                "status": "PERMITTED_FOR_PRIVATE_TECHNICAL_EVALUATION",
                "authority": "studio-synthetic-rehearsal",
            },
        },
    )
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if not plan["intake"]["units"]:
        raise ValueError("synthetic rehearsal source must contain at least one JAR or ZIP")

    unit = plan["intake"]["units"][0]
    pack_id = f"synthetic-{unit['unit_id'][-12:]}"
    store = OrchestrationStore(config["queue_database"])
    store.initialize()
    store.create_campaign(
        campaign_id=CAMPAIGN_ID,
        name="Studio factory synthetic rehearsal",
        kind="JAVA_TO_BEDROCK",
        metadata={
            "plan_id": plan["plan_id"],
            "source_tree_sha256": plan["intake"]["source"]["tree_sha256"],
            "synthetic": True,
        },
    )

    submission = store.append_message(
        campaign_id=CAMPAIGN_ID,
        pack_id=pack_id,
        message_type="CANDIDATE_SUBMISSION",
        sender_role="synthetic_feature_producer",
        recipient_role="t1_preflight_tester",
        candidate_generation=1,
        payload={"local_validation": "PASS", "downstream_pass_required": False},
        idempotency_key=f"{CAMPAIGN_ID}:{pack_id}:candidate-submission:g1",
    )
    candidate_one = store.publish_candidate(
        campaign_id=CAMPAIGN_ID,
        pack_id=pack_id,
        generation=1,
        payload={"synthetic_artifact_sha256": hashlib.sha256(b"generation-one").hexdigest()},
        idempotency_key=f"{CAMPAIGN_ID}:{pack_id}:candidate:g1",
        source_message_id=submission["message_id"],
    )
    failed = store.append_message(
        campaign_id=CAMPAIGN_ID,
        pack_id=pack_id,
        message_type="TEST_FAIL_PRODUCT",
        sender_role="t1_preflight_tester",
        recipient_role="factory_router",
        candidate_generation=1,
        parent_message_id=submission["message_id"],
        payload={"stop_code": "PUBLICATION_INTEGRITY_FAILURE", "consolidated": True},
        idempotency_key=f"{CAMPAIGN_ID}:{pack_id}:t1-fail:g1",
    )
    repair = store.append_message(
        campaign_id=CAMPAIGN_ID,
        pack_id=pack_id,
        message_type="REPAIR_REQUIRED",
        sender_role="factory_router",
        recipient_role="synthetic_feature_producer",
        candidate_generation=2,
        parent_message_id=failed["message_id"],
        payload={
            "rejected_generation": 1,
            "required_replacement_generation": 2,
            "one_authoritative_consolidated_message": True,
        },
        idempotency_key=f"{CAMPAIGN_ID}:{pack_id}:repair:g1",
    )
    candidate_two = store.publish_repair_candidate(
        campaign_id=CAMPAIGN_ID,
        pack_id=pack_id,
        rejected_generation=1,
        payload={
            "synthetic_artifact_sha256": hashlib.sha256(b"generation-two-material-change").hexdigest(),
            "repair_message_id": repair["message_id"],
        },
        idempotency_key=f"{CAMPAIGN_ID}:{pack_id}:candidate:g2",
        source_message_id=repair["message_id"],
    )
    result_messages = []
    for message_type, sender in (
        ("T1_PASS", "t1_preflight_tester"),
        ("BDS_PASS", "bds_tester"),
        ("T10_PASS", "independent_auditor"),
    ):
        result_messages.append(
            store.append_message(
                campaign_id=CAMPAIGN_ID,
                pack_id=pack_id,
                message_type=message_type,
                sender_role=sender,
                recipient_role="factory_router",
                candidate_generation=2,
                parent_message_id=repair["message_id"],
                payload={"status": "PASS", "candidate_id": candidate_two["candidate_id"]},
                idempotency_key=f"{CAMPAIGN_ID}:{pack_id}:{message_type.lower()}:g2",
            )
        )

    assignment_path = campaign_root / "synthetic-assignment.json"
    activation_path = campaign_root / "synthetic-activation.json"
    if not assignment_path.exists():
        atomic_json(
            assignment_path,
            {"assignment_id": f"synthetic-{pack_id}", "unit_id": unit["unit_id"]},
        )
    if not activation_path.exists():
        atomic_json(
            activation_path,
            {
                "activation_type": "REPAIR_REQUIRED",
                "rejected_generation": 1,
                "next_generation": 2,
                "completion": "CANDIDATE_SUBMITTED",
            },
        )
    outbox = ThreadDispatchOutbox(factory_root / "runtime" / "dispatch" / "synthetic")
    dispatch = outbox.enqueue(
        campaign_id=CAMPAIGN_ID,
        assignment_id=f"synthetic-{pack_id}",
        role="feature_producer",
        skill="launch-cleanroom-production-worker",
        lane="PRODUCTION",
        assignment_path=assignment_path,
        activation_path=activation_path,
    )
    if dispatch["state"] == "PENDING_SEND":
        dispatch = outbox.acknowledge(
            dispatch["request_id"],
            state="ACKNOWLEDGED",
            worker_task_id="synthetic-rehearsal-worker",
        )

    runtime = OverseerRuntime(
        store,
        runtime_root=factory_root / "runtime" / "synthetic-overseer",
        pool_concurrency={name: 1 for name in POOL_LANES},
        reconciliation_interval_seconds=0.02,
    )
    runtime.start()
    deadline = time.monotonic() + 2
    while runtime.snapshot(CAMPAIGN_ID)["reconciliation"]["cycles"] < 1:
        if time.monotonic() > deadline:
            runtime.stop(timeout=2)
            raise RuntimeError("overseer reconciliation did not start")
        time.sleep(0.01)
    if not runtime.stop(timeout=2):
        raise RuntimeError("overseer role pools did not drain")

    receipt: dict[str, Any] = {
        "schema_version": "studio-factory-synthetic-rehearsal-v1",
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "plan_id": plan["plan_id"],
        "pack_id": pack_id,
        "overseer_interface": "CODEX_TASK",
        "ui_created": False,
        "pools": {name: sorted(lanes) for name, lanes in POOL_LANES.items()},
        "candidate_generations": [candidate_one["generation"], candidate_two["generation"]],
        "rejected_generation_preserved": True,
        "repair_bound_to_message": repair["message_id"],
        "downstream_results": [row["message_type"] for row in result_messages],
        "dispatch_state": dispatch["state"],
        "dispatch_request_id": dispatch["request_id"],
        "mailbox_message_count": len(store.list_messages(campaign_id=CAMPAIGN_ID)),
        "candidate_count": len(store.list_candidates(campaign_id=CAMPAIGN_ID)),
    }
    receipt["receipt_sha256"] = hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    receipt_path = factory_root / "runtime" / "receipts" / "synthetic-rehearsal.json"
    if receipt_path.exists():
        observed = json.loads(receipt_path.read_text(encoding="utf-8"))
        if observed != receipt:
            raise RuntimeError("existing synthetic rehearsal receipt does not match replay")
    else:
        atomic_json(receipt_path, receipt)

    config["activation_allowed"] = True
    config["activation_requirement"] = "SATISFIED_BY_SYNTHETIC_REHEARSAL"
    config["synthetic_rehearsal"] = {
        "receipt": str(receipt_path),
        "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "status": "PASS",
    }
    atomic_json(config_path, config)
    return {"receipt": str(receipt_path), **receipt}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--factory-root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = rehearse(args.factory_root, args.source)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
