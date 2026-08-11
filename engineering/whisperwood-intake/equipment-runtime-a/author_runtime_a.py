#!/usr/bin/env python3
"""Deterministically bind the eight native-passed Whisperwood equipment-A assets."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "engineering/native-assets/whisperwood/equipment-a/evidence"

SPECS = {
    "mossfang_spear": {
        "name": "Mossfang Spear", "damage": 5, "durability": 360,
        "clips": ["idle_hold", "thrust_pose", "sweep_pose"], "idle": "idle_hold",
    },
    "widow_fang_dagger": {
        "name": "Widow Fang Dagger", "damage": 3, "durability": 260,
        "clips": ["idle_hold", "stab_pose"], "idle": "idle_hold",
    },
    "thorn_whip": {
        "name": "Thorn Whip", "damage": 4, "durability": 300,
        "clips": ["idle_coil", "crack_pose", "extend_pose"], "idle": "idle_coil",
    },
    "briar_cleaver": {
        "name": "Briar Cleaver", "damage": 8, "durability": 320,
        "clips": ["idle_hold", "chop_pose"], "idle": "idle_hold",
    },
    "moon_sap_staff": {
        "name": "Moon Sap Staff", "damage": 3, "durability": 340,
        "clips": ["idle_hold", "cast_raise", "pulse"], "idle": "idle_hold",
        "use": {"category": "aionbound_moon_sap_staff", "duration": 10.0},
    },
    "root_knife": {
        "name": "Root Knife", "damage": 2, "durability": 180,
        "clips": ["hold"], "idle": "hold",
        "digger": [
            ({"tags": "query.any_tag('plant', 'leaves')"}, 3),
            ("aionbound:briar_vine", 5), ("aionbound:whisper_fern", 5),
            ("aionbound:pale_reed", 5), ("aionbound:root_flower", 5),
        ],
    },
    "whisperwood_hatchet": {
        "name": "Whisperwood Hatchet", "damage": 4, "durability": 300,
        "clips": ["hold", "chop"], "idle": "hold",
        "digger": [
            ({"tags": "query.any_tag('wood', 'plant')"}, 6),
            ("aionbound:whisperwood_log", 7), ("aionbound:stripped_whisperwood_log", 7),
            ("aionbound:whisperwood_wood", 7), ("aionbound:hollow_wood", 7),
            ("aionbound:moss_bark", 7), ("aionbound:briar_vine", 7),
        ],
    },
    "lantern_hook": {
        "name": "Lantern Hook", "damage": 2, "durability": 280,
        "clips": ["hold", "hang"], "idle": "hold",
        "use": {"category": "aionbound_lantern_hook", "duration": 10.0},
    },
}

# Preserve the integration-head atlas order so this focused lane contributes
# only its eight trailing entries and avoids needless merge conflicts.
BASE_ATLAS_ORDER = """barkling_token burrowgate_key chrono_core finale_ignition_key
starter_codex_bookmark stripvein_charge trophy_basalt_tusk trophy_codex
trophy_colossus_shard trophy_concord_scale trophy_edge trophy_edge_preview
vector_ray_projector waykeeper_whistle aether_gauntlet aionite_crystal
anvil_chitin basalt_maul behemoth_tusk_bow brine_spear brood_fang_daggers
charged_prism cinder_saber concord_boots concord_chestplate concord_helmet
concord_leggings ferrowake_boots ferrowake_chestplate ferrowake_coupling
ferrowake_helmet ferrowake_leggings gale_repeater lumen_draught lumen_salt
miners_resin mite_resin mote_lantern pilgrim_clasp pinion_feather_tuft
prism_dew_crystal prismatic_binder quarry_lens raw_ferrowake resonance_coil
roc_pinion_glaive rootglass_shard salvage_magnet stabilizing_chalk survey_core
tempered_ferrowake trophy_relic_tooth ward_knot wayfinder_spool waystone_ration
woven_sinew ancient_acorn briar_antler glow_spore hollow_amber lantern_fur
moon_sap moss_resin root_heart whisper_bark widow_silk""".split()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def item_document(asset_id: str, spec: dict) -> dict:
    components: dict[str, object] = {
        "minecraft:damage": spec["damage"],
        "minecraft:display_name": {"value": spec["name"]},
        "minecraft:durability": {"max_durability": spec["durability"]},
        "minecraft:hand_equipped": True,
        "minecraft:icon": {"textures": {"default": asset_id}},
        "minecraft:max_stack_size": 1,
    }
    if "digger" in spec:
        components["minecraft:digger"] = {
            "destroy_speeds": [
                {"block": block, "speed": speed} for block, speed in spec["digger"]
            ],
            "use_efficiency": True,
        }
    if "use" in spec:
        components["minecraft:cooldown"] = spec["use"]
        components["minecraft:use_modifiers"] = {"movement_modifier": 0.8, "use_duration": 0.2}
    return {
        "format_version": "1.21.80",
        "minecraft:item": {
            "components": components,
            "description": {
                "identifier": f"aionbound:{asset_id}",
                "menu_category": {"category": "equipment"},
            },
        },
    }


def attachable_document(asset_id: str, spec: dict) -> dict:
    animations = {
        clip: f"animation.aionbound.{asset_id}.{clip}" for clip in spec["clips"]
    }
    return {
        "format_version": "1.10.0",
        "minecraft:attachable": {
            "description": {
                "animations": animations,
                "geometry": {"default": f"geometry.aionbound.{asset_id}"},
                "identifier": f"aionbound:{asset_id}",
                "materials": {"default": "entity_alphatest"},
                "render_controllers": ["controller.render.aionbound.default"],
                "scripts": {"animate": [spec["idle"]]},
                "textures": {
                    "default": f"textures/aionbound/whisperwood/equipment/models/{asset_id}"
                },
            }
        },
    }


def main() -> None:
    atlas_path = ROOT / "resource_pack/textures/item_texture.json"
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    language_path = ROOT / "resource_pack/texts/en_US.lang"
    language = language_path.read_text(encoding="utf-8").splitlines()
    language = [line for line in language if not any(line.startswith(f"item.aionbound:{asset_id}=") for asset_id in SPECS)]

    for asset_id, spec in SPECS.items():
        source = NATIVE / asset_id
        write_json(ROOT / f"behavior_pack/items/{asset_id}.item.json", item_document(asset_id, spec))
        write_json(ROOT / f"resource_pack/attachables/{asset_id}.attachable.json", attachable_document(asset_id, spec))

        geometry_target = ROOT / f"resource_pack/models/aionbound/whisperwood/equipment/{asset_id}.geo.json"
        animation_target = ROOT / f"resource_pack/animations/aionbound/whisperwood/equipment/{asset_id}.animation.json"
        texture_target = ROOT / f"resource_pack/textures/aionbound/whisperwood/equipment/models/{asset_id}.png"
        geometry_target.parent.mkdir(parents=True, exist_ok=True)
        animation_target.parent.mkdir(parents=True, exist_ok=True)
        texture_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / "native-exports/pass-2.geo.json", geometry_target)
        shutil.copyfile(source / "native-exports/pass-2.animation.json", animation_target)
        shutil.copyfile(source / f"native-project/textures/{asset_id}.png", texture_target)

        atlas["texture_data"][asset_id] = {
            "textures": f"textures/aionbound/whisperwood/equipment/{asset_id}"
        }
        language.append(f"item.aionbound:{asset_id}={spec['name']}")

    prior = atlas["texture_data"]
    atlas["texture_data"] = {
        key: prior[key] for key in [*BASE_ATLAS_ORDER, *SPECS] if key in prior
    }
    write_json(atlas_path, atlas)
    language_path.write_text("\n".join(language) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
