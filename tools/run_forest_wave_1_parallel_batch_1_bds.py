#!/usr/bin/env python3
"""Run Stable and Preview BDS qualification for Forest Wave 1 parallel batch 1."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from mccompiler.runtime.bds import (
    BDSConsoleProbe,
    BDSLogProbe,
    BDSRunRequest,
    run_bds_diagnostic,
)


ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "production/batches/forest-wave-1-parallel-batch-1"
REPORTS = BATCH / "reports"
RUNTIME = BATCH / "runtime"
IMAGE = "itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39"
SEED_BASE = ROOT / "production/features/resonance-sling/runtime"
VERSIONS = {"stable": "1.26.33.2", "preview": "1.26.50.20"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_report(name: str, result: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(canonical_json(result), encoding="utf-8")


def reset_run_root(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def remove_server_payload(path: Path) -> None:
    """Keep receipts and normalized logs, never another cached BDS installation."""
    shutil.rmtree(path / "data", ignore_errors=True)


def run_stable() -> dict[str, Any]:
    run_root = RUNTIME / "stable-bds"
    reset_run_root(run_root)
    expected = (
        "[resonance-sling] script runtime initialized stable_api=2.0.0",
        "[barkguard-charm] stable_api=2.0.0",
    )
    probes = tuple(
        BDSLogProbe(
            check_id=f"stable-{name}-cycle-{cycle}",
            cycle=cycle,
            expect_output=output,
            classification="bds_restart_diagnostic",
        )
        for cycle in range(1, 4)
        for name, output in (("resonance", expected[0]), ("barkguard", expected[1]))
    )
    try:
        result = run_bds_diagnostic(
            BDSRunRequest(
                image=IMAGE,
                mcworld=BATCH / "dist/forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcworld",
                run_root=run_root,
                timeout_seconds=180,
                boot_grace_seconds=20,
                network_mode="bridge",
                bds_version=VERSIONS["stable"],
                preview_channel=False,
                restart_count=3,
                log_probes=probes,
                server_seed_root=SEED_BASE / "stable-server-seed",
            )
        )
        write_report("stable-bds-result.json", result)
        return result
    finally:
        remove_server_payload(run_root)


def run_preview() -> dict[str, Any]:
    contract = json.loads(
        (BATCH / "diagnostic/preview-simulated-player/probes.json").read_text(encoding="utf-8")
    )
    run_root = RUNTIME / "preview-simulated-player"
    reset_run_root(run_root)
    console = tuple(
        BDSConsoleProbe(
            check_id=str(row["check_id"]),
            cycle=int(row["cycle"]),
            after_boot_seconds=float(row["after_boot_seconds"]),
            command=str(row["command"]),
            expect_output=str(row["expect_output"]),
        )
        for row in contract["console_probes"]
    )
    logs = tuple(
        [
            *(
                BDSLogProbe(
                    check_id=f"preview-{name.replace('_', '-')}",
                    cycle=1,
                    expect_output=f"[forest-batch-1:preview] {name}=passed",
                    classification="simulated_player_integration",
                )
                for name in contract["cycle_1_checks"]
            ),
            *(
                BDSLogProbe(
                    check_id=f"preview-restart-{name.replace('_', '-')}",
                    cycle=2,
                    expect_output=f"[forest-batch-1:preview] {name}=passed",
                    classification="simulated_player_integration",
                )
                for name in contract["cycle_2_checks"]
            ),
        ]
    )
    try:
        result = run_bds_diagnostic(
            BDSRunRequest(
                image=IMAGE,
                mcworld=RUNTIME / "preview-simulated-player.mcworld",
                run_root=run_root,
                timeout_seconds=240,
                boot_grace_seconds=90,
                network_mode="bridge",
                bds_version=VERSIONS["preview"],
                preview_channel=True,
                restart_count=2,
                console_probes=console,
                log_probes=logs,
                server_seed_root=SEED_BASE / "preview-server-seed",
            )
        )
        write_report("preview-simulated-player-result.json", result)
        return result
    finally:
        remove_server_payload(run_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("channel", choices=("stable", "preview", "all", "summary"))
    args = parser.parse_args()
    results: dict[str, Any] = {}
    if args.channel in {"stable", "all"}:
        results["stable"] = run_stable()
    if args.channel in {"preview", "all"}:
        results["preview"] = run_preview()
    if args.channel == "summary":
        integration = json.loads(
            (REPORTS / "integration-artifact-manifest.json").read_text(encoding="utf-8")
        )
        expected = {
            "stable": integration["artifacts"]["mcworld"]["sha256"],
            "preview": integration["preview_diagnostic"]["sha256"],
        }
        for channel, filename in (
            ("stable", "stable-bds-result.json"),
            ("preview", "preview-simulated-player-result.json"),
        ):
            result = json.loads((REPORTS / filename).read_text(encoding="utf-8"))
            if result["artifact"]["sha256"] != expected[channel]:
                raise ValueError(
                    f"{channel} BDS receipt does not match current artifact: "
                    f"{result['artifact']['sha256']} != {expected[channel]}"
                )
            results[channel] = result
    summary = {
        "schema_version": "1.0.0",
        "batch_id": "forest-wave-1-parallel-batch-1",
        "channels": {
            name: {
                "status": result["status"],
                "passed": result["passed"],
                "artifact_sha256": result["artifact"]["sha256"],
                "bds_version": result["runtime"]["requested_bds_version"],
            }
            for name, result in results.items()
        },
        "passed": bool(results) and all(bool(result["passed"]) for result in results.values()),
        "claims": {
            "physical_ps4_verified": False,
            "marketplace_approved": False,
            "creator_tools_executed": False,
        },
    }
    write_report("bds-qualification-summary.json", summary)
    print(canonical_json(summary), end="")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
