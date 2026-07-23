#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mccompiler.runtime.bds import BDSConsoleProbe, BDSRunRequest, run_bds_diagnostic
from mccompiler.world import generate_test_world


ASSET = ROOT / "prototypes/blockbench/bramblehorn"
ADDON = ASSET / "addon"
QUALIFICATION = ASSET / "qualification"
WORLD = QUALIFICATION / "bramblehorn-stable-bds.mcworld"
RUN_ROOT = QUALIFICATION / "stable-bds"
IMAGE = "itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39"


def run() -> dict[str, Any]:
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    generate_test_world(
        ADDON / "behavior_pack",
        ADDON / "resource_pack",
        WORLD,
        world_name="Bramblehorn Stable BDS",
    )
    shutil.rmtree(RUN_ROOT, ignore_errors=True)
    probes = (
        BDSConsoleProbe("load-chunk", 1, 1, "tickingarea add circle 0 70 0 1 bramble true", "Added"),
        BDSConsoleProbe("summon-single", 1, 2, "summon ccoriginal_cc:bramblehorn 0 70 0", "successfully summoned"),
        BDSConsoleProbe("find-single", 1, 4, "testfor @e[type=ccoriginal_cc:bramblehorn,c=1]", "Found"),
        BDSConsoleProbe("stress-twenty", 1, 6, "function ccoriginal_cc/bramblehorn/stress", "Successfully executed"),
        BDSConsoleProbe("find-twenty", 1, 8, "testfor @e[type=ccoriginal_cc:bramblehorn,c=20]", "Found"),
        BDSConsoleProbe("cleanup", 1, 10, "function ccoriginal_cc/bramblehorn/cleanup", "Successfully executed"),
        BDSConsoleProbe("restart-stress", 2, 2, "function ccoriginal_cc/bramblehorn/stress", "Successfully executed"),
        BDSConsoleProbe("restart-find", 2, 4, "testfor @e[type=ccoriginal_cc:bramblehorn,c=20]", "Found"),
        BDSConsoleProbe("restart-cleanup", 2, 6, "function ccoriginal_cc/bramblehorn/cleanup", "Successfully executed"),
    )
    result = run_bds_diagnostic(BDSRunRequest(
        image=IMAGE,
        mcworld=WORLD,
        run_root=RUN_ROOT,
        timeout_seconds=180,
        boot_grace_seconds=20,
        network_mode="bridge",
        bds_version="1.26.33.2",
        restart_count=2,
        console_probes=probes,
    ))
    receipt = {
        "schema_version": "1.0.0",
        "classification": "STABLE_BDS_ENTITY_AND_STRESS_QUALIFICATION",
        "status": "PASSED" if result["passed"] else "FAILED",
        "bds_version": "1.26.33.2",
        "restart_cycles": 2,
        "stress_entity_count": 20,
        "world_sha256": hashlib.sha256(WORLD.read_bytes()).hexdigest(),
        "package_sha256": hashlib.sha256((ADDON / "bramblehorn_animated.mcaddon").read_bytes()).hexdigest(),
        "result": result,
        "claims": {"client_rendering_verified": False, "physical_ps4_verified": False},
    }
    (QUALIFICATION / "stable-bds-result.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.rmtree(RUN_ROOT / "data", ignore_errors=True)
    return receipt


if __name__ == "__main__":
    value = run()
    print(json.dumps(value, indent=2, sort_keys=True))
    raise SystemExit(0 if value["status"] == "PASSED" else 1)
