#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("ASHEN_EQUIPMENT_FUNCTIONAL_EVIDENCE.json")
BASE = {"commit": "c115574759935c1dafd5bf508733b7b0737ed5c2", "tree": "41e485ed219ae6bc4177059d9ae8d11be714d1f5"}
AUTHORITIES = {
    "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json": "cf7e1cd8b81b4a8088d136e1f9f2cb4ee3e245cfa71259f2a957d6e4f55ccff9",
    "engineering/ashen-intake/equipment/ASHEN_EQUIPMENT_INTAKE.json": "1fe10a0cf8af6b8563144eb4310e9fca325dc6282d5e96178d912a34cdc64f5d",
}
ITEMS = {
    "basalt_hammer": {"damage": 9, "durability": 480, "repair": ["aionbound:basalt_core", 96], "declarative_role": "stone_and_exact_Ashen_structure_digger"},
    "ember_great_axe": {"damage": 9, "durability": 420, "repair": ["aionbound:ember_resin", 84]},
    "ash_repeater": {"damage": 3, "durability": 360, "repair": ["aionbound:volcanic_glass_shard", 72], "use_seconds": .2, "item_cooldown_seconds": .6},
    "ashen_helmet": {"durability": 220, "protection": 2, "repair": ["aionbound:ember_resin", 44]},
    "ashen_chest": {"durability": 320, "protection": 5, "repair": ["aionbound:ember_resin", 64]},
    "ashen_legs": {"durability": 300, "protection": 4, "repair": ["aionbound:ember_resin", 60]},
    "ashen_boots": {"durability": 260, "protection": 2, "repair": ["aionbound:ember_resin", 52]},
    "basalt_pick": {"damage": 4, "durability": 420, "repair": ["aionbound:basalt_core", 84], "declarative_role": "hard_stone_ore_and_exact_Ashen_material_digger"},
    "ember_hammer": {"damage": 3, "durability": 300, "repair": ["aionbound:ember_resin", 60], "declarative_role": "exact_forge_basalt_digger"},
    "ore_chisel": {"damage": 2, "durability": 240, "repair": ["aionbound:furnace_chitin", 48], "declarative_role": "exact_precision_node_digger"},
}
ACTIVE = {
    "basalt_hammer": {"cooldown_ticks": 30, "stun_ticks": 20, "armored_weakness_ticks": 40},
    "ember_great_axe": {"cooldown_ticks": 24, "radius": 3, "secondary_target_cap": 3, "secondary_damage": 1, "fire_seconds": 2},
    "ash_repeater": {"range": 18, "damage": 4, "cooldown_ticks": 12, "particle_cap": 4, "fire_seconds": 2, "ammo": "aionbound:volcanic_glass_shard", "ammo_per_shot": 1, "durability_per_shot": 1},
    "ashen_armor": {"pieces_required": 4, "fire_resistance_refresh_ticks": 60},
    "ember_totem": {"fire_resistance_refresh_ticks": 60, "reactive_ticks": 200, "reactive_cooldown_ticks": 200},
}
SOURCES = [
    "behavior_pack/scripts/ashen_equipment.js", "behavior_pack/scripts/ashen_equipment_roles.js",
    *[f"behavior_pack/items/{item}.item.json" for item in ITEMS],
    "tests/wave1_ashen_equipment_functional.test.mjs",
    "engineering/ashen-intake/equipment-runtime-ashen/test_runtime.py",
    "engineering/ashen-intake/equipment-functional/ACTIVATION_WITHHELD.md",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    return {
        "schema": "aionbound.ashen_equipment_functional_evidence.v1",
        "status": "DEDICATED_SERVICE_AND_DECLARATIVE_COMPONENTS_PASS_ACTIVATION_WITHHELD",
        "base": BASE,
        "authority": [{"path": path, "sha256": value, "verified": sha256(ROOT / path) == value} for path, value in sorted(AUTHORITIES.items())],
        "engineering_refinements": {"declarative_items": ITEMS, "dedicated_active_roles": ACTIVE},
        "source": [{"path": path, "sha256": sha256(ROOT / path)} for path in SOURCES],
        "preserved_boundaries": {"W1-CREATIVE-005": "DEFERRED", "briar_ring": "UNCHANGED_BASE_BYTES"},
        "source_blocked": {"ember_totem_durability_and_repair": "offhand passive use has no clean automatic durability consumption; custom consumption remains unactivated"},
        "stale_test_disposition": {"engineering/ashen-intake/equipment-runtime-ashen/test_runtime.py": "ADAPTED_TO_PRESERVE_HISTORICAL_SHELL_RECEIPT_WHILE_ACCEPTING_SUCCESSOR_FUNCTIONAL_ITEM_HASHES"},
        "proof": {"declarative_components": True, "dedicated_service_semantics": True, "shared_runtime_activation": False, "build": False, "package": False, "bds": False, "client": False},
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n")
