#!/usr/bin/env python3
"""Bind bounded EARLY placeholder audio for Ashen creatures."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOUNDS = ROOT / "resource_pack/sounds.json"

ROWS = {
    "ash_mite": ("mob.spider.say", "mob.spider.say", "mob.spider.death", [1.15, 1.30], 0.45, 6, 8),
    "ember_crow": ("mob.vex.ambient", "mob.vex.hurt", "mob.vex.death", [1.10, 1.25], 0.55, 12, 10),
    "magma_lizard": ("mob.pig.say", "mob.pig.say", "mob.pig.death", [0.95, 1.10], 0.55, 10, 9),
    "furnace_beetle": ("mob.spider.say", "mob.spider.say", "mob.spider.death", [0.60, 0.75], 0.70, 14, 10),
    "char_wolf": ("mob.wolf.bark", "mob.wolf.hurt", "mob.wolf.death", [0.70, 0.85], 0.80, 8, 12),
    "cinder_lynx": ("mob.wolf.bark", "mob.wolf.hurt", "mob.wolf.death", [1.05, 1.20], 0.60, 11, 12),
    "ash_ram": ("mob.goat.ambient", "mob.goat.hurt", "mob.goat.death", [0.70, 0.85], 0.85, 12, 12),
    "soot_stag": ("mob.goat.ambient", "mob.goat.hurt", "mob.goat.death", [0.90, 1.00], 0.65, 15, 14),
    "basalt_tortoise": ("mob.ravager.ambient", "mob.ravager.hurt", "mob.ravager.death", [0.50, 0.65], 0.75, 18, 10),
    "ash_drake": ("mob.ravager.ambient", "mob.ravager.hurt", "mob.ravager.death", [0.65, 0.80], 1.00, 8, 16),
}


def main() -> None:
    sounds = json.loads(SOUNDS.read_text())
    entities = sounds.setdefault("entity_sounds", {}).setdefault("entities", {})
    for asset, (ambient, hurt, death, pitch, volume, interval, distance) in ROWS.items():
        entities[f"aionbound:{asset}"] = {
            "events": {"ambient": ambient, "death": death, "hurt": hurt},
            "pitch": pitch, "volume": volume,
        }
        path = ROOT / f"behavior_pack/entities/aionbound/ashen/{asset}.entity.json"
        data = json.loads(path.read_text())
        data["minecraft:entity"]["components"]["minecraft:ambient_sound_interval"] = {
            "event_name": "ambient", "range": distance, "value": interval,
        }
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    SOUNDS.write_text(json.dumps(sounds, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
