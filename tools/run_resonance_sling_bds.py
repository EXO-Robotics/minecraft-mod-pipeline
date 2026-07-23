#!/usr/bin/env python3
"""Run isolated stable-BDS boot/restart qualification for the Resonance Sling package."""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from mccompiler.runtime.bds import BDSConsoleProbe, BDSLogProbe, BDSRunRequest, run_bds_diagnostic

ROOT=Path(__file__).resolve().parents[1]
WORLD=ROOT/"production/features/resonance-sling/dist/resonance-sling-INTERNAL-TEST.mcworld"
RUNTIME=ROOT/"production/features/resonance-sling/runtime"
IMAGE="itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39"

def run(restarts:int=3)->dict[str,object]:
    root=RUNTIME/"stable-bds"
    if root.exists(): shutil.rmtree(root)
    probes=tuple(BDSLogProbe(check_id=f"stable-init-{cycle}",cycle=cycle,expect_output="[resonance-sling] script runtime initialized stable_api=2.0.0",classification="bds_restart_diagnostic") for cycle in range(1,restarts+1))
    seed=RUNTIME/"stable-server-seed"
    seed_arg=seed if (seed/"bedrock_server-1.26.33.2").is_file() else None
    result=run_bds_diagnostic(BDSRunRequest(image=IMAGE,mcworld=WORLD,run_root=root,timeout_seconds=180,boot_grace_seconds=15,network_mode="bridge",bds_version="1.26.33.2",preview_channel=False,restart_count=restarts,log_probes=probes,server_seed_root=seed_arg))
    (RUNTIME/"stable-bds-result.json").parent.mkdir(parents=True,exist_ok=True)
    (RUNTIME/"stable-bds-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    data=root/"data"
    if data.is_dir() and (data/"bedrock_server-1.26.33.2").is_file():
        if seed.exists(): shutil.rmtree(seed)
        shutil.copytree(data,seed,ignore=shutil.ignore_patterns("worlds","logs","*.log"))
    shutil.rmtree(root/"data",ignore_errors=True)
    return result

def run_preview()->dict[str,object]:
    contract=json.loads((ROOT/"production/features/resonance-sling/diagnostic/preview-simulated-player/probes.json").read_text())
    root=RUNTIME/"preview-simulated-player"
    if root.exists(): shutil.rmtree(root)
    console=tuple(BDSConsoleProbe(check_id=row["check_id"],cycle=row["cycle"],after_boot_seconds=row["after_boot_seconds"],command=row["command"],expect_output=row["expect_output"]) for row in contract["console_probes"])
    logs=tuple([
        *(BDSLogProbe(check_id=f"preview-{name.replace('_','-')}",cycle=1,expect_output=f"[resonance-sling:preview] {name}=passed",classification="simulated_player_integration") for name in contract["cycle_1_checks"]),
        *(BDSLogProbe(check_id=f"preview-restart-{name.replace('_','-')}",cycle=2,expect_output=f"[resonance-sling:preview] {name}=passed",classification="simulated_player_integration") for name in contract["cycle_2_checks"]),
    ])
    seed=RUNTIME/"preview-server-seed"
    seed_arg=seed if (seed/"bedrock_server-1.26.50.20").is_file() else None
    result=run_bds_diagnostic(BDSRunRequest(image=IMAGE,mcworld=RUNTIME/"preview-simulated-player.mcworld",run_root=root,timeout_seconds=240,boot_grace_seconds=90,network_mode="bridge",bds_version="1.26.50.20",preview_channel=True,restart_count=2,console_probes=console,log_probes=logs,server_seed_root=seed_arg))
    (RUNTIME/"preview-simulated-player-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    data=root/"data"
    if data.is_dir() and (data/"bedrock_server-1.26.50.20").is_file():
        if seed.exists(): shutil.rmtree(seed)
        shutil.copytree(data,seed,ignore=shutil.ignore_patterns("worlds","logs","*.log"))
    shutil.rmtree(root/"data",ignore_errors=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("channel",choices=["stable","preview"],default="stable",nargs="?");p.add_argument("--restarts",type=int,default=3);a=p.parse_args()
    out=run_preview() if a.channel=="preview" else run(a.restarts);print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out.get("passed") else 1)
