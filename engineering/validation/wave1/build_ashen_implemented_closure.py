#!/usr/bin/env python3
"""Build the exact source-hash closure consumed by the Wave 1 validator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TARGET = Path(__file__).with_name("WAVE_1_ASHEN_IMPLEMENTED_CLOSURE.json")
PLANTS = ["cinder_grass", "ash_fern", "smoke_reed", "char_shrub", "soot_mushroom", "magma_moss", "glow_root", "basalt_flower", "ember_vine", "fire_bloom"]
CREATURES = ["ash_drake", "ash_mite", "ash_ram", "basalt_tortoise", "char_wolf", "cinder_lynx", "ember_crow", "furnace_beetle", "magma_lizard", "soot_stag"]
NATURAL_CREATURES = [value for value in CREATURES if value != "ash_drake"]
STRUCTURES = ["fire_totem", "burned_camp", "char_wagon", "broken_bridge", "basalt_arch", "ash_watchtower", "ancient_kiln", "ember_forge", "lava_shrine", "ash_cave"]
RESOURCES = ["smolder_bark", "charbone", "sulfur_cluster", "volcanic_glass_shard", "ember_resin", "heatstone", "furnace_chitin", "basalt_core", "ash_crystal", "fire_bloom_seed"]
FULL_BLOCKS = ["ash_log", "char_planks", "basalt_brick", "smolder_stone", "ash_soil", "ember_moss", "volcanic_glass_block", "heat_bark", "basalt_pillar", "cinder_gravel"]
EQUIPMENT = ["basalt_hammer", "ember_great_axe", "ash_repeater", "ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots", "basalt_pick", "ember_hammer", "ore_chisel", "ember_totem", "ash_drake_horn", "ember_forge_core"]
PLACEABLE_EQUIPMENT = {"ash_drake_horn", "ember_forge_core"}
DERIVED = ["heat_core", "heavy_head", "chitin_plate", "ember_heart"]


def rows(paths: list[str]) -> list[dict[str, str]]:
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate path within source group")
    output = []
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        output.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return output


def build() -> dict:
    resources_blocks_plants = [
        "engineering/ashen-intake/resource-runtime/ASHEN_RESOURCE_RUNTIME_REPORT.json",
        "engineering/ashen-intake/block-runtime/ASHEN_BLOCK_RUNTIME_REPORT.json",
        "engineering/ashen-intake/plant-runtime/ASHEN_PLANT_RUNTIME_REPORT.json",
    ]
    resources_blocks_plants += [f"behavior_pack/items/{value}.item.json" for value in RESOURCES]
    resources_blocks_plants += [f"behavior_pack/blocks/{value}.block.json" for value in FULL_BLOCKS + PLANTS]
    resources_blocks_plants += [f"resource_pack/models/aionbound/ashen/{value}.geo.json" for value in PLANTS]
    resources_blocks_plants += [f"resource_pack/textures/aionbound/ashen/plants/{value}.png" for value in PLANTS]

    entity_runtime = ["engineering/ashen-intake/entity-runtime/ASHEN_ENTITY_RUNTIME_REPORT.json"]
    entity_runtime += [f"behavior_pack/entities/aionbound/ashen/{value}.entity.json" for value in CREATURES]
    entity_runtime += [f"resource_pack/entity/aionbound/ashen/{value}.entity.json" for value in CREATURES]
    entity_runtime += [f"behavior_pack/spawn_rules/aionbound/ashen/{value}.spawn_rules.json" for value in NATURAL_CREATURES]

    worldgen_structures = [
        "engineering/ashen-intake/ecology-worldgen/ASHEN_ECOLOGY_WORLDGEN.json",
        "engineering/ashen-intake/structure-assemblies/ASHEN_STRUCTURE_ASSEMBLIES.json",
        "engineering/ashen-intake/structure-assemblies/ASHEN_STRUCTURE_VALIDATION_REPORT.json",
    ]
    worldgen_structures += [f"behavior_pack/features/ah_ecology_{value}.feature.json" for value in PLANTS]
    worldgen_structures += [f"behavior_pack/feature_rules/ah_ecology_{value}.feature_rule.json" for value in PLANTS]
    worldgen_structures += [f"behavior_pack/structures/aionbound/{value}.mcstructure" for value in STRUCTURES]
    worldgen_structures += [f"behavior_pack/features/{value}.structure_feature.json" for value in STRUCTURES]
    worldgen_structures += [f"behavior_pack/feature_rules/{value}.structure_feature_rule.json" for value in STRUCTURES]

    loot_economy = [
        "engineering/ashen-intake/structure-economy/ASHEN_STRUCTURE_ECONOMY.json",
        "engineering/ashen-intake/structure-economy/ASHEN_STRUCTURE_ECONOMY_VALIDATION_REPORT.json",
        "behavior_pack/scripts/ashen_structure_reward_data.js",
        "behavior_pack/scripts/ashen_structure_rewards.js",
    ]
    loot_economy += [f"behavior_pack/loot_tables/blocks/ashen/{value}.json" for value in FULL_BLOCKS + PLANTS]
    loot_economy += [f"behavior_pack/loot_tables/entities/ashen/{value}{'_ecology' if value == 'ash_drake' else ''}.json" for value in CREATURES]
    loot_economy += [f"behavior_pack/loot_tables/chests/ashen/{value}.json" for value in ["burned_camp", "char_wagon", "broken_bridge", "basalt_arch", "ash_watchtower", "ancient_kiln", "ash_cave", "ember_forge"]]
    loot_economy += ["behavior_pack/recipes/ashen_ash_log_to_char_planks.recipe.json", "behavior_pack/recipes/ashen_smolder_bark_to_char_planks.recipe.json"]

    codex_runtime = [
        "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        "engineering/ashen-intake/codex/ASHEN_CODEX_PROGRESSION_INTAKE_MAP.json",
        "behavior_pack/scripts/wave1_codex_ashen_data.js",
        "behavior_pack/scripts/wave1_codex_data.js",
        "behavior_pack/scripts/catalog.js",
        "behavior_pack/scripts/codex.js",
        "behavior_pack/scripts/state.js",
        "behavior_pack/scripts/router.js",
        "behavior_pack/scripts/runtime.js",
        "engineering/ashen-intake/codex-runtime/test_ashen_codex_runtime.py",
        "tests/wave1_codex_runtime_events.test.mjs",
        "tests/wave1_codex_v4.test.mjs",
    ]

    equipment_runtime_crafting = [
        "engineering/ashen-intake/equipment-runtime-ashen/ASHEN_EQUIPMENT_RUNTIME_REPORT.json",
        "engineering/ashen-intake/economy/author_ashen_equipment_recipes.py",
        "engineering/ashen-intake/economy/test_ashen_equipment_recipes.py",
    ]
    for value in EQUIPMENT:
        equipment_runtime_crafting += [
            f"resource_pack/attachables/{value}.attachable.json",
            f"resource_pack/models/aionbound/ashen/equipment/{value}.geo.json",
            f"resource_pack/animations/aionbound/ashen/equipment/{value}.animation.json",
            f"resource_pack/textures/aionbound/ashen/equipment/{value}.png",
            f"resource_pack/textures/aionbound/ashen/equipment/models/{value}.png",
            f"behavior_pack/{'blocks' if value in PLACEABLE_EQUIPMENT else 'items'}/{value}.{'block' if value in PLACEABLE_EQUIPMENT else 'item'}.json",
        ]
    equipment_runtime_crafting += [f"behavior_pack/items/{value}.item.json" for value in DERIVED]
    equipment_runtime_crafting += [f"resource_pack/textures/aionbound/ashen/components/{value}.png" for value in DERIVED]
    equipment_runtime_crafting += [f"behavior_pack/recipes/ashen_{value}.recipe.json" for value in EQUIPMENT if value not in PLACEABLE_EQUIPMENT]
    equipment_runtime_crafting += [f"behavior_pack/recipes/ashen_{value}.recipe.json" for value in DERIVED]

    kiln_sky = [
        "engineering/ashen-intake/kiln-sky-runtime/KILN_SKY_RUNTIME_EVIDENCE.json",
        "engineering/ashen-intake/kiln-sky-runtime/ACTIVATION_WITHHELD.md",
        "behavior_pack/scripts/kiln_sky.js",
        "behavior_pack/scripts/ashen_rewards.js",
        "tests/wave1_kiln_sky.test.mjs",
        "tests/wave1_ashen_rewards.test.mjs",
    ]

    functional_equipment = [
        "engineering/ashen-intake/equipment-functional/ASHEN_EQUIPMENT_FUNCTIONAL_EVIDENCE.json",
        "engineering/ashen-intake/equipment-functional/ACTIVATION_WITHHELD.md",
        "engineering/ashen-intake/equipment-functional/README.md",
        "engineering/ashen-intake/equipment-functional/build_ashen_equipment_evidence.py",
        "engineering/ashen-intake/equipment-functional/test_ashen_equipment_evidence.py",
        "engineering/ashen-intake/equipment-runtime-ashen/test_runtime.py",
        "behavior_pack/scripts/ashen_equipment.js",
        "behavior_pack/scripts/ashen_equipment_roles.js",
        "tests/wave1_ashen_equipment_functional.test.mjs",
    ]

    native_aggregates = [
        "engineering/native-assets/ashen/representative/ASHEN_REPRESENTATIVE_NATIVE_REPORT.json",
        "engineering/native-assets/ashen/plants/ASHEN_PLANT_NATIVE_REPORT.json",
        "engineering/native-assets/ashen/creatures/ASHEN_CREATURE_NATIVE_REPORT.json",
        "engineering/native-assets/ashen/landmarks/ASHEN_LANDMARK_NATIVE_REPORT.json",
        "engineering/native-assets/ashen/equipment/ASHEN_EQUIPMENT_NATIVE_REPORT.json",
    ]
    groups = {
        "resources_blocks_plants": rows(resources_blocks_plants),
        "entity_client_spawn_runtime": rows(entity_runtime),
        "ecology_structures_features_rules": rows(worldgen_structures),
        "loot_and_acquisition_economy": rows(loot_economy),
        "decision_ledger_v3_and_codex_runtime": rows(codex_runtime),
        "equipment_13_plus_derived_4_and_crafting": rows(equipment_runtime_crafting),
        "kiln_sky_dedicated_service_activation_withheld": rows(kiln_sky),
        "functional_equipment_dedicated_activation_withheld": rows(functional_equipment),
        "native_aggregate_receipts": rows(native_aggregates),
    }
    all_paths = [row["path"] for values in groups.values() for row in values]
    if len(all_paths) != len(set(all_paths)):
        raise ValueError("duplicate path across source groups")
    return {
        "schema": "aionbound.wave1.ashen.implemented_source_closure.v1",
        "status": "EXACT_IMPLEMENTED_ASHEN_SOURCE_CLOSURE",
        "base": {"commit": "61a77d7", "authority": "G8 successor integration line"},
        "groups": groups,
        "pending_follow_up": {
            "kiln_sky_shared_runtime_activation": "WITHHELD_BY_DEDICATED_EVIDENCE",
            "functional_equipment_shared_runtime_activation": "WITHHELD_BY_DEDICATED_EVIDENCE",
            "creative": "W1-CREATIVE-005_DEFERRED",
        },
        "proof_boundary": "SOURCE PATH, BYTE HASH, IDENTIFIER, AND STATIC EVIDENCE CLOSURE ONLY; NO BUILD, PACKAGE, BDS, CLIENT, MULTIPLAYER, CONSOLE, OR RELEASE PROOF",
    }


def main() -> None:
    TARGET.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
