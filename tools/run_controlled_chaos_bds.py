#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from mccompiler.runtime.bds import BDSLogProbe, BDSRunRequest, run_bds_diagnostic


ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "benchmarks/controlled-chaos-integration/dist/controlled-chaos-qualification.mcworld"
RUNTIME = ROOT / "benchmarks/controlled-chaos-integration/runtime"
IMAGE = "itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39"
VERSIONS = {"stable": "1.26.33.2", "preview": "1.26.50.20"}


def run(channel: str) -> dict[str, object]:
    run_root = RUNTIME / f"{channel}-bds"
    if run_root.exists():
        shutil.rmtree(run_root)
    restarts = 3 if channel == "stable" else 1
    probes = tuple(
        BDSLogProbe(
            check_id=f"{channel}-runtime-cycle-{cycle}",
            cycle=cycle,
            expect_output=f"persistent_boot={cycle}",
            classification="bds_restart_diagnostic" if channel == "stable" else "preview_api_diagnostic",
        )
        for cycle in range(1, restarts + 1)
    )
    result = run_bds_diagnostic(BDSRunRequest(
        image=IMAGE,
        mcworld=WORLD,
        run_root=run_root,
        timeout_seconds=180,
        boot_grace_seconds=15,
        network_mode="bridge",
        bds_version=VERSIONS[channel],
        preview_channel=channel == "preview",
        restart_count=restarts,
        log_probes=probes,
    ))
    shutil.rmtree(run_root / "data", ignore_errors=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("channel", choices=sorted(VERSIONS))
    args = parser.parse_args()
    result = run(args.channel)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
