#!/usr/bin/env python3
"""Bind committed Crystal loot tables after creature and plant lanes merge.

This is intentionally not run at the 6a10cd8 base because those BP definitions
do not exist there. It edits only the exact twenty already-ratified entity and
plant block definitions and introduces no runtime handler or persistence state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CREATURES = (
    "prism_frog", "crystal_newt", "crystal_dragonfly", "bloom_crab", "mire_turtle",
    "glass_heron", "reed_serpent", "silt_crocodile", "bog_watcher", "marsh_wight",
)
PLANTS = (
    "pearl_grass", "marsh_fern", "flood_reed", "glass_moss", "glow_kelp",
    "bubble_pod", "crystal_lily", "crystal_vine", "mire_orchid", "prism_bloom",
)


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def expected() -> list[tuple[Path, str, str]]:
    return [
        *((ROOT / "behavior_pack/entities/aionbound/crystal_marsh" / f"{asset}.entity.json", "minecraft:entity", f"loot_tables/entities/crystal/{asset}.json") for asset in CREATURES),
        *((ROOT / "behavior_pack/blocks" / f"{asset}.block.json", "minecraft:block", f"loot_tables/blocks/{asset}.json") for asset in PLANTS),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    missing = [str(path.relative_to(ROOT)) for path, _root, _table in expected() if not path.is_file()]
    if missing:
        print(json.dumps({"status": "WAITING_FOR_POST_MERGE_DEFINITIONS", "missing": missing}, indent=2))
        return 2
    mismatches = []
    for path, root_key, table in expected():
        document = json.loads(path.read_text())
        components = document[root_key]["components"]
        current = components.get("minecraft:loot")
        if args.check:
            if current != {"table": table} and current != table:
                mismatches.append({"path": str(path.relative_to(ROOT)), "expected": table, "actual": current})
        else:
            components["minecraft:loot"] = {"table": table} if root_key == "minecraft:entity" else table
            path.write_bytes(encoded(document))
    if mismatches:
        print(json.dumps({"status": "FAIL", "mismatches": mismatches}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "mode": "check" if args.check else "write", "bindings": 20}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
