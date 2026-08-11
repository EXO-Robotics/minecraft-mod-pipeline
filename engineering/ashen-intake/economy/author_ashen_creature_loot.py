#!/usr/bin/env python3
"""Author the ratified Ashen ecology-form creature loot tables."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "behavior_pack" / "loot_tables" / "entities" / "ashen"

# Each tuple is (item, chance, min_count, max_count).  All values are selected
# inside W1-004-AH.  Collapsed terms follow the exact W1-001-AH aliases.
TABLES = {
    "ash_mite": [
        ("aionbound:charbone", 1.00, 1, 3),
        ("aionbound:ember_resin", 0.32, 1, 1),
        ("aionbound:furnace_chitin", 0.10, 1, 1),
    ],
    "ember_crow": [
        ("aionbound:volcanic_glass_shard", 0.80, 1, 2),
        ("aionbound:charbone", 0.28, 1, 1),
    ],
    "magma_lizard": [
        ("aionbound:ember_resin", 0.85, 1, 3),
        ("aionbound:volcanic_glass_shard", 0.35, 1, 2),
    ],
    "furnace_beetle": [
        ("aionbound:furnace_chitin", 0.50, 1, 2),
        ("aionbound:ember_resin", 0.12, 1, 1),
        ("aionbound:basalt_core", 0.10, 1, 1),
    ],
    "char_wolf": [
        ("aionbound:furnace_chitin", 0.85, 1, 2),
        ("aionbound:ember_resin", 0.40, 1, 2),
    ],
    "cinder_lynx": [
        ("aionbound:furnace_chitin", 0.48, 1, 2),
        ("aionbound:charbone", 0.40, 1, 1),
        ("aionbound:heatstone", 0.30, 1, 1),
    ],
    "ash_ram": [
        ("aionbound:basalt_core", 0.40, 1, 1),
        ("aionbound:furnace_chitin", 0.90, 1, 3),
        ("aionbound:charbone", 0.12, 1, 1),
    ],
    "soot_stag": [
        ("aionbound:charbone", 0.40, 1, 1),
        ("aionbound:furnace_chitin", 0.85, 1, 2),
        ("aionbound:fire_bloom_seed", 0.30, 1, 1),
        ("aionbound:ember_resin", 0.12, 1, 1),
    ],
    "basalt_tortoise": [
        ("aionbound:basalt_core", 0.12, 1, 1),
        ("aionbound:furnace_chitin", 0.45, 1, 2),
    ],
    "ash_drake_ecology": [
        ("aionbound:drake_scale", 0.45, 1, 2),
        ("aionbound:ember_resin", 0.40, 1, 1),
        ("aionbound:volcanic_glass_shard", 0.50, 1, 2),
        ("aionbound:heatstone", 0.50, 2, 2),
    ],
}


def entry(item: str, chance: float, low: int, high: int) -> dict:
    count: int | dict = low if low == high else {"min": low, "max": high}
    pool = {
        "rolls": 1,
        "entries": [{
            "type": "item",
            "name": item,
            "weight": 1,
            "functions": [{"function": "set_count", "count": count}],
        }],
    }
    if chance < 1:
        pool["conditions"] = [{"condition": "random_chance", "chance": chance}]
    return pool


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in TABLES.items():
        payload = {"pools": [entry(*row) for row in rows]}
        (OUT / f"{name}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
