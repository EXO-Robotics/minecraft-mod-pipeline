#!/usr/bin/env python3
"""Bind deterministic self-harvest tables to the ten Ashen plants."""

from __future__ import annotations

import json
from pathlib import Path

from build_ashen_plants import PLANTS


ROOT = Path(__file__).resolve().parents[3]


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for asset in PLANTS:
        entries = [{"type": "item", "name": f"aionbound:{asset}", "weight": 1}]
        pools = [{"rolls": 1, "entries": entries}]
        if asset == "fire_bloom":
            pools.append({
                "rolls": 1,
                "entries": [{
                    "type": "item",
                    "name": "aionbound:fire_bloom_seed",
                    "weight": 1,
                    "conditions": [{"condition": "random_chance", "chance": 0.35}],
                }],
            })
        table = {"pools": pools}
        dump(ROOT / f"behavior_pack/loot_tables/blocks/ashen/{asset}.json", table)
        block_path = ROOT / f"behavior_pack/blocks/{asset}.block.json"
        block = json.loads(block_path.read_text(encoding="utf-8"))
        block["minecraft:block"]["components"]["minecraft:loot"] = f"loot_tables/blocks/ashen/{asset}.json"
        dump(block_path, block)


if __name__ == "__main__":
    main()
