#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from mccompiler.runtime.bds import BDSLogProbe, BDSRunRequest, run_bds_diagnostic
from mccompiler.runtime.bds import BDSConsoleProbe


ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "benchmarks/controlled-chaos-integration/dist/controlled-chaos-qualification.mcworld"
RUNTIME = ROOT / "benchmarks/controlled-chaos-integration/runtime"
IMAGE = "itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39"
VERSIONS = {"stable": "1.26.33.2", "preview": "1.26.50.20"}


def _tree_receipt(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    size = 0
    files = 0
    if path.exists():
        for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
            relative = item.relative_to(path).as_posix().encode()
            payload = item.read_bytes()
            digest.update(relative + b"\0" + payload)
            size += len(payload)
            files += 1
    return {"sha256": digest.hexdigest(), "size_bytes": size, "file_count": files}


def _stamp_result(result: dict[str, object], run_root: Path, started: datetime, finished: datetime) -> None:
    log = result.get("log")
    if isinstance(log, dict) and isinstance(log.get("path"), str):
        log_path = Path(log["path"])
        normalized = "\n".join(line.rstrip() for line in log_path.read_text(encoding="utf-8").splitlines()) + "\n"
        log_path.write_text(normalized, encoding="utf-8")
        log["sha256"] = hashlib.sha256(normalized.encode()).hexdigest()
    worlds = run_root / "data/worlds"
    result["receipt"] = {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_seconds": round((finished - started).total_seconds(), 3),
        "post_run_world_state": _tree_receipt(worlds),
    }
    (run_root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    started = datetime.now(timezone.utc)
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
    _stamp_result(result, run_root, started, datetime.now(timezone.utc))
    shutil.rmtree(run_root / "data", ignore_errors=True)
    return result


def run_preview_qualification() -> dict[str, object]:
    from build_controlled_chaos_preview_diagnostic import build

    build()
    contract = json.loads(
        (ROOT / "benchmarks/controlled-chaos-integration/diagnostic/server-qualification/probes.json")
        .read_text(encoding="utf-8")
    )
    world_path = RUNTIME / "preview-server-qualification.mcworld"
    run_root = RUNTIME / "preview-server-qualification"
    if run_root.exists():
        shutil.rmtree(run_root)
    console = tuple(BDSConsoleProbe(
        check_id=str(row["check_id"]),
        cycle=int(row["cycle"]),
        after_boot_seconds=float(row["after_boot_seconds"]),
        command=str(row["command"]),
        expect_output=str(row["expect_output"]),
    ) for row in contract["console_probes"])
    logs = tuple([
        *(BDSLogProbe(
            check_id=f"preview-{check.replace('_', '-')}",
            cycle=1,
            expect_output=f"[controlled-chaos:server-qualification] {check}=passed",
            classification="simulated_player_integration",
        ) for check in contract["required_log_checks"]),
        *(BDSLogProbe(
            check_id=f"preview-restart-{check.replace('_', '-')}",
            cycle=2,
            expect_output=f"[controlled-chaos:server-qualification] {check}=passed",
            classification="bds_restart_diagnostic",
        ) for check in contract["restart_log_checks"]),
    ])
    started = datetime.now(timezone.utc)
    result = run_bds_diagnostic(BDSRunRequest(
        image=IMAGE,
        mcworld=world_path,
        run_root=run_root,
        timeout_seconds=240,
        boot_grace_seconds=28,
        network_mode="bridge",
        bds_version=VERSIONS["preview"],
        preview_channel=True,
        restart_count=2,
        console_probes=console,
        log_probes=logs,
    ))
    _stamp_result(result, run_root, started, datetime.now(timezone.utc))
    shutil.rmtree(run_root / "data", ignore_errors=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("channel", choices=[*sorted(VERSIONS), "preview-qualification"])
    args = parser.parse_args()
    result = run_preview_qualification() if args.channel == "preview-qualification" else run(args.channel)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
