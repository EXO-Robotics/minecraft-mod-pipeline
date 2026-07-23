#!/usr/bin/env python3
"""Run isolated stable-BDS boot/restart qualification for the Resonance Sling package."""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from mccompiler.runtime.bds import BDSLogProbe, BDSRunRequest, run_bds_diagnostic

ROOT=Path(__file__).resolve().parents[1]
WORLD=ROOT/"production/features/resonance-sling/dist/resonance-sling-INTERNAL-TEST.mcworld"
RUNTIME=ROOT/"production/features/resonance-sling/runtime"
IMAGE="itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39"

def run(restarts:int=3)->dict[str,object]:
    root=RUNTIME/"stable-bds"
    if root.exists(): shutil.rmtree(root)
    probes=tuple(BDSLogProbe(check_id=f"stable-init-{cycle}",cycle=cycle,expect_output="[resonance-sling] script runtime initialized stable_api=2.0.0",classification="bds_restart_diagnostic") for cycle in range(1,restarts+1))
    result=run_bds_diagnostic(BDSRunRequest(image=IMAGE,mcworld=WORLD,run_root=root,timeout_seconds=180,boot_grace_seconds=15,network_mode="bridge",bds_version="1.26.33.2",preview_channel=False,restart_count=restarts,log_probes=probes))
    (RUNTIME/"stable-bds-result.json").parent.mkdir(parents=True,exist_ok=True)
    (RUNTIME/"stable-bds-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    shutil.rmtree(root/"data",ignore_errors=True)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--restarts",type=int,default=3);a=p.parse_args()
    out=run(a.restarts);print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out.get("passed") else 1)
