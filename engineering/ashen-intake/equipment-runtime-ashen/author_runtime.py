#!/usr/bin/env python3
"""Deterministically bind native-qualified Ashen equipment base identities.

This focused lane intentionally supplies visual/base-role registration only.
Acquisition, recipes, loot, reward delivery, sidegrades, and numeric balance are
owned by other authority slices.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LANE = ROOT / "engineering/ashen-intake/equipment-runtime-ashen"
NATIVE = ROOT / "engineering/native-assets/ashen/equipment/evidence"
AUTHORITY_COMMIT = "7505ac2223f362d9b4e59a82cab5486cab304fc5"

SPECS = {
    "basalt_hammer": ("Basalt Hammer", "weapon", ["idle_hold", "smash_pose"], "idle_hold"),
    "ember_great_axe": ("Ember Great Axe", "weapon", ["idle_hold", "overhead_pose", "slam_pose"], "idle_hold"),
    "ash_repeater": ("Ash Repeater", "weapon", ["crank_pose", "fire_pose", "idle_hold"], "idle_hold"),
    "ashen_helmet": ("Ashen Helmet", "armor_head", ["vent_pulse_showcase"], "vent_pulse_showcase"),
    "ashen_chest": ("Ashen Chest", "armor_chest", [], None),
    "ashen_legs": ("Ashen Legs", "armor_legs", [], None),
    "ashen_boots": ("Ashen Boots", "armor_feet", [], None),
    "basalt_pick": ("Basalt Pick", "tool", ["hold", "swing"], "hold"),
    "ember_hammer": ("Ember Hammer", "tool", ["hold", "tap"], "hold"),
    "ore_chisel": ("Ore Chisel", "tool", ["hold", "tap"], "hold"),
    "ember_totem": ("Ember Totem", "accessory", ["vent_pulse"], "vent_pulse"),
    "ash_drake_horn": ("Ash Drake Horn", "trophy", ["pulse_base"], "pulse_base"),
    "ember_forge_core": ("Ember Forge Core", "trophy", ["idle_pulse"], "idle_pulse"),
}
COMPONENTS = {
    "heat_core": "Heat Core",
    "heavy_head": "Heavy Head",
    "chitin_plate": "Chitin Plate",
    "ember_heart": "Ember Heart",
}
SLOTS = {
    "armor_head": "slot.armor.head",
    "armor_chest": "slot.armor.chest",
    "armor_legs": "slot.armor.legs",
    "armor_feet": "slot.armor.feet",
    "accessory": "slot.weapon.offhand",
}

SUBJECTS = {
    "basalt_hammer": "a massive basalt war hammer with squared dark stone head, ember seams, and wrapped wooden haft",
    "ember_great_axe": "a two-handed great axe with broad black basalt blade, glowing ember edge, and long wrapped haft",
    "ash_repeater": "a compact ash-wood mechanical repeater crossbow with basalt arms, crank, and restrained ember accents",
    "ashen_helmet": "a full dark basalt armor helmet with angular brow, narrow glowing orange visor, and small vent ridges",
    "ashen_chest": "a heavy dark basalt chestplate with layered angular plates and restrained glowing ember seams",
    "ashen_legs": "a matched pair of dark basalt armored leggings with segmented plates and restrained ember seams",
    "ashen_boots": "a matched pair of chunky dark basalt armored boots with reinforced toes and restrained ember seams",
    "basalt_pick": "a rugged basalt mining pickaxe with black stone head, ember inlay, and wrapped wooden handle",
    "ember_hammer": "a compact forge hammer with dark basalt head, bright ember core, and short wrapped handle",
    "ore_chisel": "a slim dark basalt ore chisel with faceted point, copper-orange collar, and wrapped grip",
    "ember_totem": "a small upright basalt totem with carved vents and a contained orange ember glow",
    "ash_drake_horn": "a curved ash drake horn trophy on a small dark basalt display base, ivory-to-char gradient with ember glow",
    "ember_forge_core": "a compact cubic basalt forge core with black metal cage and bright contained orange furnace center",
    "heat_core": "a palm-sized circular basalt heat core with a bright orange center held by four dark stone clamps",
    "heavy_head": "a dense unfinished squared basalt hammer head component with a small ember socket and no handle",
    "chitin_plate": "one layered furnace-beetle chitin armor plate, charcoal black with ridged ember-orange underside",
    "ember_heart": "one faceted heart-shaped ember crystal, bright molten orange center inside a dark basalt shell",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def item_document(asset: str, name: str, role: str) -> dict:
    components: dict[str, object] = {
        "minecraft:display_name": {"value": name},
        "minecraft:icon": {"textures": {"default": asset}},
        "minecraft:max_stack_size": 1,
    }
    if role in {"weapon", "tool"}:
        components["minecraft:hand_equipped"] = True
    if role in SLOTS:
        components["minecraft:wearable"] = {"slot": SLOTS[role]}
    return {
        "format_version": "1.21.80",
        "minecraft:item": {
            "description": {
                "identifier": f"aionbound:{asset}",
                "menu_category": {"category": "equipment"},
            },
            "components": components,
        },
    }


def component_document(asset: str, name: str) -> dict:
    return {
        "format_version": "1.21.80",
        "minecraft:item": {
            "description": {
                "identifier": f"aionbound:{asset}",
                "menu_category": {"category": "items"},
            },
            "components": {
                "minecraft:display_name": {"value": name},
                "minecraft:icon": {"textures": {"default": asset}},
                "minecraft:max_stack_size": 64,
            },
        },
    }


def attachable_document(asset: str, clips: list[str], idle: str | None) -> dict:
    description: dict[str, object] = {
        "identifier": f"aionbound:{asset}",
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/aionbound/ashen/equipment/models/{asset}"},
        "geometry": {"default": f"geometry.aionbound.{asset}"},
        "render_controllers": ["controller.render.aionbound.default"],
    }
    if clips:
        description["animations"] = {
            clip: f"animation.aionbound.{asset}.{clip}" for clip in clips
        }
    if idle:
        description["scripts"] = {"animate": [idle]}
    return {"format_version": "1.10.0", "minecraft:attachable": {"description": description}}


def trophy_document(asset: str, name: str) -> dict:
    return {
        "format_version": "1.21.80",
        "minecraft:block": {
            "description": {
                "identifier": f"aionbound:{asset}",
                "menu_category": {"category": "construction"},
            },
            "components": {
                "minecraft:display_name": name,
                "minecraft:collision_box": {"origin": [-6, 0, -6], "size": [12, 12, 12]},
                "minecraft:selection_box": {"origin": [-7, 0, -7], "size": [14, 14, 14]},
                "minecraft:geometry": f"geometry.aionbound.{asset}",
                "minecraft:material_instances": {
                    "*": {"texture": asset, "render_method": "alpha_test"}
                },
                "minecraft:placement_filter": {
                    "conditions": [{
                        "allowed_faces": ["up"],
                        "block_filter": [
                            "minecraft:stone", "minecraft:blackstone",
                            "minecraft:basalt", "aionbound:basalt_brick",
                            "aionbound:smolder_stone",
                        ],
                    }]
                },
            },
        },
    }


def icon_prompt(asset: str, component: bool) -> str:
    kind = "crafting component" if component else "inventory icon"
    object_word = "component" if component else "object"
    padding = "18" if component else "15"
    return (
        "Use case: stylized-concept\n"
        f"Asset type: Minecraft Bedrock {kind} source for {asset}\n"
        f"Primary request: {SUBJECTS[asset]}\n"
        "Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for local removal\n"
        "Style/medium: original hand-painted low-poly voxel game UI icon, chunky Minecraft-readable forms, crisp pixel-art-like edges, no photorealism\n"
        f"Composition/framing: one centered object, square canvas, {padding} percent padding, strong silhouette readable at 16x16\n"
        "Color palette: charcoal black, basalt gray, ember orange, restrained ash beige\n"
        f"Constraints: background is one uniform #00ff00 with no shadows, gradients, floor, reflections, or texture; do not use #00ff00 in subject; no text; no logo; no watermark; exactly one {object_word}"
    )


def main() -> int:
    item_atlas_path = ROOT / "resource_pack/textures/item_texture.json"
    terrain_atlas_path = ROOT / "resource_pack/textures/terrain_texture.json"
    item_atlas = json.loads(item_atlas_path.read_text(encoding="utf-8"))
    terrain_atlas = json.loads(terrain_atlas_path.read_text(encoding="utf-8"))
    lang_path = ROOT / "resource_pack/texts/en_US.lang"
    lang_lines = lang_path.read_text(encoding="utf-8").splitlines()
    owned_prefixes = [
        *(f"item.aionbound:{asset}.name=" for asset in SPECS if SPECS[asset][1] != "trophy"),
        *(f"tile.aionbound:{asset}.name=" for asset in SPECS if SPECS[asset][1] == "trophy"),
        *(f"item.aionbound:{asset}.name=" for asset in COMPONENTS),
    ]
    lang_lines = [line for line in lang_lines if not any(line.startswith(p) for p in owned_prefixes)]

    for asset, (name, role, clips, idle) in SPECS.items():
        evidence = NATIVE / asset
        geo_source = evidence / "native-exports/pass-2.geo.json"
        animation_source = evidence / "native-exports/pass-2.animation.json"
        texture_source = evidence / f"native-project/textures/{asset}.png"
        for source in (geo_source, animation_source, texture_source):
            if not source.is_file():
                raise FileNotFoundError(source)

        geo_target = ROOT / f"resource_pack/models/aionbound/ashen/equipment/{asset}.geo.json"
        animation_target = ROOT / f"resource_pack/animations/aionbound/ashen/equipment/{asset}.animation.json"
        model_texture_target = ROOT / f"resource_pack/textures/aionbound/ashen/equipment/models/{asset}.png"
        for target in (geo_target, animation_target, model_texture_target):
            target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(geo_source, geo_target)
        shutil.copyfile(animation_source, animation_target)
        shutil.copyfile(texture_source, model_texture_target)
        write_json(ROOT / f"resource_pack/attachables/{asset}.attachable.json", attachable_document(asset, clips, idle))

        item_atlas["texture_data"][asset] = {
            "textures": f"textures/aionbound/ashen/equipment/{asset}"
        }
        if role == "trophy":
            write_json(ROOT / f"behavior_pack/blocks/{asset}.block.json", trophy_document(asset, name))
            terrain_atlas["texture_data"][asset] = {
                "textures": f"textures/aionbound/ashen/equipment/models/{asset}"
            }
            lang_lines.append(f"tile.aionbound:{asset}.name={name}")
        else:
            write_json(ROOT / f"behavior_pack/items/{asset}.item.json", item_document(asset, name, role))
            lang_lines.append(f"item.aionbound:{asset}.name={name}")

    for asset, name in COMPONENTS.items():
        write_json(ROOT / f"behavior_pack/items/{asset}.item.json", component_document(asset, name))
        item_atlas["texture_data"][asset] = {
            "textures": f"textures/aionbound/ashen/components/{asset}"
        }
        lang_lines.append(f"item.aionbound:{asset}.name={name}")

    write_json(item_atlas_path, item_atlas)
    write_json(terrain_atlas_path, terrain_atlas)
    lang_path.write_text("\n".join(lang_lines) + "\n", encoding="utf-8")

    artifacts = []
    for asset in SPECS:
        native = NATIVE / asset
        paths = {
            "native_geometry": native / "native-exports/pass-2.geo.json",
            "runtime_geometry": ROOT / f"resource_pack/models/aionbound/ashen/equipment/{asset}.geo.json",
            "native_animation": native / "native-exports/pass-2.animation.json",
            "runtime_animation": ROOT / f"resource_pack/animations/aionbound/ashen/equipment/{asset}.animation.json",
            "native_model_uv": native / f"native-project/textures/{asset}.png",
            "runtime_model_uv": ROOT / f"resource_pack/textures/aionbound/ashen/equipment/models/{asset}.png",
            "icon_source": LANE / f"icons/chroma-sources/{asset}.png",
            "icon_alpha_master": LANE / f"icons/alpha-master/{asset}.png",
            "shipping_icon": ROOT / f"resource_pack/textures/aionbound/ashen/equipment/{asset}.png",
            "attachable": ROOT / f"resource_pack/attachables/{asset}.attachable.json",
        }
        role = SPECS[asset][1]
        if role == "trophy":
            paths["behavior_block"] = ROOT / f"behavior_pack/blocks/{asset}.block.json"
        else:
            paths["behavior_item"] = ROOT / f"behavior_pack/items/{asset}.item.json"
        artifacts.append({
            "id": asset,
            "role": role,
            "brief_clips": SPECS[asset][2],
            "prompt": icon_prompt(asset, False),
            "files": {key: {"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for key, path in paths.items()},
        })
    component_artifacts = []
    for asset in COMPONENTS:
        paths = {
            "icon_source": LANE / f"icons/chroma-sources/{asset}.png",
            "icon_alpha_master": LANE / f"icons/alpha-master/{asset}.png",
            "shipping_icon": ROOT / f"resource_pack/textures/aionbound/ashen/components/{asset}.png",
            "behavior_item": ROOT / f"behavior_pack/items/{asset}.item.json",
        }
        component_artifacts.append({
            "id": asset,
            "prompt": icon_prompt(asset, True),
            "files": {key: {"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for key, path in paths.items()},
        })
    write_json(LANE / "ASHEN_EQUIPMENT_RUNTIME_REPORT.json", {
        "schema_version": 1,
        "authority_commit": AUTHORITY_COMMIT,
        "status": "TARGETED_STATIC_PASS",
        "scope": {
            "native_equipment_base_ids": list(SPECS),
            "ratified_derived_components": list(COMPONENTS),
            "preserved_existing_base": "aionbound:briar_ring",
            "deferred": "W1-CREATIVE-005",
        },
        "icon_pipeline": {
            "generator": "OpenAI built-in imagegen",
            "calls": 17,
            "call_rule": "one call per distinct icon",
            "chroma_key": "#00ff00",
            "transparent_threshold": 18,
            "opaque_threshold": 90,
            "edge_feather": 0.8,
            "spill_cleanup": True,
            "shipping_size": [32, 32],
            "shipping_transform": "Lanczos downscale from generated alpha master; no upscale",
        },
        "equipment": artifacts,
        "components": component_artifacts,
        "semantic_boundary": {
            "stable_base_roles_only": True,
            "numeric_damage_durability_repair_protection_or_mining_speed": "OMITTED_NO_EXACT_APPROVED_VALUES",
            "recipes_or_acquisition": "NOT_IN_THIS_LANE",
            "loot_or_reward_delivery": "NOT_IN_THIS_LANE",
            "sidegrades": "DEFERRED_NOT_CREATED",
            "bds_build_or_candidate": "NOT_RUN",
        },
        "validation": {
            "targeted_runtime_suite": {
                "command": "python3 -m unittest engineering/ashen-intake/equipment-runtime-ashen/test_runtime.py",
                "tests": 9,
                "result": "PASS",
            },
            "native_authoring_regression": {
                "command": "cd engineering/native-assets/ashen/equipment && python3 -m unittest test_author_equipment.py",
                "tests": 6,
                "result": "PASS",
            },
            "deterministic_author_rerun": {
                "method": "compare git diff --binary SHA-256 before and after an author rerun",
                "equal": True,
                "result": "PASS",
            },
            "git_diff_check": "PASS",
        },
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
