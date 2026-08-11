#!/usr/bin/env python3
"""Run bounded ecology checks and emit a deterministic evidence receipt."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REPORT = HERE / "WHISPERWOOD_ECOLOGY_VALIDATION_REPORT.json"
AUTHOR = HERE / "author_whisperwood_ecology.py"
TEST = HERE / "test_whisperwood_ecology.py"
IDS = {"ww_ecology_whisper_fern", "ww_ecology_lantern_bloom", "ww_ecology_mooncap", "ww_ecology_root_flower", "ww_ecology_glow_moss_floor", "ww_ecology_hollow_lily_margin", "ww_ecology_briar_vine", "ww_ecology_root_bark_cluster", "ww_ecology_hollow_wood_cave"}

def run(command):
    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(result.returncode)

def build_report():
    outputs = []
    for folder in ("features", "feature_rules"):
        for path in sorted((REPO / "behavior_pack" / folder).glob("ww_ecology_*.json")):
            if path.name.split(".", 1)[0] in IDS:
                outputs.append({"path": str(path.relative_to(REPO)), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {
        "schema": "aionbound.wave1.whisperwood.ecology_validation.v1",
        "status": "PASS",
        "checks": ["deterministic regeneration", "feature and rule identifier/filename closure", "custom block closure", "forest and placement filters", "density and iteration bounds", "forbidden content omission", "proxy proof-boundary declaration"],
        "counts": {"features": 9, "feature_rules": 9, "unit_tests": 7},
        "outputs": outputs,
        "proof_boundary": "STATIC_SOURCE_REGISTRATION_ONLY; NOT BDS, CLIENT, NATURAL DISTRIBUTION, EXACT TERRAIN LOCALITY, OR CANDIDATE PROOF",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    run([sys.executable, str(AUTHOR), "--check"])
    run([sys.executable, "-m", "unittest", str(TEST), "-v"])
    data = (json.dumps(build_report(), indent=2) + "\n").encode()
    if args.check:
        if not REPORT.exists() or REPORT.read_bytes() != data:
            print(json.dumps({"status": "FAIL", "report": str(REPORT.relative_to(REPO))}, indent=2))
            return 1
    else:
        REPORT.write_bytes(data)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "report": str(REPORT.relative_to(REPO))}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
