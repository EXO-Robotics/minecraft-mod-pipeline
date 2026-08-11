#!/usr/bin/env python3
"""Bind native-passed Whisperwood armor, accessories, and trophies to BP/RP."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "engineering/native-assets/whisperwood/equipment-b"
ARMOR = {
    "whisperwood_helmet": ("Whisperwood Helmet", "slot.armor.head", 1, 165, 40),
    "whisperwood_chest": ("Whisperwood Chest", "slot.armor.chest", 3, 240, 60),
    "whisperwood_legs": ("Whisperwood Legs", "slot.armor.legs", 2, 225, 55),
    "whisperwood_boots": ("Whisperwood Boots", "slot.armor.feet", 1, 195, 50),
}
ACCESSORIES = {
    "moss_charm": "Moss Charm",
    "root_bracelet": "Root Bracelet",
    "lantern_badge": "Lantern Badge",
    "moon_sap_pendant": "Moon Sap Pendant",
    "briar_ring": "Briar Ring",
}
TROPHIES = {
    "thorn_stalker_skull": "Thorn Stalker Skull",
    "briar_elk_trophy": "Briar Elk Trophy",
    "mosskip_trophy": "Mosskip Trophy",
    "ancient_acorn_display": "Ancient Acorn Display",
}
CLIPS = {"moss_charm": "idle_sway", "moon_sap_pendant": "pulse"}


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def native_paths(asset: str) -> tuple[Path, Path]:
    evidence = NATIVE / "evidence" / asset
    return evidence / "native-exports/pass-2.geo.json", evidence / "native-exports/pass-2.animation.json"


def copy_visual(asset: str, category: str) -> None:
    geo, animation = native_paths(asset)
    texture = NATIVE / "inputs" / asset / "textures" / f"{asset}.png"
    model_dir = "blocks" if category == "trophies" else "aionbound/equipment"
    target_model = ROOT / "resource_pack/models" / model_dir / f"{asset}.geo.json"
    target_model.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(geo, target_model)
    target_texture = ROOT / "resource_pack/textures/aionbound/whisperwood/equipment/models" / f"{asset}.png"
    target_texture.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(texture, target_texture)
    if asset in CLIPS:
        target_animation = ROOT / "resource_pack/animations/aionbound/equipment" / f"{asset}.animation.json"
        target_animation.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(animation, target_animation)


def attachable(asset: str, category: str) -> dict:
    description = {
        "identifier": f"aionbound:{asset}",
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/aionbound/whisperwood/equipment/models/{asset}"},
        "geometry": {"default": f"geometry.aionbound.{asset}"},
        "render_controllers": ["controller.render.aionbound.default"],
    }
    if asset in CLIPS:
        clip = CLIPS[asset]
        description["animations"] = {clip: f"animation.aionbound.{asset}.{clip}"}
        description["scripts"] = {"animate": [clip]}
    return {"format_version": "1.10.0", "minecraft:attachable": {"description": description}}


def main() -> int:
    item_atlas_path = ROOT / "resource_pack/textures/item_texture.json"
    terrain_atlas_path = ROOT / "resource_pack/textures/terrain_texture.json"
    item_atlas, terrain_atlas = json.loads(item_atlas_path.read_text()), json.loads(terrain_atlas_path.read_text())
    lang_path = ROOT / "resource_pack/texts/en_US.lang"
    lang_lines = lang_path.read_text().splitlines()
    owned_keys = {f"item.aionbound:{asset}.name=" for asset in (*ARMOR, *ACCESSORIES)} | {f"tile.aionbound:{asset}.name=" for asset in TROPHIES}
    lang_lines = [line for line in lang_lines if not any(line.startswith(key) for key in owned_keys)]
    for asset, (name, slot, protection, durability, repair) in ARMOR.items():
        copy_visual(asset, "armor")
        write(ROOT / "behavior_pack/items" / f"{asset}.item.json", {
            "format_version": "1.21.80",
            "minecraft:item": {
                "description": {"identifier": f"aionbound:{asset}", "menu_category": {"category": "equipment"}},
                "components": {
                    "minecraft:display_name": {"value": name},
                    "minecraft:icon": {"textures": {"default": asset}},
                    "minecraft:max_stack_size": 1,
                    "minecraft:durability": {"max_durability": durability},
                    "minecraft:repairable": {"repair_items": [{"items": ["aionbound:moss_resin"], "repair_amount": repair}]},
                    "minecraft:wearable": {"slot": slot, "protection": protection},
                },
            },
        })
        write(ROOT / "resource_pack/attachables" / f"{asset}.attachable.json", attachable(asset, "armor"))
        item_atlas["texture_data"][asset] = {"textures": f"textures/aionbound/whisperwood/equipment/{asset}"}
        lang_lines.append(f"item.aionbound:{asset}.name={name}")
    for asset, name in ACCESSORIES.items():
        copy_visual(asset, "accessories")
        write(ROOT / "behavior_pack/items" / f"{asset}.item.json", {
            "format_version": "1.21.80",
            "minecraft:item": {
                "description": {"identifier": f"aionbound:{asset}", "menu_category": {"category": "equipment"}},
                "components": {
                    "minecraft:display_name": {"value": name},
                    "minecraft:icon": {"textures": {"default": asset}},
                    "minecraft:max_stack_size": 1,
                    "minecraft:wearable": {"slot": "slot.weapon.offhand"},
                },
            },
        })
        write(ROOT / "resource_pack/attachables" / f"{asset}.attachable.json", attachable(asset, "accessories"))
        item_atlas["texture_data"][asset] = {"textures": f"textures/aionbound/whisperwood/equipment/{asset}"}
        lang_lines.append(f"item.aionbound:{asset}.name={name}")
    for asset, name in TROPHIES.items():
        copy_visual(asset, "trophies")
        write(ROOT / "behavior_pack/blocks" / f"{asset}.block.json", {
            "format_version": "1.21.80",
            "minecraft:block": {
                "description": {"identifier": f"aionbound:{asset}", "menu_category": {"category": "construction"}},
                "components": {
                    "minecraft:display_name": name,
                    "minecraft:collision_box": {"origin": [-6, 0, -6], "size": [12, 12, 12]},
                    "minecraft:selection_box": {"origin": [-7, 0, -7], "size": [14, 14, 14]},
                    "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.2},
                    "minecraft:geometry": f"geometry.aionbound.{asset}",
                    "minecraft:material_instances": {"*": {"texture": asset, "render_method": "alpha_test"}},
                    "minecraft:placement_filter": {"conditions": [{"allowed_faces": ["up"], "block_filter": ["minecraft:grass_block", "minecraft:dirt", "minecraft:stone", "minecraft:oak_planks", "aionbound:whisperwood_planks", "aionbound:forest_brick"]}]},
                },
            },
        })
        terrain_atlas["texture_data"][asset] = {"textures": f"textures/aionbound/whisperwood/equipment/models/{asset}"}
        lang_lines.append(f"tile.aionbound:{asset}.name={name}")
    write(item_atlas_path, item_atlas)
    write(terrain_atlas_path, terrain_atlas)
    lang_path.write_text("\n".join(lang_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
