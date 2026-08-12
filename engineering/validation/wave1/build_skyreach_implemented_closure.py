#!/usr/bin/env python3
"""Build the exact source-hash closure for implemented Skyreach surfaces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TARGET = Path(__file__).with_name("WAVE_1_SKYREACH_IMPLEMENTED_CLOSURE.json")
RESOURCES = ["sky_feather", "cloud_wool", "updraft_reed_item", "sky_vine_item", "wind_silk", "cliff_crystal", "float_resin", "lift_bloom_item", "storm_pinion", "aether_stone"]
BLOCKS = ["cliff_stone", "pale_shelf_stone", "cliff_gravel", "wind_slate", "skyreach_log", "skyreach_wood", "skyreach_planks", "rope_timber", "cloud_wool_block", "sky_moss_block"]
PLANTS = ["wind_reed_plant", "hanging_sky_vine", "rope_root", "cloud_moss", "cloudpuff_plant", "shelf_shrub", "cliff_flower", "skybloom", "floating_blossom", "nest_thatch_tuft"]
CREATURES = ["cloud_goat", "sky_fox", "cliff_ram", "storm_gull", "gale_hawk", "ropewing", "stone_vulture", "glide_drake", "ruin_harpy", "wind_roc"]
NATURAL = [value for value in CREATURES if value != "wind_roc"]
STRUCTURES = ["rope_bridge", "broken_sky_path", "cliff_outpost", "cliff_beacon", "observation_tower", "nest_platform", "floating_ruin_floor", "ancient_sky_arch", "hanging_lift_frame", "wind_shrine"]
DERIVED = ["wing_bone_stay", "climbing_hook_head", "climbing_rope", "glider_frame", "glider_panel", "lift_tonic", "soft_landing_pad", "twin_mineral_lens", "aether_bind"]
RECIPES = [value for value in DERIVED if value != "wing_bone_stay"] + ["surveyor_medallion", "surveyor_staff", "trail_compass", "warden_sigil"]


def rows(paths: list[str]) -> list[dict[str, str]]:
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate source path")
    result = []
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        result.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def build() -> dict:
    static = [
        "engineering/skyreach-intake/static-foundations/SKYREACH_STATIC_FOUNDATIONS_AUTHORITY.json",
        "engineering/skyreach-intake/static-foundations/SKYREACH_STATIC_FOUNDATIONS_REPORT.json",
    ]
    static += [f"behavior_pack/items/{value}.item.json" for value in RESOURCES]
    static += [f"behavior_pack/blocks/{value}.block.json" for value in BLOCKS]
    static += [f"resource_pack/textures/aionbound/skyreach/items/{value}.png" for value in RESOURCES]
    static += [f"resource_pack/textures/aionbound/skyreach/blocks/{value}.png" for value in BLOCKS]

    plants = ["engineering/skyreach-intake/plant-runtime/SKYREACH_PLANT_PRODUCT_REPORT.json"]
    plants += [f"behavior_pack/blocks/{value}.block.json" for value in PLANTS]
    plants += [f"resource_pack/models/aionbound/skyreach/{value}.geo.json" for value in PLANTS]
    plants += [f"resource_pack/textures/aionbound/skyreach/plants/{value}.png" for value in PLANTS]
    plants += [f"behavior_pack/features/sr_ecology_{value}.feature.json" for value in PLANTS]
    plants += [f"behavior_pack/feature_rules/sr_ecology_{value}.feature_rule.json" for value in PLANTS]

    creatures = ["engineering/skyreach-intake/entity-runtime/SKYREACH_ENTITY_RUNTIME_REPORT.json"]
    creatures += [f"behavior_pack/entities/aionbound/skyreach/{value}.entity.json" for value in CREATURES]
    creatures += [f"resource_pack/entity/aionbound/skyreach/{value}.entity.json" for value in CREATURES]
    creatures += [f"resource_pack/models/aionbound/skyreach/{value}.geo.json" for value in CREATURES]
    creatures += [f"resource_pack/animations/aionbound/skyreach/{value}.animation.json" for value in CREATURES]
    creatures += [f"resource_pack/animation_controllers/aionbound/skyreach/{value}.animation_controller.json" for value in CREATURES]
    creatures += [f"resource_pack/render_controllers/aionbound/skyreach/{value}.render_controller.json" for value in CREATURES]
    creatures += [f"resource_pack/textures/aionbound/skyreach/entity/{value}.png" for value in CREATURES]
    creatures += [f"behavior_pack/spawn_rules/aionbound/skyreach/{value}.spawn_rules.json" for value in NATURAL]

    structures = [
        "engineering/skyreach-intake/structure-assemblies/SKYREACH_STRUCTURE_ASSEMBLIES.json",
    ]
    structures += [f"behavior_pack/structures/aionbound/{value}.mcstructure" for value in STRUCTURES]
    structures += [f"behavior_pack/features/{value}.structure_feature.json" for value in STRUCTURES]
    structures += [f"behavior_pack/feature_rules/{value}.structure_feature_rule.json" for value in STRUCTURES]

    economy = ["engineering/skyreach-intake/approved-vertical/SKYREACH_APPROVED_VERTICAL_REPORT.json"]
    economy += [f"behavior_pack/items/{value}.item.json" for value in DERIVED]
    economy += [f"behavior_pack/recipes/{value}.recipe.json" for value in RECIPES]
    economy += [f"behavior_pack/loot_tables/entities/aionbound/skyreach/{value}.json" for value in CREATURES]
    economy += [f"behavior_pack/loot_tables/blocks/aionbound/skyreach/{value}.json" for value in PLANTS]

    codex = [
        "engineering/skyreach-intake/economy-codex/SKYREACH_ECONOMY_CODEX_SCAFFOLD.json",
        "behavior_pack/scripts/wave1_codex_skyreach_data.js",
        "behavior_pack/scripts/wave1_codex_skyreach_runtime_data.js",
        "behavior_pack/scripts/wave1_codex_data.js",
        "behavior_pack/scripts/catalog.js",
        "behavior_pack/scripts/codex.js",
        "behavior_pack/scripts/state.js",
        "tests/wave1_codex_v4.test.mjs",
    ]
    encounter = [
        "behavior_pack/scripts/skyreach_rewards.js",
        "behavior_pack/scripts/storm_nest.js",
        "behavior_pack/scripts/runtime.js",
        "tests/wave1_skyreach_economy.test.mjs",
        "tests/wave1_storm_nest.test.mjs",
    ]
    native = [
        "engineering/native-assets/skyreach/representative/SKYREACH_REPRESENTATIVE_NATIVE_REPORT.json",
        "engineering/native-assets/skyreach/creatures/SKYREACH_CREATURE_NATIVE_REPORT.json",
        "engineering/native-assets/skyreach/plants/SKYREACH_PLANT_NATIVE_REPORT.json",
        "engineering/native-assets/skyreach/landmarks/SKYREACH_LANDMARK_NATIVE_REPORT.json",
    ]
    groups = {
        "resources_and_full_cube_blocks": rows(static),
        "plants_and_bounded_ecology": rows(plants),
        "creature_ai_client_motion_and_spawn": rows(creatures),
        "inert_structures_and_worldgen": rows(structures),
        "identity_codex_registry_v5": rows(codex),
        "loot_crafting_acquisition_and_packet006_links": rows(economy),
        "storm_nest_existing_handler_persistence_and_recovery": rows(encounter),
        "native_editable_asset_aggregates": rows(native),
    }
    all_paths = [row["path"] for group in groups.values() for row in group]
    if len(all_paths) != len(set(all_paths)):
        raise ValueError("duplicate path across groups")
    return {
        "schema": "aionbound.wave1.skyreach.implemented_source_closure.v1",
        "status": "SKYREACH_VERTICAL_SOURCE_COMPLETE_TARGETED_LOCAL_PASS",
        "groups": groups,
        "invariants": {
            "base_packet_ids": 50,
            "creatures": 10,
            "natural_creatures": 9,
            "arena_only_wind_roc": True,
            "plants": 10,
            "structures": 10,
            "native_custom_assets": 30,
            "codex_registry_entries": 50,
            "state_schema": 4,
            "new_subscription_classes": 0,
            "new_interval_classes": 0,
            "ratified_loot_crafting_and_acquisition": True,
            "storm_nest_existing_schema_service_composed": True,
            "storm_pinion_once_recovery_semantics": True,
        },
        "pending_follow_up": {
            "W1-CREATIVE-005": "DEFERRED_BY_USER_NO_SIDEGRADE_IDENTITIES",
            "runtime_qualification": "DEFERRED_TO_FINAL_INTEGRATED_GATE",
        },
        "proof_boundary": "EXACT SOURCE PATH AND HASH CLOSURE ONLY; NO PACKAGE, BDS, CLIENT, MULTIPLAYER, CONSOLE, MARKETPLACE, OR RELEASE CLAIM",
    }


def main() -> None:
    TARGET.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
