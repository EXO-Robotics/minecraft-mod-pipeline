#!/usr/bin/env python3
"""Author the ratified Crystal Marsh economy and Packet 006 base equipment.

This lane owns declarative pack leaves only. Pearl Depths terminal state,
per-player mask entitlement/recovery, Codex, and shared runtime handlers remain
outside this module. Natural Marsh Wights can never grant the chapter seal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
NATIVE = ROOT / "engineering/native-assets/crystal-marsh/equipment/evidence"
BASE_COMMIT = "6a10cd8a82635299ae62ab8f6b9095c9b793c7a3"
BASE_TREE = "689fa214ae21ab9739a8b6710fdbb5bb00ebeaeb"


EQUIPMENT = {
    "crystal_pike": {"name": "Crystal Pike", "role": "weapon", "idle": "idle_hold"},
    "prism_bow": {"name": "Prism Bow", "role": "weapon", "idle": "idle_hold"},
    "crystal_circlet": {"name": "Crystal Circlet", "role": "armor", "idle": "pulse"},
    "explorer_cloak": {"name": "Explorer Cloak", "role": "armor", "idle": "idle_sway"},
    "crystal_shovel": {"name": "Crystal Shovel", "role": "tool", "idle": "hold"},
    "marsh_sickle": {"name": "Marsh Sickle", "role": "tool", "idle": "hold"},
    "crystal_talisman": {"name": "Crystal Talisman", "role": "accessory", "idle": "pulse"},
    "marsh_idol": {"name": "Marsh Idol", "role": "accessory", "idle": "idle"},
    "marsh_wight_mask": {"name": "Marsh Wight Mask", "role": "trophy", "idle": "eye_glow"},
    "moon_pearl_pedestal": {"name": "Moon Pearl Pedestal", "role": "trophy", "idle": "soft_pulse"},
    "crystal_obelisk_fragment": {"name": "Crystal Obelisk Fragment", "role": "trophy", "idle": "pulse"},
}

COMPONENTS = {
    "prism_wing": "Prism Wing",
    "watcher_lens": "Watcher Lens",
    "wight_shroud": "Wight Shroud",
    "crystal_pole": "Crystal Pole",
    "living_crystal_core": "Living Crystal Core",
    "wet_plate": "Wet Plate",
}

RESOURCE_BLOCKS = {
    "algae_block": [("aionbound:algae_block", 1.0, 1, 1), ("aionbound:glass_algae", .75, 1, 2)],
    "crystal_gravel": [("aionbound:crystal_gravel", 1.0, 1, 1), ("aionbound:silt_core", .10, 1, 1)],
    "crystal_log": [("aionbound:crystal_log", 1.0, 1, 1), ("aionbound:crystal_root_item", .12, 1, 1)],
    "crystal_stone": [("aionbound:crystal_stone", 1.0, 1, 1), ("aionbound:flood_crystal", .10, 1, 1)],
    "flood_planks": [("aionbound:flood_planks", 1.0, 1, 1)],
    "glass_root_block": [("aionbound:glass_root_block", 1.0, 1, 1), ("aionbound:crystal_root_item", .10, 1, 1)],
    "marsh_soil": [("aionbound:marsh_soil", 1.0, 1, 1), ("aionbound:marsh_resin", .08, 1, 1)],
    "marsh_wood": [("aionbound:marsh_wood", 1.0, 1, 1), ("aionbound:marsh_resin", .10, 1, 1)],
    "prism_brick": [("aionbound:prism_brick", 1.0, 1, 1)],
    "wet_clay_block": [("aionbound:wet_clay_block", 1.0, 1, 1), ("aionbound:silt_core", .10, 1, 1)],
}

PLANT_LOOT = {
    "pearl_grass": [("aionbound:pearl_grass", 1.0, 1, 1), ("aionbound:moon_pearl", .08, 1, 1)],
    "marsh_fern": [("aionbound:marsh_fern", 1.0, 1, 1), ("aionbound:marsh_resin", .25, 1, 1)],
    "flood_reed": [("aionbound:flood_reed", 1.0, 1, 1), ("aionbound:crystal_reed_item", .75, 1, 2)],
    "glass_moss": [("aionbound:glass_moss", 1.0, 1, 1), ("aionbound:glass_algae", .75, 1, 2)],
    "glow_kelp": [("aionbound:glow_kelp", 1.0, 1, 1), ("aionbound:glass_algae", 1.0, 1, 2)],
    "bubble_pod": [("aionbound:bubble_pod", 1.0, 1, 1), ("aionbound:marsh_resin", .25, 1, 1)],
    "crystal_lily": [("aionbound:crystal_lily", 1.0, 1, 1), ("aionbound:moon_pearl", .12, 1, 1)],
    "crystal_vine": [("aionbound:crystal_vine", 1.0, 1, 1), ("aionbound:marsh_resin", .75, 1, 2)],
    "mire_orchid": [("aionbound:mire_orchid", 1.0, 1, 1), ("aionbound:mire_bloom_item", .75, 1, 1)],
    "prism_bloom": [("aionbound:prism_bloom", 1.0, 1, 1), ("aionbound:flood_crystal", .40, 1, 1), ("aionbound:prism_pearl", .08, 1, 1)],
}

# C=.75-1.0, U=.25-.55, normal R=.08-.20, elite R=.35-.65,
# elite E=.08-.20. Curiosity prose remains Codex-only and creates no item.
ENTITY_LOOT = {
    "prism_frog": [("aionbound:marsh_resin", 1.0, 1, 2), ("aionbound:flood_crystal", .30, 1, 1)],
    "crystal_newt": [("aionbound:wet_chitin", 1.0, 1, 2), ("aionbound:glass_algae", .75, 1, 2)],
    "crystal_dragonfly": [("aionbound:flood_crystal", .75, 1, 1), ("aionbound:prism_wing", .35, 1, 1)],
    "bloom_crab": [("aionbound:marsh_resin", 1.0, 1, 2), ("aionbound:wet_chitin", .75, 1, 2), ("aionbound:prism_pearl", .25, 1, 1)],
    "mire_turtle": [("aionbound:glass_algae", 1.0, 1, 2), ("aionbound:wet_chitin", .40, 1, 1), ("aionbound:silt_core", .12, 1, 1)],
    "glass_heron": [("aionbound:flood_crystal", .45, 1, 2), ("aionbound:flood_crystal", .18, 1, 1)],
    "reed_serpent": [("aionbound:wet_chitin", 1.0, 1, 2), ("aionbound:crystal_reed_item", .45, 1, 2), ("aionbound:flood_crystal", .12, 1, 1)],
    "silt_crocodile": [("aionbound:wet_chitin", .55, 1, 2), ("aionbound:silt_core", .50, 1, 1), ("aionbound:prism_pearl", .12, 1, 1)],
    "bog_watcher": [("aionbound:marsh_resin", 1.0, 1, 2), ("aionbound:flood_crystal", .50, 1, 2), ("aionbound:watcher_lens", .50, 1, 1)],
    # Ecology-only. The Pearl Depths service exclusively owns mask entitlement.
    "marsh_wight": [("aionbound:wight_shroud", .50, 1, 1), ("aionbound:prism_pearl", .50, 1, 2), ("aionbound:moon_pearl", .35, 1, 1), ("aionbound:flood_crystal", .50, 1, 2), ("aionbound:crystal_root_item", .35, 1, 1)],
}


def e(item: str, weight: int, low: int = 1, high: int = 1) -> tuple[str, int, int, int]:
    return item, weight, low, high


CHESTS = {
    "flooded_dock": ("standard_structure", 1, (2, 4), [e("aionbound:crystal_reed_item", 40, 1, 3), e("aionbound:glass_algae", 35, 1, 2), e("aionbound:marsh_resin", 25, 1, 2)], [e("aionbound:crystal_reed_item", 30, 1, 3), e("aionbound:wet_chitin", 25), e("aionbound:glass_algae", 25, 1, 2), e("aionbound:marsh_sickle", 10), e("aionbound:flood_crystal", 10)]),
    "ancient_boat": ("landmark_structure", 2, (2, 4), [e("aionbound:crystal_reed_item", 45, 1, 3), e("aionbound:flood_planks", 35, 2, 4), e("aionbound:marsh_resin", 20, 1, 2)], [e("aionbound:wet_chitin", 28, 1, 2), e("aionbound:glass_algae", 25, 1, 2), e("aionbound:flood_crystal", 22), e("aionbound:moon_pearl", 15), e("aionbound:marsh_sickle", 10)]),
    "marsh_broken_bridge": ("standard_structure", 1, (2, 4), [e("aionbound:flood_planks", 45, 2, 4), e("aionbound:crystal_reed_item", 30, 1, 3), e("aionbound:wet_chitin", 25, 1, 2)], [e("aionbound:wet_chitin", 30, 1, 2), e("aionbound:marsh_resin", 25, 1, 2), e("aionbound:glass_algae", 20, 1, 2), e("aionbound:moon_pearl", 15), e("aionbound:silt_core", 10)]),
    "pearl_cairn": ("minor_cache", 1, (1, 2), [e("aionbound:glass_algae", 45, 1, 2), e("aionbound:marsh_resin", 35, 1, 2), e("aionbound:flood_crystal", 20)], [e("aionbound:moon_pearl", 35), e("aionbound:prism_pearl", 15), e("aionbound:flood_crystal", 25), e("aionbound:glass_algae", 25, 1, 2)]),
    "crystal_arch": ("landmark_structure", 2, (2, 4), [e("aionbound:flood_crystal", 55, 1, 3), e("aionbound:crystal_stone", 25, 1, 3), e("aionbound:prism_brick", 20, 1, 2)], [e("aionbound:flood_crystal", 35, 1, 3), e("aionbound:crystal_root_item", 25), e("aionbound:moon_pearl", 20), e("aionbound:prism_pearl", 10), e("aionbound:silt_core", 10)]),
    "crystal_obelisk": ("landmark_structure", 2, (2, 4), [e("aionbound:flood_crystal", 50, 1, 3), e("aionbound:crystal_root_item", 30, 1, 2), e("aionbound:prism_brick", 20, 1, 2)], [e("aionbound:flood_crystal", 30, 1, 2), e("aionbound:crystal_root_item", 25), e("aionbound:moon_pearl", 20), e("aionbound:prism_pearl", 15), e("aionbound:crystal_obelisk_fragment", 10)]),
    "ruined_observatory": ("landmark_structure", 2, (2, 4), [e("aionbound:flood_crystal", 45, 1, 2), e("aionbound:crystal_root_item", 35, 1, 2), e("aionbound:prism_brick", 20, 1, 2)], [e("aionbound:watcher_lens", 25), e("aionbound:moon_pearl", 25), e("aionbound:prism_pearl", 15), e("aionbound:crystal_obelisk_fragment", 10), e("aionbound:silt_core", 25)]),
    # Protected cache: authored table exists, but no static structure NBT binds it.
    "pearl_depths": ("apex_arena_chest", 2, (2, 4), [e("aionbound:flood_crystal", 45, 1, 3), e("aionbound:crystal_root_item", 30, 1, 2), e("aionbound:wight_shroud", 25)], [e("aionbound:prism_pearl", 30, 1, 2), e("aionbound:moon_pearl", 25, 1, 2), e("aionbound:wight_shroud", 20), e("aionbound:watcher_lens", 15), e("aionbound:silt_core", 10)]),
}

RECIPES = {
    "mire_bloom_cyan_dye": (["aionbound:mire_bloom_item"], "minecraft:cyan_dye"),
    "crystal_pole": (["aionbound:flood_crystal", "aionbound:crystal_reed_item", "aionbound:crystal_reed_item"], "aionbound:crystal_pole"),
    "living_crystal_core": (["aionbound:crystal_root_item", "aionbound:moon_pearl"], "aionbound:living_crystal_core"),
    "wet_plate": (["aionbound:wet_chitin", "aionbound:wet_chitin", "aionbound:marsh_resin"], "aionbound:wet_plate"),
    "crystal_pike": (["aionbound:crystal_pole", "aionbound:flood_crystal"], "aionbound:crystal_pike"),
    "prism_bow": (["aionbound:flood_crystal", "aionbound:flood_crystal", "aionbound:prism_wing", "aionbound:glass_algae"], "aionbound:prism_bow"),
    "crystal_circlet": (["aionbound:living_crystal_core", "aionbound:watcher_lens", "aionbound:widow_silk"], "aionbound:crystal_circlet"),
    "explorer_cloak": (["aionbound:wet_chitin", "aionbound:wet_chitin", "aionbound:whisper_bark", "aionbound:glass_algae"], "aionbound:explorer_cloak"),
    "crystal_shovel": (["aionbound:silt_core", "aionbound:crystal_reed_item", "aionbound:crystal_reed_item"], "aionbound:crystal_shovel"),
    "marsh_sickle": (["aionbound:wet_plate", "aionbound:flood_crystal", "aionbound:crystal_reed_item"], "aionbound:marsh_sickle"),
    "crystal_talisman": (["aionbound:flood_crystal", "aionbound:prism_pearl"], "aionbound:crystal_talisman"),
    "marsh_idol": (["aionbound:marsh_wood", "aionbound:mire_orchid", "aionbound:marsh_resin"], "aionbound:marsh_idol"),
    "moon_pearl_pedestal": (["aionbound:moon_pearl", "aionbound:prism_brick", "aionbound:prism_brick", "aionbound:prism_brick"], "aionbound:moon_pearl_pedestal"),
}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loot_pool(item: str, chance: float, low: int, high: int) -> dict:
    entry = {"type": "item", "name": item, "weight": 1}
    if low != 1 or high != 1:
        entry["functions"] = [{"function": "set_count", "count": low if low == high else {"min": low, "max": high}}]
    pool = {"rolls": 1, "entries": [entry]}
    if chance < 1:
        pool["conditions"] = [{"condition": "random_chance", "chance": chance}]
    return pool


def weighted(item: str, weight: int, low: int, high: int) -> dict:
    value = {"type": "item", "name": item, "weight": weight}
    if low != 1 or high != 1:
        value["functions"] = [{"function": "set_count", "count": low if low == high else {"min": low, "max": high}}]
    return value


def chest_doc(spec: tuple) -> dict:
    _band, guaranteed, choice_rolls, fixed, choice = spec
    return {"pools": [
        {"rolls": guaranteed, "entries": [weighted(*row) for row in fixed]},
        {"rolls": {"min": choice_rolls[0], "max": choice_rolls[1]}, "entries": [weighted(*row) for row in choice]},
    ]}


def item_doc(asset: str, name: str, role: str) -> dict:
    components: dict[str, object] = {
        "minecraft:display_name": {"value": name},
        "minecraft:icon": {"textures": {"default": asset}},
        "minecraft:max_stack_size": 1,
    }
    if role in {"weapon", "tool"}:
        components["minecraft:hand_equipped"] = True
    if asset == "crystal_pike":
        components.update({"minecraft:damage": 6, "minecraft:durability": {"max_durability": 400}, "minecraft:repairable": {"repair_items": [{"items": ["aionbound:flood_crystal"], "repair_amount": 80}]}})
    elif asset == "prism_bow":
        components.update({"minecraft:damage": 4, "minecraft:durability": {"max_durability": 420}, "minecraft:cooldown": {"category": "aionbound_prism_bow", "duration": 1.0}, "minecraft:use_modifiers": {"use_duration": .5, "movement_modifier": .65}, "minecraft:repairable": {"repair_items": [{"items": ["aionbound:prism_wing"], "repair_amount": 70}]}})
    elif asset == "crystal_circlet":
        components.update({"minecraft:durability": {"max_durability": 210}, "minecraft:repairable": {"repair_items": [{"items": ["aionbound:living_crystal_core"], "repair_amount": 42}]}, "minecraft:wearable": {"slot": "slot.armor.head", "protection": 2}})
    elif asset == "explorer_cloak":
        components.update({"minecraft:durability": {"max_durability": 260}, "minecraft:repairable": {"repair_items": [{"items": ["aionbound:wet_chitin"], "repair_amount": 52}]}, "minecraft:wearable": {"slot": "slot.armor.chest", "protection": 3}})
    elif asset == "crystal_shovel":
        components.update({"minecraft:damage": 4, "minecraft:durability": {"max_durability": 360}, "minecraft:digger": {"destroy_speeds": [{"block": {"tags": "query.any_tag('dirt', 'sand', 'gravel')"}, "speed": 6}, {"block": "aionbound:marsh_soil", "speed": 8}, {"block": "aionbound:wet_clay_block", "speed": 8}, {"block": "aionbound:crystal_gravel", "speed": 8}], "use_efficiency": True}, "minecraft:repairable": {"repair_items": [{"items": ["aionbound:silt_core"], "repair_amount": 72}]}})
    elif asset == "marsh_sickle":
        components.update({"minecraft:damage": 4, "minecraft:durability": {"max_durability": 320}, "minecraft:digger": {"destroy_speeds": [{"block": {"tags": "query.any_tag('plant', 'leaves')"}, "speed": 6}, *({"block": f"aionbound:{plant}", "speed": 8} for plant in PLANT_LOOT)], "use_efficiency": True}, "minecraft:repairable": {"repair_items": [{"items": ["aionbound:wet_plate"], "repair_amount": 64}]}})
    elif role == "accessory":
        components["minecraft:wearable"] = {"slot": "slot.weapon.offhand"}
    return {"format_version": "1.21.80", "minecraft:item": {"description": {"identifier": f"aionbound:{asset}", "menu_category": {"category": "equipment"}}, "components": components}}


def component_doc(asset: str, name: str) -> dict:
    return {"format_version": "1.21.80", "minecraft:item": {"description": {"identifier": f"aionbound:{asset}", "menu_category": {"category": "items"}}, "components": {"minecraft:display_name": {"value": name}, "minecraft:icon": {"textures": {"default": asset}}, "minecraft:max_stack_size": 64}}}


def trophy_doc(asset: str, name: str) -> dict:
    return {"format_version": "1.21.80", "minecraft:block": {"description": {"identifier": f"aionbound:{asset}", "menu_category": {"category": "construction"}}, "components": {"minecraft:display_name": name, "minecraft:collision_box": {"origin": [-6, 0, -6], "size": [12, 12, 12]}, "minecraft:selection_box": {"origin": [-7, 0, -7], "size": [14, 14, 14]}, "minecraft:geometry": f"geometry.aionbound.{asset}", "minecraft:material_instances": {"*": {"texture": asset, "render_method": "alpha_test"}}, "minecraft:placement_filter": {"conditions": [{"allowed_faces": ["up"], "block_filter": ["minecraft:stone", "minecraft:mud", "minecraft:clay", "aionbound:crystal_stone", "aionbound:prism_brick", "aionbound:marsh_soil"]}]}, "minecraft:loot": f"loot_tables/blocks/{asset}.json"}}}


def attachable_doc(asset: str, animation_names: list[str], idle: str) -> dict:
    short = {name.rsplit(".", 1)[-1]: name for name in animation_names}
    return {"format_version": "1.10.0", "minecraft:attachable": {"description": {"identifier": f"aionbound:{asset}", "materials": {"default": "entity_alphatest"}, "textures": {"default": f"textures/aionbound/crystal_marsh/equipment/models/{asset}"}, "geometry": {"default": f"geometry.aionbound.{asset}"}, "render_controllers": ["controller.render.aionbound.default"], "animations": short, "scripts": {"animate": [idle]}}}}


def recipe_doc(asset: str, ingredients: list[str], result: str) -> dict:
    return {"format_version": "1.20.10", "minecraft:recipe_shapeless": {"description": {"identifier": f"aionbound:{asset}_recipe"}, "tags": ["crafting_table"], "ingredients": [{"item": item} for item in ingredients], "result": {"item": result, "count": 1}, "unlock": [{"item": ingredients[0]}]}}


def icon(asset: str, output: Path) -> None:
    """Draw a distinct, transparent, pixel-readable Crystal Marsh icon."""
    seed = int(hashlib.sha256(asset.encode()).hexdigest()[:8], 16)
    dark = (24 + seed % 18, 49 + (seed >> 4) % 24, 55 + (seed >> 8) % 20, 255)
    teal = (45 + (seed >> 12) % 34, 150 + (seed >> 16) % 48, 154 + (seed >> 20) % 38, 255)
    mint = (128 + (seed >> 7) % 44, 226, 207 + (seed >> 11) % 36, 255)
    pearl = (218, 235, 239, 255)
    purple = (125 + (seed >> 5) % 46, 92, 186 + (seed >> 9) % 42, 255)
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if asset in {"crystal_pike", "crystal_pole", "crystal_shovel"}:
        d.line((8, 27, 23, 6), fill=dark, width=4)
        d.line((9, 27, 24, 6), fill=teal, width=2)
        tip = [(21, 8), (25, 3), (27, 9), (23, 12)] if asset != "crystal_shovel" else [(19, 8), (25, 4), (28, 9), (23, 13)]
        d.polygon(tip, fill=mint, outline=pearl)
    elif asset in {"prism_bow", "prism_wing"}:
        d.arc((5, 3, 26, 29), 70, 290, fill=teal, width=4)
        d.line((10, 5, 10, 27), fill=pearl, width=1)
        d.polygon([(15, 16), (24, 9), (21, 17), (26, 24)], fill=mint, outline=purple)
    elif asset in {"crystal_circlet", "watcher_lens"}:
        d.arc((5, 9, 27, 28), 195, 345, fill=teal, width=4)
        d.polygon([(16, 5), (22, 14), (16, 19), (10, 14)], fill=purple, outline=mint)
        d.ellipse((13, 10, 19, 16), fill=pearl)
    elif asset == "explorer_cloak":
        d.polygon([(12, 4), (20, 4), (25, 27), (7, 27)], fill=dark, outline=teal)
        d.polygon([(15, 8), (19, 8), (22, 23), (11, 23)], fill=purple)
    elif asset in {"marsh_sickle", "wet_plate"}:
        d.line((10, 27, 17, 14), fill=dark, width=4)
        d.arc((10, 3, 28, 21), 90, 255, fill=mint, width=5)
        if asset == "wet_plate": d.rectangle((8, 11, 24, 25), fill=teal, outline=pearl)
    elif asset in {"crystal_talisman", "living_crystal_core"}:
        d.line((9, 5, 23, 5), fill=dark, width=2)
        d.polygon([(16, 8), (24, 16), (16, 27), (8, 16)], fill=teal, outline=pearl)
        d.polygon([(16, 11), (20, 16), (16, 22), (12, 16)], fill=purple)
    elif asset in {"marsh_idol", "marsh_wight_mask"}:
        d.polygon([(9, 6), (23, 6), (26, 16), (21, 27), (11, 27), (6, 16)], fill=dark, outline=teal)
        d.rectangle((10, 13, 14, 16), fill=mint)
        d.rectangle((18, 13, 22, 16), fill=mint)
        d.line((16, 16, 16, 23), fill=purple, width=2)
    elif asset == "moon_pearl_pedestal":
        d.rectangle((8, 24, 24, 28), fill=dark, outline=teal)
        d.polygon([(11, 24), (14, 13), (18, 13), (21, 24)], fill=purple, outline=teal)
        d.ellipse((10, 4, 22, 16), fill=pearl, outline=mint)
    elif asset == "crystal_obelisk_fragment":
        d.rectangle((7, 25, 25, 28), fill=dark)
        d.polygon([(12, 25), (10, 13), (17, 4), (22, 11), (19, 25)], fill=purple, outline=mint)
    elif asset == "wight_shroud":
        d.polygon([(11, 5), (21, 5), (26, 28), (18, 24), (14, 28), (6, 25)], fill=dark, outline=teal)
        d.line((12, 9, 20, 9), fill=mint, width=2)
    else:
        d.polygon([(16, 4), (26, 14), (21, 27), (10, 25), (6, 13)], fill=teal, outline=mint)
    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output, format="PNG", optimize=False)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def replace_owned_language_entries(lines: list[str], entries: list[str], prefixes: list[str]) -> list[str]:
    """Replace Crystal-owned keys in place without reordering later verticals."""
    owned_indexes = [
        index for index, line in enumerate(lines)
        if any(line.startswith(prefix) for prefix in prefixes)
    ]
    insertion = owned_indexes[0] if owned_indexes else len(lines)
    preserved = [
        line for line in lines
        if not any(line.startswith(prefix) for prefix in prefixes)
    ]
    return preserved[:insertion] + entries + preserved[insertion:]


def author() -> dict:
    item_atlas_path = RP / "textures/item_texture.json"
    terrain_atlas_path = RP / "textures/terrain_texture.json"
    item_atlas = json.loads(item_atlas_path.read_text())
    terrain_atlas = json.loads(terrain_atlas_path.read_text())
    lang_path = RP / "texts/en_US.lang"
    lines = lang_path.read_text().splitlines()
    owned = [*(f"item.aionbound:{x}.name=" for x in COMPONENTS), *(f"item.aionbound:{x}.name=" for x, v in EQUIPMENT.items() if v["role"] != "trophy"), *(f"tile.aionbound:{x}.name=" for x, v in EQUIPMENT.items() if v["role"] == "trophy")]
    language_entries: list[str] = []

    for asset, spec in EQUIPMENT.items():
        evidence = NATIVE / asset
        geometry = evidence / "native-exports/pass-2.geo.json"
        animation = evidence / "native-exports/pass-2.animation.json"
        model_uv = evidence / "native-project/textures" / f"{asset}.png"
        for source in (geometry, animation, model_uv):
            if not source.is_file(): raise FileNotFoundError(source)
        geo_target = RP / "models/aionbound/crystal_marsh/equipment" / f"{asset}.geo.json"
        anim_target = RP / "animations/aionbound/crystal_marsh/equipment" / f"{asset}.animation.json"
        uv_target = RP / "textures/aionbound/crystal_marsh/equipment/models" / f"{asset}.png"
        for target in (geo_target, anim_target, uv_target): target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(geometry, geo_target); shutil.copyfile(animation, anim_target); shutil.copyfile(model_uv, uv_target)
        animation_names = sorted(json.loads(animation.read_text())["animations"])
        write_json(RP / "attachables" / f"{asset}.attachable.json", attachable_doc(asset, animation_names, spec["idle"]))
        role = spec["role"]
        if role == "trophy":
            write_json(BP / "blocks" / f"{asset}.block.json", trophy_doc(asset, spec["name"]))
            write_json(BP / "loot_tables/blocks" / f"{asset}.json", {"pools": [loot_pool(f"aionbound:{asset}", 1.0, 1, 1)]})
            trophy_uv = RP / "textures/aionbound/wave1/equipment/trophies" / f"{asset}.png"
            trophy_uv.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(model_uv, trophy_uv)
            terrain_atlas["texture_data"][asset] = {"textures": f"textures/aionbound/wave1/equipment/trophies/{asset}"}
            presentation = RP / "textures/aionbound/crystal_marsh/equipment/presentation/trophies" / f"{asset}.png"
            icon(asset, presentation)
            item_atlas["texture_data"][asset] = {"textures": f"textures/aionbound/crystal_marsh/equipment/presentation/trophies/{asset}"}
            language_entries.append(f"tile.aionbound:{asset}.name={spec['name']}")
        else:
            write_json(BP / "items" / f"{asset}.item.json", item_doc(asset, spec["name"], role))
            group = "armor" if role == "armor" else "accessories" if role == "accessory" else "items"
            presentation = RP / f"textures/aionbound/wave1/equipment/{group}/{asset}.png"
            icon(asset, presentation)
            item_atlas["texture_data"][asset] = {"textures": f"textures/aionbound/wave1/equipment/{group}/{asset}"}
            language_entries.append(f"item.aionbound:{asset}.name={spec['name']}")

    for asset, name in COMPONENTS.items():
        write_json(BP / "items" / f"{asset}.item.json", component_doc(asset, name))
        presentation = RP / "textures/aionbound/crystal_marsh/components" / f"{asset}.png"
        icon(asset, presentation)
        item_atlas["texture_data"][asset] = {"textures": f"textures/aionbound/crystal_marsh/components/{asset}"}
        language_entries.append(f"item.aionbound:{asset}.name={name}")

    for recipe_id, (ingredients, result) in RECIPES.items():
        write_json(BP / "recipes" / f"{recipe_id}.recipe.json", recipe_doc(recipe_id, ingredients, result))
    for entity_id, rows in ENTITY_LOOT.items():
        write_json(BP / "loot_tables/entities/crystal" / f"{entity_id}.json", {"pools": [loot_pool(*row) for row in rows]})
    for block_id, rows in {**RESOURCE_BLOCKS, **PLANT_LOOT}.items():
        write_json(BP / "loot_tables/blocks" / f"{block_id}.json", {"pools": [loot_pool(*row) for row in rows]})
    for block_id in RESOURCE_BLOCKS:
        path = BP / "blocks" / f"{block_id}.block.json"
        doc = json.loads(path.read_text())
        doc["minecraft:block"]["components"]["minecraft:loot"] = f"loot_tables/blocks/{block_id}.json"
        write_json(path, doc)
    for structure, spec in CHESTS.items():
        write_json(BP / "loot_tables/chests/crystal" / f"{structure}.json", chest_doc(spec))
    write_json(BP / "loot_tables/encounters/crystal/pearl_depths_materials.json", {"pools": [
        {"rolls": {"min": 2, "max": 4}, "entries": [weighted("aionbound:wight_shroud", 30, 1, 1), weighted("aionbound:flood_crystal", 40, 1, 3), weighted("aionbound:crystal_root_item", 30, 1, 2)]},
        {"rolls": {"min": 1, "max": 2}, "entries": [weighted("aionbound:prism_pearl", 55, 1, 2), weighted("aionbound:moon_pearl", 45, 1, 2)]},
    ]})
    write_json(item_atlas_path, item_atlas); write_json(terrain_atlas_path, terrain_atlas)
    lines = replace_owned_language_entries(lines, language_entries, owned)
    lang_path.write_text("\n".join(lines) + "\n")

    files = sorted({*([BP / "items" / f"{x}.item.json" for x in COMPONENTS]), *([BP / "items" / f"{x}.item.json" for x, v in EQUIPMENT.items() if v["role"] != "trophy"]), *([BP / "blocks" / f"{x}.block.json" for x, v in EQUIPMENT.items() if v["role"] == "trophy"]), *list((BP / "loot_tables/entities/crystal").glob("*.json")), *list((BP / "loot_tables/chests/crystal").glob("*.json")), *([BP / "recipes" / f"{x}.recipe.json" for x in RECIPES])})
    report = {
        "schema": "aionforge.wave1.crystal_marsh.economy_equipment.v1",
        "status": "SOURCE_COMPLETE_TARGETED_STATIC_PASS",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "authority": ["W1-001-CM", "W1-004-CM"],
        "w1_creative_005": "DEFERRED_UNCHANGED_NO_SIDEGRADES",
        "counts": {"equipment": len(EQUIPMENT), "components_and_new_drops": len(COMPONENTS), "recipes": len(RECIPES), "entity_tables": len(ENTITY_LOOT), "plant_tables": len(PLANT_LOOT), "resource_block_tables": len(RESOURCE_BLOCKS), "structure_tables": len(CHESTS)},
        "soft_craft": {"source": "aionbound:mire_bloom_item", "result": "minecraft:cyan_dye", "consumable_effect": "WITHHELD_NO_EXACT_EFFECT_AUTHORITY"},
        "ecology_guard": {"natural_marsh_wight_table": "loot_tables/entities/crystal/marsh_wight.json", "forbidden": ["aionbound:marsh_wight_mask", "Pearl Depths completion", "seal credit", "reward entitlement"]},
        "protected_pearl_depths": {"material_table": "loot_tables/encounters/crystal/pearl_depths_materials.json", "apex_chest": "loot_tables/chests/crystal/pearl_depths.json", "contains_mask": False, "static_structure_binding": False, "terminal_owner": "PEARL_DEPTHS_SERVICE_ONLY"},
        "mastery": {"optional_only": ["aionbound:moon_pearl_pedestal", "aionbound:crystal_obelisk_fragment", "aionbound:marsh_idol"], "pilgrim_seal_substitute": False},
        "post_merge_bindings": {"entities": "add minecraft:loot to the ten creature BP definitions after creature-lane merge", "plants": "plant lane owns minecraft:loot components pointing to these ten committed tables", "ordinary_structure_nbt": "bind only seven ordinary barrel anchors; keep deep_pool_entrance protected cache empty"},
        "artifacts": [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in files],
        "proof_boundary": "STATIC JSON, NATIVE PASS-2 BYTE BINDING, PNG DECODE, ECONOMY ENVELOPE, AND SEMANTIC TESTS ONLY; NO SHARED RUNTIME, BDS, CLIENT, MULTIPLAYER, CONSOLE, CANDIDATE, OR TERMINAL REWARD PROOF",
    }
    write_json(HERE / "CRYSTAL_ECONOMY_EQUIPMENT_REPORT.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); args = parser.parse_args()
    before = None
    if args.check:
        before = hashlib.sha256((HERE / "CRYSTAL_ECONOMY_EQUIPMENT_REPORT.json").read_bytes()).hexdigest()
    report = author()
    if args.check and hashlib.sha256((HERE / "CRYSTAL_ECONOMY_EQUIPMENT_REPORT.json").read_bytes()).hexdigest() != before:
        raise SystemExit("nondeterministic report")
    print(json.dumps({"status": report["status"], "counts": report["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
