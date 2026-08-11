#!/usr/bin/env python3
"""Validate the bounded direct-prop worldgen lane and write its receipt."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
AUTHOR = HERE / "author_direct_prop_worldgen.py"
TEST = HERE / "test_direct_prop_worldgen.py"
REPORT = HERE / "WHISPERWOOD_DIRECT_PROP_VALIDATION_REPORT.json"
IDS = ("ww_prop_lantern_post", "ww_prop_moss_cairn")

def run(command):
    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(result.returncode)

def build_report():
    rows = []
    for identifier in IDS:
        for relative in (f"behavior_pack/features/{identifier}.feature.json", f"behavior_pack/feature_rules/{identifier}.feature_rule.json"):
            path = REPO / relative
            rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {
        "schema": "aionbound.wave1.whisperwood.direct_prop_validation.v1",
        "status": "PASS",
        "checks": ["deterministic regeneration", "direct-prop block closure", "feature/rule identifier and target closure", "forest surface filters", "combined ecology density ceiling", "forbidden scope omission"],
        "counts": {"features": 2, "feature_rules": 2, "unit_tests": 7},
        "outputs": rows,
        "proof_boundary": "STATIC SOURCE REGISTRATION ONLY; NOT TRAIL OR HOLLOW DETECTION, BDS, CLIENT, NATURAL DISTRIBUTION, BUILD, OR CANDIDATE PROOF",
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
