#!/usr/bin/env python3
"""Bind Ashen full-cube harvests to ratified regional acquisition."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BLOCKS = ROOT / "behavior_pack/blocks"
LOOT = ROOT / "behavior_pack/loot_tables/blocks/ashen"

# (item, chance, min, max); chance 1 means guaranteed.
TABLES = {
    "ash_log": [("aionbound:ash_log", 1, 1, 1), ("aionbound:smolder_bark", 1, 1, 2)],
    "ash_soil": [("aionbound:ash_soil", 1, 1, 1), ("aionbound:charbone", 0.40, 1, 1)],
    "basalt_brick": [("aionbound:basalt_brick", 1, 1, 1)],
    "basalt_pillar": [("aionbound:basalt_pillar", 1, 1, 1), ("aionbound:basalt_core", 0.08, 1, 1)],
    "char_planks": [("aionbound:char_planks", 1, 1, 1)],
    "cinder_gravel": [("aionbound:cinder_gravel", 1, 1, 1), ("aionbound:sulfur_cluster", 0.35, 1, 1)],
    "ember_moss": [("aionbound:ember_moss", 1, 1, 1), ("aionbound:ember_resin", 0.30, 1, 1)],
    "heat_bark": [("aionbound:heat_bark", 1, 1, 1), ("aionbound:smolder_bark", 1, 1, 1)],
    "smolder_stone": [
        ("aionbound:smolder_stone", 1, 1, 1),
        ("aionbound:heatstone", 0.30, 1, 1),
        ("aionbound:ash_crystal", 0.08, 1, 1),
    ],
    "volcanic_glass_block": [("aionbound:volcanic_glass_shard", 1, 2, 4)],
}


def pool(item: str, chance: float, low: int, high: int) -> dict:
    count = low if low == high else {"min": low, "max": high}
    value = {
        "rolls": 1,
        "entries": [{"type": "item", "name": item, "weight": 1,
                     "functions": [{"function": "set_count", "count": count}]}],
    }
    if chance < 1:
        value["conditions"] = [{"condition": "random_chance", "chance": chance}]
    return value


def main() -> None:
    LOOT.mkdir(parents=True, exist_ok=True)
    for block, rows in TABLES.items():
        target = LOOT / f"{block}.json"
        target.write_text(json.dumps({"pools": [pool(*r) for r in rows]}, indent=2) + "\n")
        block_path = BLOCKS / f"{block}.block.json"
        data = json.loads(block_path.read_text())
        data["minecraft:block"]["components"]["minecraft:loot"] = f"loot_tables/blocks/ashen/{block}.json"
        block_path.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
