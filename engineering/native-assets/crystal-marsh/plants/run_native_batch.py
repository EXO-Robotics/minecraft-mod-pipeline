#!/usr/bin/env python3
"""Execute the exact eight-plant native gate against one loopback session."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import author_plants as author


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-003-crystal-marsh")
HERE = Path(__file__).resolve().parent
ENDPOINT = "http://127.0.0.1:9266"


def main() -> int:
    completed = []
    for asset in author.ASSETS:
        code, receipt = author.execute(author.native_gate.Inputs(
            asset,
            (PACKET / "assets" / "editable" / f"{asset}.bbmodel").resolve(),
            (PACKET / "assets" / "editable" / f"{asset}.png").resolve(),
            (PACKET / "assets" / "export" / "models" / f"{asset}.geo.json").resolve(),
            (PACKET / "assets" / "briefs" / f"{asset}.json").resolve(),
            (HERE / "evidence" / asset).resolve(),
            ENDPOINT,
        ))
        completed.append({"asset": asset, "status": receipt["status"], "exit_code": code})
        if code:
            print(json.dumps({"status": "FAIL", "completed": completed}, sort_keys=True))
            return code
    print(json.dumps({"status": "PASS_NATIVE_REPAIR_GATE", "completed": completed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
