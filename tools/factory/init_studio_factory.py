#!/usr/bin/env python3
"""Materialize an inert Studio-local factory control root and Git mailbox."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .init_studio_mailbox import initialize_mailbox
except ImportError:  # Direct script execution.
    from init_studio_mailbox import initialize_mailbox


def initialize_factory(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"factory root is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for relative in (
        "campaigns",
        "runtime/receipts",
        "runtime/logs",
        "runtime/dispatch",
        "production",
        "audit",
        "qualification",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    mailbox = initialize_mailbox(
        root / "mailbox",
        Path(__file__).resolve().parents[2] / "schemas" / "mailbox",
        "codex/studio-factory-mailbox-v1",
    )
    config: dict[str, object] = {
        "schema_version": "studio-java-to-bedrock-factory-v1",
        "root": str(root),
        "overseer_interface": "CODEX_TASK",
        "queue_database": str(root / "orchestration.sqlite3"),
        "runtime_root": str(root / "runtime"),
        "campaign_root": str(root / "campaigns"),
        "mailbox": mailbox,
        "distribution": {
            "kind": "PORTABLE_STANDALONE_FACTORY",
            "repository": str(Path(__file__).resolve().parents[2]),
        },
        "pools": {
            "task_maker": {"lanes": ["EVIDENCE", "CONTROL"], "concurrency": 2},
            "production_workers": {"lanes": ["PRODUCTION"], "concurrency": 2},
            "integration_worker": {"lanes": ["INTEGRATION"], "concurrency": 1},
            "tester_workers": {"lanes": ["QUALIFICATION"], "concurrency": 2},
            "audit_workers": {"lanes": ["AUDIT"], "concurrency": 1},
        },
        "adaptive_scaling": {
            "enabled": True,
            "wait_heartbeats_before_scale_up": 2,
            "idle_heartbeats_before_scale_down": 4,
            "actionable_statuses": ["READY"],
            "explicit_capacity_wait_field": "payload.capacity_blocked",
            "min_threads": {
                "task_maker": 1,
                "production_workers": 1,
                "integration_worker": 1,
                "tester_workers": 1,
                "audit_workers": 1,
            },
            "max_threads": {
                "task_maker": 4,
                "production_workers": 6,
                "integration_worker": 2,
                "tester_workers": 4,
                "audit_workers": 3,
            },
            "service_caps": {
                "STABLE_BDS": {
                    "execution_slots": 2,
                    "on_saturation": "BACKPRESSURE_PRODUCTION",
                }
            },
            "duplicate_spawn_policy": "ONE_OPEN_DIRECTIVE_PER_PACKET",
            "scale_down_policy": "IDLE_ONLY_NEVER_INTERRUPT_LEASED_WORK",
        },
        "automation_policy": {
            "routine_questions": "USE_PORTFOLIO_DEFAULTS",
            "candidate_publication_requires_downstream_pass": False,
            "preserve_failed_generations": True,
            "unchanged_candidate_retry": "FORBIDDEN",
            "automatic_repair_limit_per_pack": 3,
            "user_gates": [
                "RIGHTS_AND_OPERATION_AUTHORIZATION",
                "PUBLICATION_AUTHORIZATION",
                "RELEASE_AUTHORIZATION",
            ],
            "external_gates": [
                "DESKTOP_CLIENT",
                "CONTROLLER",
                "REALMS",
                "SPLIT_SCREEN",
                "PHYSICAL_PS4",
                "MARKETPLACE",
            ],
        },
        "platform_qualification": {
            "required_before_campaign_activation": True,
            "schema_version": "bedrock-factory.platform-qualification.v1.0.0",
            "receipt": str(root / "runtime" / "receipts" / "factory-platform-qualification.json"),
            "status": "NOT_QUALIFIED",
            "invalidate_on_component_hash_change": True,
        },
        "identity_namespaces": {
            "candidate": "C#",
            "activation": "A#",
            "repair_authority": "RA#",
            "t1_run": "T1-R#",
            "bds_run": "BDS-R#",
            "observation_run": "OBS-R#",
            "t10_run": "T10-R#",
            "integration_candidate": "I#",
        },
        "activation_allowed": False,
        "activation_requirement": (
            "Submit one hash-bound campaign request and pass the synthetic "
            "mailbox/worker/tester/repair rehearsal."
        ),
    }
    config_path = root / "factory-config.json"
    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"config": str(config_path), **config}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = initialize_factory(args.root)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
