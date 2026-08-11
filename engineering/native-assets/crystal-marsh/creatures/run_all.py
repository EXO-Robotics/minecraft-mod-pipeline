#!/usr/bin/env python3
"""Run the exact seven-asset native gate against one isolated Blockbench session."""

from pathlib import Path

import author_creatures as author


PACKET = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-003-crystal-marsh")
HERE = Path(__file__).resolve().parent
ENDPOINT = "http://127.0.0.1:9265"


def main() -> int:
    for asset in author.SPECS:
        code, receipt = author.execute(author.engine.Inputs(
            asset,
            PACKET / "assets" / "editable" / f"{asset}.bbmodel",
            PACKET / "assets" / "editable" / f"{asset}.png",
            PACKET / "assets" / "export" / "models" / f"{asset}.geo.json",
            PACKET / "assets" / "briefs" / f"{asset}.json",
            HERE / "evidence" / asset,
            ENDPOINT,
        ))
        print(f"{asset}: {receipt['status']}", flush=True)
        if code:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
