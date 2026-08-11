#!/usr/bin/env python3
"""Run bounded Crystal structure-economy checks and capture stable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REPORT = HERE / "CRYSTAL_STRUCTURE_ECONOMY_VALIDATION_REPORT.json"
COMMANDS = [
    [sys.executable, "engineering/crystal-marsh-intake/structure-economy/author_crystal_structure_economy.py", "--check"],
    [sys.executable, "-m", "unittest", "engineering/crystal-marsh-intake/structure-economy/test_crystal_structure_economy.py", "-v"],
]


def stable_output(value: str) -> str:
    value = re.sub(r"Ran (\d+) tests in [0-9.]+s", r"Ran \1 tests in DURATION", value)
    return re.sub(r"\([0-9.]+ms\)", "(DURATION)", value)


def run(command: list[str]) -> dict:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True, env=environment)
    evidence = {
        "command": " ".join(["python3", *command[1:]]) if command[0] == sys.executable else " ".join(command),
        "exit_code": result.returncode,
        "normalized_stdout_sha256": hashlib.sha256(stable_output(result.stdout).encode()).hexdigest(),
        "normalized_stderr_sha256": hashlib.sha256(stable_output(result.stderr).encode()).hexdigest(),
    }
    if result.returncode:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return evidence


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report(evidence: list[dict]) -> dict:
    binding = json.loads((HERE / "CRYSTAL_STRUCTURE_ECONOMY_BINDING.json").read_text())
    outputs = [
        REPO / item["structure_path"] for item in binding["assemblies"]
    ] + [HERE / "CRYSTAL_STRUCTURE_ECONOMY_BINDING.json", HERE / "README.md"]
    return {
        "schema": "aionbound.wave1.crystal_marsh.structure_economy_validation.v1",
        "status": "PASS",
        "integration_authority": {"commit": "d8974fee959f0f15a8a212364a38d285e38078a5", "tree": "35a07b3a82e161e43bc03f8bdbf6929902fc2297"},
        "ratified_authority": ["W1-001-CM", "W1-004-CM"],
        "checks": [
            "deterministic post-ratification structure regeneration",
            "exact predecessor anchor-manifest closure",
            "ten unchanged assembly sizes palettes and block-index layers",
            "seven exact ordinary barrel LootTable bindings",
            "four-cardinal rotation and anchor bounds closure",
            "two no-chest-identity structures remain inert",
            "Pearl Depths protected cache remains empty and synchronously guardable",
            "ordinary loot identity closure and marsh_wight_mask prohibition",
            "feature and feature-rule files excluded from the mutation surface",
        ],
        "captured_commands": evidence,
        "counts": {
            "assemblies": 10,
            "ordinary_static_bindings": 7,
            "inert_no_chest_identity": 2,
            "protected_empty_encounter_cache": 1,
            "cardinal_rotation_cases": 28,
            "python_tests": 6,
        },
        "outputs": [{"path": str(path.relative_to(REPO)), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in outputs],
        "proof_boundary": "STATIC_EXACT_NBT_BINDING_AND_TARGETED_SEMANTIC_TEST_EVIDENCE_ONLY; NO BDS, BUILD, CLIENT, ENCOUNTER_RUNTIME, REWARD, OR CANDIDATE CLAIM",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    evidence = [run(command) for command in COMMANDS]
    encoded = (json.dumps(build_report(evidence), indent=2) + "\n").encode()
    if args.check:
        if not REPORT.exists() or REPORT.read_bytes() != encoded:
            print(json.dumps({"status": "FAIL", "report": str(REPORT.relative_to(REPO))}, indent=2))
            return 1
    else:
        REPORT.write_bytes(encoded)
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "report": str(REPORT.relative_to(REPO))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
