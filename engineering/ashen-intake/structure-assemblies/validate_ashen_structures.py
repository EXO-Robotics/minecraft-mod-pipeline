#!/usr/bin/env python3
"""Run bounded Ashen assembly checks and emit an evidence-derived report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
AUTHOR = HERE / "author_ashen_structures.py"
TEST = HERE / "test_ashen_structure_assemblies.py"
REPORT = HERE / "ASHEN_STRUCTURE_VALIDATION_REPORT.json"
IDS = {"fire_totem", "burned_camp", "char_wagon", "broken_bridge", "basalt_arch", "ash_watchtower", "ancient_kiln", "ember_forge", "lava_shrine", "ash_cave"}


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
    return {
        "schema": "aionbound.wave1.ashen.structure_validation.v1",
        "status": "PASS",
        "integration_authority": {"commit": "fce314f2251f9e9eb0cb9a1c2b8310d90a8a7c6c", "tree": "c059ca23dadb7d19ac471848e910bfd28a55caa5"},
        "checks": [
            "committed-output deterministic regeneration",
            "little-endian NBT full decode without trailing bytes",
            "ten distinct assembly hashes, sizes, identifiers, and anchor identifiers",
            "palette/index closure and occupied-coordinate bounds",
            "inert barrel/lodestone/lectern anchor coordinate closure",
            "empty block_position_data and no LootTable NBT",
            "custom block identifier closure",
            "stable feature/rule/structure-name/filename reference closure",
            "overworld non-ocean mountain-or-mesa proxy filters",
            "Ashen-specific distinct rarity denominators not copied from Whisperwood",
            "ember_forge exact realm uniqueness explicitly unproven",
            "visual models excluded from assembly-byte inputs",
        ],
        "commands": [
            "python3 engineering/ashen-intake/structure-assemblies/author_ashen_structures.py --check",
            "python3 -m unittest engineering/ashen-intake/structure-assemblies/test_ashen_structure_assemblies.py -v",
        ],
        "counts": {"assemblies": 10, "structure_files": 10, "features": 10, "feature_rules": 10, "unit_tests": 8, "inert_anchor_blocks": 20, "block_entity_nbt_records": 0},
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
