#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mccompiler.creator_tools import (
    invoke_creator_tools,
    load_creator_tools_lock,
    load_creator_tools_policy,
)


ASSET = ROOT / "prototypes/blockbench/bramblehorn"
PACKAGE = ASSET / "addon/bramblehorn_animated.mcaddon"
OUTPUT = ASSET / "qualification/creator-tools-result.json"


def run(executable: Path) -> dict:
    result = invoke_creator_tools(
        executable,
        PACKAGE,
        lock=load_creator_tools_lock(),
        policy=load_creator_tools_policy(),
    )
    receipt = {
        "schema_version": "1.0.0",
        "classification": "CREATOR_TOOLS_STATIC_QUALIFICATION",
        "status": "PASSED" if result["passed"] else "FAILED",
        "package_sha256": hashlib.sha256(PACKAGE.read_bytes()).hexdigest(),
        "result": result,
        "claims": {"marketplace_approved": False, "physical_ps4_verified": False},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    value = run(args.executable.resolve())
    print(json.dumps(value, indent=2, sort_keys=True))
    raise SystemExit(0 if value["status"] == "PASSED" else 1)
