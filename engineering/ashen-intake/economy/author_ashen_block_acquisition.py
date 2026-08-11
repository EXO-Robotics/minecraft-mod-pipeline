#!/usr/bin/env python3
"""Bind Ashen full-cube harvests to ratified regional acquisition."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BLOCKS = ROOT / "behavior_pack/blocks"
LOOT = ROOT / "behavior_pack/loot_tables/blocks/ashen"

# Every break produces one pool outcome. This prevents a placed block from
# returning itself plus a bonus resource and becoming a re-break duplication
# loop. Rows are (item, weight, min, max).
TABLES = {
    "ash_log": [("aionbound:ash_log", 100, 1, 1)],
    "ash_soil": [("aionbound:ash_soil", 100, 1, 1)],
    "basalt_brick": [("aionbound:basalt_brick", 100, 1, 1)],
    "basalt_pillar": [("aionbound:basalt_pillar", 92, 1, 1), ("aionbound:basalt_core", 8, 1, 1)],
    "char_planks": [("aionbound:char_planks", 100, 1, 1)],
    "cinder_gravel": [("aionbound:cinder_gravel", 65, 1, 1), ("aionbound:sulfur_cluster", 35, 1, 1)],
    "ember_moss": [("aionbound:ember_moss", 70, 1, 1), ("aionbound:ember_resin", 30, 1, 1)],
    "heat_bark": [("aionbound:heat_bark", 100, 1, 1)],
    "smolder_stone": [
        ("aionbound:smolder_stone", 62, 1, 1),
        ("aionbound:heatstone", 30, 1, 1),
        ("aionbound:ash_crystal", 8, 1, 1),
    ],
    "volcanic_glass_block": [("aionbound:volcanic_glass_shard", 100, 2, 4)],
}


def loot_entry(item: str, weight: int, low: int, high: int) -> dict:
    count = low if low == high else {"min": low, "max": high}
    return {
        "type": "item", "name": item, "weight": weight,
        "functions": [{"function": "set_count", "count": count}],
    }


def main() -> None:
    LOOT.mkdir(parents=True, exist_ok=True)
    for block, rows in TABLES.items():
        target = LOOT / f"{block}.json"
        target.write_text(json.dumps({
            "pools": [{"rolls": 1, "entries": [loot_entry(*r) for r in rows]}]
        }, indent=2) + "\n")
        block_path = BLOCKS / f"{block}.block.json"
        data = json.loads(block_path.read_text())
        data["minecraft:block"]["components"]["minecraft:loot"] = f"loot_tables/blocks/ashen/{block}.json"
        block_path.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
