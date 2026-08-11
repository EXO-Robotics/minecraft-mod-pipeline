#!/usr/bin/env python3
"""Capture deterministic bundled static-validation evidence for native exports."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import author_creatures as author


HERE = Path(__file__).resolve().parent
VALIDATOR = Path("/Users/blakegrove/.codex/skills/blockbench-build-bedrock-assets/scripts/validate_bedrock_asset.py")
OUTPUT = HERE / "CRYSTAL_MARSH_CREATURE_STATIC_VALIDATION.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    assets = []
    for asset in author.SPECS:
        root = HERE / "evidence" / asset
        geometry = root / "native-exports" / "pass-2.geo.json"
        texture = root / "native-project" / "textures" / f"{asset}.png"
        command = [
            "python3", str(VALIDATOR),
            "--geometry", str(geometry),
            "--texture", str(texture),
            "--namespace", "aionbound",
            "--required-locator", "effect",
            "--required-locator", "gaze",
        ]
        result = subprocess.run(command, text=True, capture_output=True)
        assets.append({
            "asset": asset,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "geometry_sha256": sha256(geometry),
            "texture_sha256": sha256(texture),
            "required_locators": ["effect", "gaze"],
        })
    return {
        "schema": "aionforge.wave1.crystal_marsh.creature_native_static_validation.v1",
        "status": "PASS" if all(item["status"] == "PASS" for item in assets) else "FAIL",
        "validator": str(VALIDATOR),
        "validator_sha256": sha256(VALIDATOR),
        "integration_authority": {"commit": author.INTEGRATION_COMMIT, "tree": author.INTEGRATION_TREE},
        "assets": assets,
        "proof_boundary": "STATIC_GEOMETRY_TEXTURE_LOCATOR_VALIDATION_ONLY",
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
