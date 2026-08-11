#!/usr/bin/env python3
"""Run bounded Ashen structure-economy checks and emit captured evidence."""

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
REPORT = HERE / "ASHEN_STRUCTURE_ECONOMY_VALIDATION_REPORT.json"
COMMANDS = [
    [sys.executable, "engineering/ashen-intake/structure-assemblies/author_ashen_structures.py", "--check"],
    [sys.executable, "engineering/ashen-intake/structure-economy/author_ashen_structure_economy.py", "--check"],
    [sys.executable, "engineering/ashen-intake/structure-assemblies/test_ashen_structure_assemblies.py"],
    [sys.executable, "engineering/ashen-intake/structure-economy/test_ashen_structure_economy.py"],
    ["node", "--test", "tests/wave1_ashen_structure_rewards.test.mjs"],
    ["node", "--test", "tests/g7_runtime_semantics.test.mjs"],
]


def run(command: list[str]) -> dict:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, cwd=REPO, text=True, capture_output=True, env=environment)
    def stable_output(value: str) -> str:
        value = re.sub(r"\([0-9.]+ms\)", "(DURATION)", value)
        value = re.sub(r"duration_ms [0-9.]+", "duration_ms DURATION", value)
        return re.sub(r"Ran (\d+) tests in [0-9.]+s", r"Ran \1 tests in DURATION", value)
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
    outputs = sorted((REPO / "behavior_pack" / "loot_tables" / "chests" / "ashen").glob("*.json"))
    outputs += [REPO / "behavior_pack/scripts/ashen_structure_reward_data.js", REPO / "behavior_pack/scripts/ashen_structure_rewards.js", REPO / "behavior_pack/scripts/runtime.js"]
    return {
        "schema": "aionbound.wave1.ashen.structure_economy_validation.v1",
        "status": "PASS",
        "integration_authority": {"commit": "ae5838c08b445e57c30e92f99d90bed426fcaf91", "tree": "b4bf5f1a2e39bb7477aedee68927a039a20f2e59"},
        "ratified_authority": ["W1-001-AH", "W1-004-AH"],
        "checks": [
            "deterministic structure and economy regeneration",
            "seven exact static LootTable path bindings",
            "distinct Ashen-purpose tables within ratified roll bands",
            "item and block identifier closure",
            "protected reward exclusion from every structure table and runtime bridge",
            "empty and guarded Ember Forge cache before explicit valid clear",
            "inventory-first ordinary delivery with owner-local overflow",
            "exact assembly-derived cardinal activation signatures and discovery stamps",
            "runtime composition without boss terminal ownership or commands",
        ],
        "captured_commands": evidence,
        "counts": {"loot_tables": 8, "static_bindings": 7, "protected_runtime_cache": 1, "activation_signatures": 20, "python_tests": 13, "node_tests": 22},
        "outputs": [{"path": str(path.relative_to(REPO)), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in outputs],
        "proof_boundary": "STATIC_LOOT_NBT_SIGNATURE_AND_SEMANTIC_TEST_EVIDENCE_ONLY; NO BDS, BUILD, CLIENT, BOSS_TERMINAL, OR CANDIDATE CLAIM",
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
