#!/usr/bin/env python3
"""Run the bounded structure lane checks and emit an evidence-derived receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
AUTHOR = HERE / "author_whisperwood_structures.py"
TEST = HERE / "test_whisperwood_structure_assemblies.py"
REPORT = HERE / "WHISPERWOOD_STRUCTURE_VALIDATION_REPORT.json"


def run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report() -> dict:
    outputs = []
    for folder, suffix in (("structures/aionbound", ".mcstructure"), ("features", ".structure_feature.json"), ("feature_rules", ".structure_feature_rule.json")):
        for path in sorted((REPO / "behavior_pack" / folder).glob(f"*{suffix}")):
            if path.stem.split(".", 1)[0] not in {
                "hunter_camp", "broken_wagon", "root_bridge", "owl_shrine",
                "forest_waystone", "hollow_cave_entrance", "ancient_totem", "fallen_giant_tree",
            }:
                continue
            outputs.append({"path": str(path.relative_to(REPO)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    return {
        "schema": "aionbound.wave1.whisperwood.structure_validation.v1",
        "status": "PASS",
        "checks": [
            "committed-output deterministic regeneration",
            "little-endian NBT full decode without trailing bytes",
            "palette and primary/secondary index closure",
            "structure dimensions and occupied-coordinate bounds",
            "inert anchor coordinate and expected-block closure",
            "custom block identifier closure",
            "feature, feature-rule, structure-name, and filename closure",
            "one-iteration conservative scatter policy",
            "direct custom prop omission",
            "unratified loot and reward binding omission",
        ],
        "commands": [
            "python3 engineering/whisperwood-intake/structure-assemblies/author_whisperwood_structures.py --check",
            "python3 -m unittest engineering/whisperwood-intake/structure-assemblies/test_whisperwood_structure_assemblies.py -v",
        ],
        "counts": {"assemblies": 8, "structure_files": 8, "features": 8, "feature_rules": 8, "unit_tests": 7},
        "outputs": outputs,
        "proof_boundary": "STATIC_SOURCE_AND_AUTHORED_BYTES_ONLY; NOT BDS, CLIENT, TERRAIN-AFFINITY, LOOT, RUNTIME, OR CANDIDATE PROOF",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    run([sys.executable, str(AUTHOR), "--check"])
    run([sys.executable, "-m", "unittest", str(TEST), "-v"])
    encoded = (json.dumps(build_report(), indent=2) + "\n").encode()
    if args.check:
        if not REPORT.exists() or REPORT.read_bytes() != encoded:
            print(json.dumps({"status": "FAIL", "report": str(REPORT.relative_to(REPO))}, indent=2))
            return 1
    else:
        REPORT.write_bytes(encoded)
    print(json.dumps({"status": "PASS", "report": str(REPORT.relative_to(REPO)), "mode": "check" if args.check else "write"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
