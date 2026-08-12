#!/usr/bin/env python3
"""Bind the exact approved Twinbond massing and presentation inputs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
SOURCE = Path("/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/studio-prep")
PROPOSALS = {
    "W1-002-TWINBOND": "0f99a748e55d15bd468d9ded25a0c170972bf94c1682e56c8abb78cde25eda7e",
    "W1-003-TWINBOND": "c22a350499fd2674d3dabedcee8ec5221c4e3e8da4f89666f91cb5a69a43cf1c",
    "W1-004-TWINBOND": "b5ac9295df1718112793d2b15ba035570e1e6032d0da814b9af68a17c27d9a4c",
}
MASSING_SHA = "dc980b99897129e3747409b169e648db4d7b82f9933effbdceeb022a01b6ef6e"
SHELLS = {
    "twin_thrones": "Twin Thrones",
    "ceremony_anvil_site": "Ceremony Anvil Site",
    "twinbond_obsidian_ring": "Twinbond Obsidian Ring",
    "twinbond_approach_marker": "Twinbond Approach Marker",
}
LEGACY_FILES = [
    "behavior_pack/items/finale_ignition_key.item.json",
    "behavior_pack/items/trophy_concord_scale.item.json",
    "behavior_pack/recipes/finale_ignition_key.recipe.json",
    "behavior_pack/recipes/concord_boots.recipe.json",
    "behavior_pack/recipes/roc_pinion_glaive.recipe.json",
    "behavior_pack/recipes/trophy_edge.recipe.json",
    "behavior_pack/feature_rules/twinbond_obelisk_site.feature_rule.json",
    "behavior_pack/features/twinbond_obelisk_site.feature.json",
    "resource_pack/animations/aionbound/finale_ignition_key.animation.json",
    "resource_pack/animations/aionbound/trophy_concord_scale.animation.json",
    "resource_pack/attachables/finale_ignition_key.attachable.json",
    "resource_pack/models/aionbound/finale_ignition_key.geo.json",
    "resource_pack/models/aionbound/trophy_concord_scale.geo.json",
    "resource_pack/textures/aionbound/finale_ignition_key.png",
    "resource_pack/textures/aionbound/trophy_concord_scale.png",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def replace(value: object, old: str, new: str) -> object:
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace(item, old, new) for item in value]
    if isinstance(value, dict):
        return {replace(key, old, new): replace(item, old, new) for key, item in value.items()}
    return value


def shell_block(identifier: str, name: str) -> dict:
    return {
        "format_version": "1.21.80",
        "minecraft:block": {
            "description": {"identifier": f"aionbound:{identifier}"},
            "components": {
                "minecraft:display_name": name,
                "minecraft:destructible_by_mining": {"seconds_to_destroy": 2},
                "minecraft:geometry": f"geometry.aionbound.{identifier}",
                "minecraft:material_instances": {"*": {"texture": identifier, "render_method": "alpha_test"}},
            },
        },
    }


def item(identifier: str, name: str, icon: str) -> dict:
    return {
        "format_version": "1.21.80",
        "minecraft:item": {
            "description": {"identifier": f"aionbound:{identifier}"},
            "components": {
                "minecraft:display_name": {"value": f"item.aionbound:{identifier}.name"},
                "minecraft:icon": {"textures": {"default": icon}},
                "minecraft:max_stack_size": 1,
            },
        },
    }


def memory_icon(path: Path) -> None:
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); draw = ImageDraw.Draw(image)
    colors = [(74, 142, 84, 255), (218, 104, 54, 255), (84, 174, 189, 255), (177, 197, 224, 255)]
    draw.ellipse((3, 3, 28, 28), fill=(35, 31, 48, 255), outline=(228, 188, 82, 255), width=2)
    draw.pieslice((6, 6, 25, 25), 180, 270, fill=colors[0]); draw.pieslice((6, 6, 25, 25), 270, 360, fill=colors[1])
    draw.pieslice((6, 6, 25, 25), 0, 90, fill=colors[2]); draw.pieslice((6, 6, 25, 25), 90, 180, fill=colors[3])
    draw.polygon([(16, 8), (23, 16), (16, 24), (9, 16)], fill=(45, 37, 58, 255), outline=(245, 218, 130, 255))
    draw.rectangle((15, 12, 17, 20), fill=(245, 218, 130, 255)); draw.rectangle((12, 15, 20, 17), fill=(245, 218, 130, 255))
    path.parent.mkdir(parents=True, exist_ok=True); image.save(path, format="PNG", optimize=False)


def author() -> None:
    for ticket, expected in PROPOSALS.items():
        actual = sha(ROOT / f"engineering/authority/support-proposals/finale/{ticket}.json")
        if actual != expected:
            raise RuntimeError(f"{ticket}_HASH_MISMATCH:{actual}")
    massing = SOURCE / "regions/twinbond/massing/twinbond_slice_v1.mcstructure"
    if sha(massing) != MASSING_SHA:
        raise RuntimeError("TWINBOND_MASSING_HASH_MISMATCH")
    target = BP / "structures/aionbound/twinbond_slice_v1.mcstructure"; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(massing, target)

    terrain = json.loads((RP / "textures/terrain_texture.json").read_text())
    blocks = json.loads((RP / "blocks.json").read_text())
    for identifier, name in SHELLS.items():
        source_geometry = SOURCE / f"assets/export/models/{identifier}.geo.json"
        source_animation = SOURCE / f"assets/export/animations/{identifier}.animation.json"
        geometry = replace(json.loads(source_geometry.read_text()), f"geometry.ccr_prep.{identifier}", f"geometry.aionbound.{identifier}")
        animation = replace(json.loads(source_animation.read_text()), f"animation.ccr_prep.{identifier}", f"animation.aionbound.{identifier}")
        write_json(RP / f"models/aionbound/{identifier}.geo.json", geometry)
        write_json(RP / f"animations/aionbound/{identifier}.animation.json", animation)
        shutil.copyfile(SOURCE / f"assets/export/textures/{identifier}.png", RP / f"textures/aionbound/{identifier}.png")
        write_json(BP / f"blocks/{identifier}.block.json", shell_block(identifier, name))
        terrain["texture_data"][identifier] = {"textures": f"textures/aionbound/{identifier}"}
        blocks[f"aionbound:{identifier}"] = {"sound": "stone", "textures": identifier}
    write_json(RP / "textures/terrain_texture.json", terrain); write_json(RP / "blocks.json", blocks)

    # Approach markers retain the established G8 Overworld locality as
    # foreshadow/handoff points. The full finale site itself is never emitted by
    # a feature rule: only the first eligible marker can bind one durable site.
    write_json(BP / "features/twinbond_approach_marker.feature.json", {
        "format_version": "1.13.0", "minecraft:single_block_feature": {
            "description": {"identifier": "aionbound:twinbond_approach_marker"},
            "places_block": "aionbound:twinbond_approach_marker", "enforce_placement_rules": True, "enforce_survivability_rules": True,
        }
    })
    write_json(BP / "feature_rules/twinbond_approach_marker.feature_rule.json", {
        "format_version": "1.13.0", "minecraft:feature_rules": {
            "description": {"identifier": "aionbound:twinbond_approach_marker.feature_rule", "places_feature": "aionbound:twinbond_approach_marker"},
            "conditions": {"placement_pass": "surface_pass", "minecraft:biome_filter": {"test": "has_biome_tag", "operator": "==", "value": "overworld"}},
            "distribution": {"iterations": 1, "scatter_chance": {"numerator": 1, "denominator": 768},
                "x": {"distribution": "uniform", "extent": [0, 15]}, "y": "q.heightmap(v.worldx, v.worldz)", "z": {"distribution": "uniform", "extent": [0, 15]}},
        }
    })

    write_json(BP / "items/trophy_edge_blank.item.json", item("trophy_edge_blank", "Trophy Edge Blank", "trophy_edge_blank"))
    write_json(BP / "items/memory_of_four_lands.item.json", item("memory_of_four_lands", "Memory of Four Lands", "memory_of_four_lands"))
    write_json(RP / "attachables/trophy_edge_blank.attachable.json", {
        "format_version": "1.10.0", "minecraft:attachable": {"description": {
            "identifier": "aionbound:trophy_edge_blank", "materials": {"default": "entity_alphatest"},
            "textures": {"default": "textures/aionbound/trophy_edge_assembled"}, "geometry": {"default": "geometry.aionbound.trophy_edge_assembled"},
            "render_controllers": ["controller.render.aionbound.default"],
        }}
    })
    shutil.copyfile(RP / "textures/aionbound/trophy_edge_preview.png", RP / "textures/aionbound/trophy_edge_blank.png")
    memory_icon(RP / "textures/aionbound/memory_of_four_lands.png")
    atlas = json.loads((RP / "textures/item_texture.json").read_text())
    for legacy in ("finale_ignition_key", "trophy_concord_scale"):
        atlas["texture_data"].pop(legacy, None)
    atlas["texture_data"]["trophy_edge_blank"] = {"textures": "textures/aionbound/trophy_edge_blank"}
    atlas["texture_data"]["memory_of_four_lands"] = {"textures": "textures/aionbound/memory_of_four_lands"}
    write_json(RP / "textures/item_texture.json", atlas)

    language = (RP / "texts/en_US.lang").read_text().splitlines()
    drop_prefixes = ("item.aionbound:finale_ignition_key", "item.aionbound:trophy_concord_scale", "item.aionbound:trophy_edge_blank", "item.aionbound:memory_of_four_lands")
    language = [line for line in language if not line.startswith(drop_prefixes)]
    language += ["item.aionbound:trophy_edge_blank.name=Trophy Edge Blank", "item.aionbound:memory_of_four_lands.name=Memory of Four Lands"]
    (RP / "texts/en_US.lang").write_text("\n".join(language) + "\n")
    for relative in LEGACY_FILES:
        path = ROOT / relative
        if path.exists(): path.unlink()


if __name__ == "__main__":
    author()
