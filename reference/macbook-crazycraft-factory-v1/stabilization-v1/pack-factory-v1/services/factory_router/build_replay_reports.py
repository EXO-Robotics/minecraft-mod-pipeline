#!/usr/bin/env python3
"""Build deterministic read-only router replay reports from mailbox authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import factory_router as router


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head", required=True)
    parser.add_argument("--cursor", required=True)
    parser.add_argument("--recovery-anchor", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    config = router.config_from(root / "factory-router-config.json")
    # The committed config is installation-relative to the authoritative
    # supervisor checkout. Report construction must bind this exact worktree's
    # reviewed ledger before the branch is promoted.
    config["compatibility_ledger"] = str(
        root / "ROUTER_LEGACY_COMPATIBILITY_LEDGER.json"
    )
    _, current_report = router.replay_state(
        config,
        head=args.head,
        recovery_anchor=args.recovery_anchor,
        cursor=args.cursor,
    )
    _, full_report = router.replay_state(
        config,
        head=args.head,
        recovery_anchor=args.recovery_anchor,
    )
    current_hash = current_report["projection_sha256"]
    full_hash = full_report["projection_sha256"]
    if current_hash != full_hash or current_report["projection"] != full_report[
        "projection"
    ]:
        raise router.RouterError("current-cursor and full-history projections differ")
    write_json(root / "CURRENT_CURSOR_REPLAY_REPORT.json", current_report)
    write_json(root / "FULL_HISTORY_REPLAY_REPORT.json", full_report)
    write_json(
        root / "ROUTER_REPLAY_EQUIVALENCE_REPORT.json",
        {
            "schema_version": "crazycraft-router-replay-equivalence-v1",
            "result": "PASS",
            "mailbox_head": args.head,
            "current_cursor": args.cursor,
            "recovery_anchor": args.recovery_anchor,
            "current_cursor_projection_sha256": current_hash,
            "full_history_projection_sha256": full_hash,
            "projections_identical": True,
            "mailbox_history_rewritten": False,
            "semantic_actions_published": 0,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
