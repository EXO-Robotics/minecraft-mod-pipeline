#!/usr/bin/env python3
"""Author the ratified Skyreach acquisition, loot, crafting and Packet 006 links."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"

PROPOSAL_HASHES = {
    "W1-001-SR": "926a401add04b6611d7cee7dd1fa3bcf6a3fe44cf656ef9aa34d9b1bad5f30cd",
    "W1-003-STORM-NEST": "59b4493857bf3d90d402d438553f4b7fc03c6b45689e5897f8a8cb501bfc15d0",
    "W1-004-SR": "823894296bb4b4ed1becd1a1a5ccc814f734cecc50c8433be855bdf1e080e4bf",
}

ITEMS = {
    "wing_bone_stay": ("Wing Bone Stay", "cliff_crystal"),
    "climbing_rope": ("Climbing Rope", "wind_silk"),
    "climbing_hook_head": ("Climbing Hook Head", "cliff_crystal"),
    "glider_panel": ("Glider Panel", "sky_feather"),
    "glider_frame": ("Glider Frame", "sky_feather"),
    "soft_landing_pad": ("Soft Landing Pad", "cloud_wool"),
    "lift_tonic": ("Lift Tonic", "lift_bloom_item"),
    "aether_bind": ("Aether Bind", "aether_stone"),
    "twin_mineral_lens": ("Twin Mineral Lens", "cliff_crystal"),
}

RECIPES = {
    "climbing_rope": (["VVV", "SSS"], {"V": "aionbound:sky_vine_item", "S": "aionbound:wind_silk"}),
    "climbing_hook_head": ([" C ", "CCC", " C "], {"C": "aionbound:cliff_crystal"}),
    "glider_panel": (["FSF", "SBS", "FSF"], {"F": "aionbound:sky_feather", "S": "aionbound:wind_silk", "B": "aionbound:wing_bone_stay"}),
    "glider_frame": (["PPP", "L L", "SSS"], {"P": "aionbound:glider_panel", "L": "aionbound:skyreach_planks", "S": "aionbound:wind_silk"}),
    "soft_landing_pad": (["WWW", "RWR", "WWW"], {"W": "aionbound:cloud_wool", "R": "aionbound:float_resin"}),
    "lift_tonic": ([" R ", "BLB", " G "], {"R": "aionbound:updraft_reed_item", "B": "aionbound:lift_bloom_item", "L": "aionbound:float_resin", "G": "minecraft:glass_bottle"}),
    "aether_bind": ([" R ", "RAR", " R "], {"R": "aionbound:float_resin", "A": "aionbound:aether_stone"}),
    "twin_mineral_lens": ([" F ", "CAC", " F "], {"F": "aionbound:flood_crystal", "C": "minecraft:copper_ingot", "A": "aionbound:ash_crystal"}),
    "surveyor_staff": ([" AL", " SL", "S  "], {"A": "aionbound:aether_stone", "L": "aionbound:twin_mineral_lens", "S": "aionbound:skyreach_log"}),
    "trail_compass": ([" C ", "RMR", " C "], {"C": "aionbound:cliff_crystal", "R": "aionbound:float_resin", "M": "minecraft:compass"}),
    "surveyor_medallion": ([" C ", "MAP", " C "], {"C": "minecraft:copper_ingot", "M": "minecraft:map", "A": "aionbound:aether_stone", "P": "minecraft:paper"}),
    "warden_sigil": ([" C ", "TLT", " R "], {"C": "aionbound:cliff_crystal", "T": "aionbound:ember_totem", "L": "aionbound:living_root_focus", "R": "aionbound:root_heart"}),
}

CREATURE_LOOT = {
    "cloud_goat": [("aionbound:cloud_wool", 1.0, 1, 2), ("aionbound:cliff_crystal", .40, 1, 1)],
    "sky_fox": [("aionbound:cloud_wool", 1.0, 1, 2), ("aionbound:wind_silk", .40, 1, 1)],
    "cliff_ram": [("aionbound:cliff_crystal", 1.0, 1, 2), ("aionbound:cloud_wool", .40, 1, 1)],
    "storm_gull": [("aionbound:sky_feather", 1.0, 1, 2), ("aionbound:float_resin", .40, 1, 1), ("aionbound:sky_vine_item", .05, 1, 1)],
    "gale_hawk": [("aionbound:sky_feather", 1.0, 1, 2), ("aionbound:wind_silk", .50, 1, 1), ("aionbound:cliff_crystal", .40, 1, 1)],
    "ropewing": [("aionbound:wind_silk", 1.0, 1, 2), ("aionbound:wing_bone_stay", .50, 1, 1), ("aionbound:float_resin", .40, 1, 1)],
    "stone_vulture": [("aionbound:cliff_crystal", 1.0, 1, 2), ("aionbound:float_resin", .40, 1, 1)],
    "glide_drake": [("aionbound:float_resin", 1.0, 1, 2), ("aionbound:wind_silk", .50, 1, 1), ("aionbound:aether_stone", .14, 1, 1)],
    "ruin_harpy": [("aionbound:cliff_crystal", 1.0, 1, 2), ("aionbound:wind_silk", .50, 1, 1), ("aionbound:aether_stone", .14, 1, 1)],
    # Ecology/command Wind Roc intentionally has no storm_pinion route.
    "wind_roc": [("aionbound:sky_feather", 1.0, 1, 2), ("aionbound:aether_stone", .50, 1, 1)],
}

PLANT_LOOT = {
    "wind_reed_plant": "aionbound:updraft_reed_item",
    "hanging_sky_vine": "aionbound:sky_vine_item",
    "rope_root": "aionbound:sky_vine_item",
    "cloud_moss": "aionbound:cloud_wool",
    "cloudpuff_plant": "aionbound:cloud_wool",
    "shelf_shrub": "aionbound:sky_vine_item",
    "cliff_flower": "aionbound:lift_bloom_item",
    "skybloom": "aionbound:lift_bloom_item",
    "floating_blossom": "aionbound:float_resin",
    "nest_thatch_tuft": "aionbound:sky_feather",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def item_payload(item_id: str, name: str, icon: str) -> dict:
    return {"format_version": "1.21.80", "minecraft:item": {"description": {"identifier": f"aionbound:{item_id}", "menu_category": {"category": "items"}}, "components": {"minecraft:display_name": {"value": name}, "minecraft:icon": {"textures": {"default": item_id}}, "minecraft:max_stack_size": 64}}}


def recipe_payload(item_id: str, pattern: list[str], keys: dict[str, str]) -> dict:
    return {"format_version": "1.20.10", "minecraft:recipe_shaped": {"description": {"identifier": f"aionbound:{item_id}_recipe"}, "tags": ["crafting_table"], "pattern": pattern, "key": {key: {"item": value} for key, value in keys.items()}, "result": {"item": f"aionbound:{item_id}", "count": 1}, "unlock": [{"item": next(iter(keys.values()))}]}}


def loot_payload(rows: list[tuple[str, float, int, int]]) -> dict:
    pools = []
    for type_id, chance, minimum, maximum in rows:
        functions = [] if minimum == maximum == 1 else [{"function": "set_count", "count": {"min": minimum, "max": maximum}}]
        pools.append({"rolls": 1, "entries": [{"type": "item", "name": type_id, "weight": 1, "functions": functions}], "conditions": [{"condition": "random_chance", "chance": chance}]})
    return {"pools": pools}


def main() -> None:
    texture_path = RP / "textures/item_texture.json"
    textures = json.loads(texture_path.read_text())
    for item_id, (name, source_icon) in ITEMS.items():
        write_json(BP / f"items/{item_id}.item.json", item_payload(item_id, name, source_icon))
        textures["texture_data"][item_id] = {"textures": f"textures/aionbound/skyreach/items/{source_icon}"}
    write_json(texture_path, textures)

    for item_id, (pattern, keys) in RECIPES.items():
        write_json(BP / f"recipes/{item_id}.recipe.json", recipe_payload(item_id, pattern, keys))

    for entity_id, rows in CREATURE_LOOT.items():
        path = BP / f"loot_tables/entities/aionbound/skyreach/{entity_id}.json"
        write_json(path, loot_payload(rows))
        entity_path = BP / f"entities/aionbound/skyreach/{entity_id}.entity.json"
        entity = json.loads(entity_path.read_text())
        entity["minecraft:entity"]["components"]["minecraft:loot"] = {"table": f"loot_tables/entities/aionbound/skyreach/{entity_id}.json"}
        write_json(entity_path, entity)

    for plant_id, type_id in PLANT_LOOT.items():
        table = f"loot_tables/blocks/aionbound/skyreach/{plant_id}.json"
        write_json(BP / table, loot_payload([(type_id, 1.0, 1, 1)]))
        block_path = BP / f"blocks/{plant_id}.block.json"
        block = json.loads(block_path.read_text())
        block["minecraft:block"]["components"]["minecraft:loot"] = table
        write_json(block_path, block)

    lang_path = RP / "texts/en_US.lang"
    lines = lang_path.read_text().splitlines()
    additions = [f"item.aionbound:{item_id}.name={name}" for item_id, (name, _icon) in ITEMS.items()]
    existing = {line.split("=", 1)[0] for line in lines if "=" in line}
    lines.extend(line for line in additions if line.split("=", 1)[0] not in existing)
    lang_path.write_text("\n".join(lines) + "\n")

    report = {
        "schema": "aionbound.wave1.skyreach.approved_vertical.v1",
        "status": "SKYREACH_APPROVED_ECONOMY_PACKET006_SOURCE_IMPLEMENTED",
        "proposal_sha256": PROPOSAL_HASHES,
        "items": sorted(ITEMS),
        "recipes": sorted(RECIPES),
        "entity_loot_tables": sorted(CREATURE_LOOT),
        "plant_acquisition_tables": sorted(PLANT_LOOT),
        "packet006_recipe_links": ["surveyor_staff", "trail_compass", "surveyor_medallion", "warden_sigil"],
        "guards": {"w1_creative_005": "DEFERRED_ABSENT", "natural_wind_roc_storm_pinion": "FORBIDDEN", "new_subscriptions": False, "new_schema": False},
        "proof_boundary": "SOURCE_AND_TARGETED_LOCAL_TESTS_ONLY_NO_BDS_CLIENT_OR_CANDIDATE_CLAIM",
    }
    write_json(Path(__file__).parent / "SKYREACH_APPROVED_VERTICAL_REPORT.json", report)


if __name__ == "__main__":
    main()
