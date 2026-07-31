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
        Path(__file__).resolve().parents[2]
        / "reference/macbook-crazycraft-factory-v1/stabilization-v1/"
        "pack-factory-v1/mailboxes/schemas",
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
        "reference_factory": {
            "path": str(
                Path(__file__).resolve().parents[2]
                / "reference/macbook-crazycraft-factory-v1"
            ),
            "commit": "9a485501c8df628f04f87cc6ed007a0025405ca0",
            "authority": "REFERENCE_ONLY",
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
