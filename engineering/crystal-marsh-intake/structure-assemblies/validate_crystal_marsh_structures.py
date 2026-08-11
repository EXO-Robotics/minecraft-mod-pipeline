#!/usr/bin/env python3
"""Run bounded Crystal Marsh assembly checks and emit captured evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
AUTHOR = HERE / "author_crystal_marsh_structures.py"
TEST = HERE / "test_crystal_marsh_structure_assemblies.py"
REPORT = HERE / "CRYSTAL_MARSH_STRUCTURE_VALIDATION_REPORT.json"
IDS = {"flooded_dock", "ancient_boat", "marsh_broken_bridge", "pearl_cairn", "marsh_totem", "crystal_arch", "crystal_obelisk", "sunken_shrine", "ruined_observatory", "deep_pool_entrance"}


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
            if path.stem.split(".", 1)[0] in IDS:
                outputs.append({"path": str(path.relative_to(REPO)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = json.loads((HERE / "CRYSTAL_MARSH_STRUCTURE_ASSEMBLIES.json").read_text())
    anchor_count = sum(len(item["anchors"]) for item in manifest["assemblies"])
    return {
        "schema": "aionbound.wave1.crystal_marsh.structure_validation.v1",
        "status": "PASS",
        "integration_authority": {"commit": "583279583cc27422c3d2ac6db52ad8a5310ec7dc", "tree": "45e23d9303fae9a0b07ca23ee9bedea9bdb5b5bc"},
        "checks": [
            "committed-output deterministic regeneration",
            "little-endian NBT full decode without trailing bytes",
            "ten exact Packet 003 landmark identifiers with distinct sizes and hashes",
            "palette and block-index closure",
            "empty entities and empty block_position_data",
            "inert barrel lodestone lectern coordinate closure",
            "custom block identifier closure",
            "stable feature rule and structure-name reference closure",
            "overworld non-ocean swamp-or-river wetland proxy filters",
            "Crystal-specific distinct conservative denominators not copied from Whisperwood or Ashen",
            "packet native visual models excluded from assembly-byte inputs",
        ],
        "commands": [
            "python3 engineering/crystal-marsh-intake/structure-assemblies/author_crystal_marsh_structures.py --check",
            "python3 -m unittest engineering/crystal-marsh-intake/structure-assemblies/test_crystal_marsh_structure_assemblies.py -v",
        ],
        "counts": {"assemblies": len(manifest["assemblies"]), "structure_files": sum(item["path"].endswith(".mcstructure") for item in outputs), "features": sum(item["path"].endswith(".structure_feature.json") for item in outputs), "feature_rules": sum(item["path"].endswith(".structure_feature_rule.json") for item in outputs), "unit_tests": 7, "inert_anchors": anchor_count, "loot_bindings": 0, "encounter_bindings": 0},
        "outputs": outputs,
        "proof_boundary": "STATIC_SOURCE_AND_AUTHORED_BYTES_ONLY; NOT MCSTRUCTURE CLIENT LOAD, BDS, TERRAIN AFFINITY, LOOT, ENCOUNTER, OR CANDIDATE PROOF",
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
