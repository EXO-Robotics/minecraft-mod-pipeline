#!/usr/bin/env python3
"""Build the exact source-hash closure for the integrated Crystal Marsh vertical."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TARGET = Path(__file__).with_name("WAVE_1_CRYSTAL_IMPLEMENTED_CLOSURE.json")
CREATURES = ["bloom_crab", "bog_watcher", "crystal_dragonfly", "crystal_newt", "glass_heron", "marsh_wight", "mire_turtle", "prism_frog", "reed_serpent", "silt_crocodile"]
NATURAL_CREATURES = [value for value in CREATURES if value != "marsh_wight"]
PLANTS = ["crystal_lily", "flood_reed", "prism_bloom", "glass_moss", "marsh_fern", "glow_kelp", "mire_orchid", "bubble_pod", "pearl_grass", "crystal_vine"]
RESOURCES = ["prism_pearl", "crystal_reed_item", "marsh_resin", "glass_algae", "silt_core", "flood_crystal", "moon_pearl", "wet_chitin", "mire_bloom_item", "crystal_root_item"]
BLOCKS = ["crystal_log", "marsh_wood", "flood_planks", "crystal_stone", "prism_brick", "wet_clay_block", "glass_root_block", "algae_block", "marsh_soil", "crystal_gravel"]
STRUCTURES = ["flooded_dock", "ancient_boat", "marsh_broken_bridge", "pearl_cairn", "marsh_totem", "crystal_arch", "crystal_obelisk", "sunken_shrine", "ruined_observatory", "deep_pool_entrance"]
EQUIPMENT = ["crystal_pike", "prism_bow", "crystal_circlet", "explorer_cloak", "crystal_shovel", "marsh_sickle", "crystal_talisman", "marsh_idol", "marsh_wight_mask", "moon_pearl_pedestal", "crystal_obelisk_fragment"]
TROPHIES = {"marsh_wight_mask", "moon_pearl_pedestal", "crystal_obelisk_fragment"}
COMPONENTS = ["prism_wing", "watcher_lens", "wight_shroud", "crystal_pole", "living_crystal_core", "wet_plate"]
RECIPES = ["mire_bloom_cyan_dye", "crystal_pole", "living_crystal_core", "wet_plate", "crystal_pike", "prism_bow", "crystal_circlet", "explorer_cloak", "crystal_shovel", "marsh_sickle", "crystal_talisman", "marsh_idol", "moon_pearl_pedestal"]
CHESTS = ["flooded_dock", "ancient_boat", "marsh_broken_bridge", "pearl_cairn", "crystal_arch", "crystal_obelisk", "ruined_observatory", "pearl_depths"]


def rows(paths: list[str]) -> list[dict[str, str]]:
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate path within source group")
    result = []
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        result.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def build() -> dict:
    resources_blocks = [
        "engineering/crystal-marsh-intake/resource-runtime/CRYSTAL_RESOURCE_RUNTIME_AUTHORITY.json",
        "engineering/crystal-marsh-intake/resource-runtime/CRYSTAL_RESOURCE_RUNTIME_REPORT.json",
        "engineering/crystal-marsh-intake/block-runtime/CRYSTAL_BLOCK_RUNTIME_AUTHORITY.json",
        "engineering/crystal-marsh-intake/block-runtime/CRYSTAL_BLOCK_RUNTIME_REPORT.json",
    ]
    resources_blocks += [f"behavior_pack/items/{value}.item.json" for value in RESOURCES]
    resources_blocks += [f"behavior_pack/blocks/{value}.block.json" for value in BLOCKS]
    resources_blocks += [f"resource_pack/textures/aionbound/crystal_marsh/items/{value}.png" for value in RESOURCES]
    resources_blocks += [f"resource_pack/textures/aionbound/crystal_marsh/blocks/{value}.png" for value in BLOCKS]

    plants_ecology = [
        "engineering/crystal-marsh-intake/plant-runtime/CRYSTAL_PLANT_RUNTIME_REPORT.json",
        "engineering/crystal-marsh-intake/ecology-worldgen/CRYSTAL_ECOLOGY_WORLDGEN.json",
    ]
    plants_ecology += [f"behavior_pack/blocks/{value}.block.json" for value in PLANTS]
    plants_ecology += [f"resource_pack/models/aionbound/crystal_marsh/{value}.geo.json" for value in PLANTS]
    plants_ecology += [f"resource_pack/textures/aionbound/crystal_marsh/plants/{value}.png" for value in PLANTS]
    plants_ecology += [f"behavior_pack/features/cm_ecology_{value}.feature.json" for value in PLANTS]
    plants_ecology += [f"behavior_pack/feature_rules/cm_ecology_{value}.feature_rule.json" for value in PLANTS]

    creatures = ["engineering/crystal-marsh-intake/entity-runtime/CRYSTAL_MARSH_ENTITY_RUNTIME_REPORT.json"]
    creatures += [f"behavior_pack/entities/aionbound/crystal_marsh/{value}.entity.json" for value in CREATURES]
    creatures += [f"resource_pack/entity/aionbound/crystal_marsh/{value}.entity.json" for value in CREATURES]
    creatures += [f"resource_pack/models/aionbound/crystal_marsh/entities/{value}.geo.json" for value in CREATURES]
    creatures += [f"resource_pack/animations/aionbound/crystal_marsh/entities/{value}.animation.json" for value in CREATURES]
    creatures += [f"resource_pack/animation_controllers/aionbound/crystal_marsh/{value}.animation_controller.json" for value in CREATURES]
    creatures += [f"resource_pack/render_controllers/aionbound/crystal_marsh/{value}.render_controller.json" for value in CREATURES]
    creatures += [f"resource_pack/textures/aionbound/crystal_marsh/entity/{value}.png" for value in CREATURES]
    creatures += [f"behavior_pack/spawn_rules/aionbound/crystal_marsh/{value}.spawn_rules.json" for value in NATURAL_CREATURES]

    structures = [
        "engineering/crystal-marsh-intake/structure-assemblies/CRYSTAL_MARSH_STRUCTURE_ASSEMBLIES.json",
        "engineering/crystal-marsh-intake/structure-assemblies/CRYSTAL_MARSH_STRUCTURE_VALIDATION_REPORT.json",
        "engineering/crystal-marsh-intake/structure-economy/CRYSTAL_STRUCTURE_ECONOMY_BINDING.json",
        "engineering/crystal-marsh-intake/structure-economy/CRYSTAL_STRUCTURE_ECONOMY_VALIDATION_REPORT.json",
    ]
    structures += [f"behavior_pack/structures/aionbound/{value}.mcstructure" for value in STRUCTURES]
    structures += [f"behavior_pack/features/{value}.structure_feature.json" for value in STRUCTURES]
    structures += [f"behavior_pack/feature_rules/{value}.structure_feature_rule.json" for value in STRUCTURES]

    economy = ["engineering/crystal-marsh-intake/economy-equipment/CRYSTAL_ECONOMY_EQUIPMENT_REPORT.json"]
    economy += [f"behavior_pack/loot_tables/entities/crystal/{value}.json" for value in CREATURES]
    economy += [f"behavior_pack/loot_tables/blocks/{value}.json" for value in BLOCKS + PLANTS]
    economy += [f"behavior_pack/loot_tables/chests/crystal/{value}.json" for value in CHESTS]
    economy += ["behavior_pack/loot_tables/encounters/crystal/pearl_depths_materials.json"]
    economy += [f"behavior_pack/recipes/{value}.recipe.json" for value in RECIPES]

    equipment = [
        "engineering/crystal-marsh-intake/equipment/CRYSTAL_EQUIPMENT_INTAKE.json",
        "engineering/crystal-marsh-intake/equipment/CRYSTAL_EQUIPMENT_INTAKE.md",
    ]
    for value in EQUIPMENT:
        equipment += [
            f"behavior_pack/{'blocks' if value in TROPHIES else 'items'}/{value}.{'block' if value in TROPHIES else 'item'}.json",
            f"resource_pack/attachables/{value}.attachable.json",
            f"resource_pack/models/aionbound/crystal_marsh/equipment/{value}.geo.json",
            f"resource_pack/animations/aionbound/crystal_marsh/equipment/{value}.animation.json",
            f"resource_pack/textures/aionbound/crystal_marsh/equipment/models/{value}.png",
        ]
    equipment += [f"behavior_pack/items/{value}.item.json" for value in COMPONENTS]
    equipment += [f"resource_pack/textures/aionbound/crystal_marsh/components/{value}.png" for value in COMPONENTS]
    equipment += [
        "behavior_pack/scripts/crystal_equipment.js", "behavior_pack/scripts/crystal_equipment_roles.js",
        "tests/wave1_crystal_equipment_roles.test.mjs",
    ]

    codex_pearl_runtime = [
        "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        "engineering/crystal-marsh-intake/authority/CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json",
        "engineering/crystal-marsh-intake/codex/CRYSTAL_CODEX_PROGRESSION_INTAKE_MAP.json",
        "behavior_pack/scripts/wave1_codex_crystal_data.js", "behavior_pack/scripts/wave1_codex_data.js",
        "behavior_pack/scripts/codex.js", "behavior_pack/scripts/catalog.js", "behavior_pack/scripts/combat.js",
        "behavior_pack/scripts/budgets.js", "behavior_pack/scripts/state.js", "behavior_pack/scripts/router.js",
        "behavior_pack/scripts/runtime.js", "behavior_pack/scripts/crystal_reward_data.js",
        "behavior_pack/scripts/crystal_rewards.js", "behavior_pack/scripts/pearl_depths.js",
        "tests/wave1_crystal_codex_rewards.test.mjs", "tests/wave1_pearl_depths.test.mjs",
    ]

    shared_presentation = [
        "resource_pack/textures/item_texture.json", "resource_pack/textures/terrain_texture.json",
        "resource_pack/blocks.json", "resource_pack/texts/en_US.lang",
    ]

    native_receipts = [
        "engineering/native-assets/crystal-marsh/representative/CRYSTAL_MARSH_REPRESENTATIVE_NATIVE_REPORT.json",
        "engineering/native-assets/crystal-marsh/creatures/CRYSTAL_MARSH_CREATURE_NATIVE_REPORT.json",
        "engineering/native-assets/crystal-marsh/plants/CRYSTAL_MARSH_PLANT_NATIVE_REPORT.json",
        "engineering/native-assets/crystal-marsh/equipment/CRYSTAL_EQUIPMENT_NATIVE_REPORT.json",
    ]

    groups = {
        "resources_and_full_cube_blocks": rows(resources_blocks),
        "plants_and_bounded_ecology": rows(plants_ecology),
        "creature_ai_client_motion_spawn_and_loot_binding": rows(creatures),
        "structures_world_discovery_and_protected_cache_binding": rows(structures),
        "loot_crafting_and_acquisition_economy": rows(economy),
        "equipment_presentation_and_existing_handler_roles": rows(equipment),
        "codex_progression_pearl_depths_persistence_and_shared_composition": rows(codex_pearl_runtime),
        "shared_atlas_localization_and_block_registry": rows(shared_presentation),
        "native_editable_asset_aggregate_receipts": rows(native_receipts),
    }
    paths = [row["path"] for values in groups.values() for row in values]
    if len(paths) != len(set(paths)):
        duplicates = sorted({path for path in paths if paths.count(path) > 1})
        raise ValueError(f"duplicate path across source groups: {duplicates}")
    return {
        "schema": "aionbound.wave1.crystal_marsh.implemented_source_closure.v1",
        "status": "CRYSTAL_MARSH_VERTICAL_SOURCE_COMPLETE_TARGETED_LOCAL_PASS",
        "base": {"commit": "fb86d22ccaadbcdc890a7cc9038be42667159927", "tree": "2a1b83fa9e7cc8ed3f584d21027cea74e05d0582", "authority": "G8 successor integration line"},
        "groups": groups,
        "invariants": {
            "persistence_schema": 4,
            "natural_entity_target": 40,
            "natural_crystal_ids": [f"aionbound:{value}" for value in NATURAL_CREATURES],
            "natural_spawn_exclusions": ["aionbound:marsh_wight"],
            "new_global_subscription_classes": 0,
            "new_recurring_interval_classes": 0,
            "protected_mask_owner": "PEARL_DEPTHS_TERMINAL_RECOVERY_ONLY",
            "natural_marsh_wight_mask_drop": False,
            "ashen_dormant_service_activation": False,
            "w1_creative_005": "DEFERRED",
        },
        "pending_follow_up": {
            "ashen_runtime_activation_ticket": "MANAGED_REVIEWER_ACTIVATION_BLOCKED_DEFERRED",
            "creative": "W1-CREATIVE-005_DEFERRED",
            "crystal_runtime_qualification": "DEFERRED_TO_FINAL_INTEGRATED_GATE",
        },
        "proof_boundary": "EXACT SOURCE PATH AND BYTE HASH CLOSURE WITH TARGETED LOCAL SEMANTIC AND MECHANICAL VALIDATION ONLY; NO BUILD, PACKAGE, BDS, CLIENT, MULTIPLAYER, CONSOLE, MARKETPLACE, RELEASE, OR PHYSICAL RUNTIME PROOF",
    }


def main() -> None:
    TARGET.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
