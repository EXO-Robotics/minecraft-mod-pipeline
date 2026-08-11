#!/usr/bin/env python3
"""Build the immutable, source-only Packet 002 runtime ownership map.

The map is deliberately read from the exact integration base commit.  This keeps
the planning receipt deterministic after implementation starts and prevents a
later working tree from being mistaken for evidence about the mapped baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


BASE_COMMIT = "9acf1b0f62ade90b59ba65e0a9e0618852ff3159"
BASE_TREE = "9b7b425e535439658df29c92f82ad73e9aa54e3d"
ALLOWED = {"KEEP", "REFINE", "REPLACE", "SUPERSEDE", "DEFER"}

AUTHORITY = [
    ("program/crazycraft-pack-production-v1/studio-prep/creative/WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json", "aa1f54df10d27d5c5675aae843ffe0d2946123d12a6509f7f021408bcdde9fb5"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_ASHEN.md", "f5b2ff909a6e7b7669da561cc2659439819227f99d15d221dbea0147750d3727"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/02_loot/LOOT_BOSSES.md", "4d80925a113bb0cca67e2405047cd228a2df2ccd2c680e1e51ccd04b6f2d63d8"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/03_crafting/CRAFTING_TREE.md", "1f3482ba3dd9f916e08aa544153cc841871a729a2e82d9e75601715f4b5ee807"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/04_equipment/EQUIPMENT_PROGRESSION.md", "7ecf57e6af099ae3cda8a7432228fb5ee996f20b02b76888a82c0c1a3e3c891d"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/05_structures/STRUCTURES_DESIGN.md", "9e62ae9ba6c1da33b64ff0bfa4ac4799b083c6de995585424864d5cf2b0cb076"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/06_world_gen/WORLD_GENERATION.md", "bc18a1e1f73d6045ab7e583afe910ca13d4776d439c8f3dfb45dae5784372f4b"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/07_bosses/BOSS_PROGRESSION.md", "5ef85e1e0b29973a617f7dca4a8b119443c01644ba33f0e11166ef8d417d5a6f"),
    ("program/crazycraft-pack-production-v1/studio-prep/creative/08_codex/CODEX_ENTRIES_CREATURES.md", "fd07694eee0c8d478b44363e822e0116f4ca09c92775661350ed8468342b01bf"),
    ("program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-002-ashen-highlands/MANIFEST_FULL.json", "6cb3bd25a1ef473e60e5ed0ebf78288bcc4d53db1ff4ec74db4d22ddb036c738"),
    ("engineering/normalization/PACKET_NORMALIZATION_INVENTORY.json", "4a65ccbc10f47a86e3aec649874916a9d4ad5cb9feef7817d75a527774a3a842"),
    ("engineering/reconciliation/G7_TO_WAVE1_RECONCILIATION_MATRIX.json", "6093e69d0e924e8330ec6bd2eb0682fb29f328cc1758d78c5ac57b7e3c166705"),
    ("engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json", "3e2b64785da9310b098e06981ebc95777ddc7e5d2666f803b79ce374470a9561"),
]

TEMPLATE_EVIDENCE = {
    "hostile_melee_ground": ("behavior_pack/entities/cinder_brood_hatchling.entity.json", "3c82a047a489a47d383313a17935bcb73075578487f4ee476640d274f33b2759"),
    "ambient_air": ("behavior_pack/entities/breezetail.entity.json", "e3797b2428d2813931f1045ec50840a3cd4e2b7dce284caf20b1f7c528643cbe"),
    "hostile_pack": ("behavior_pack/entities/rot_wolf.entity.json", "52a45a7ddf9279c0b49af9a887c1196e6c24b0d974a4c9a57dbeacefa5918d9d"),
    "neutral_retaliatory": ("behavior_pack/entities/rootback_boar.entity.json", "7a356399b856d10edadbc706c2ee4adc3b7616b7370f6e6bcc8b2b60c5a531d5"),
    "neutral_rare": ("behavior_pack/entities/briar_elk.entity.json", "f0a6761fb5f7f10a0bb5425f1ee1bbb0f88652cba18841af6a74e56dbc69f8b9"),
    "legacy_ash_boss_cast": ("behavior_pack/entities/ash_sovereign_wyrm.entity.json", "fd55521297173234fc4fde18a78e49b9f03216f721ec31a693ca9f2787cfdd4e"),
}

CREATURES = [
    ("ash_mite", "swarm_hostile", "hostile_melee_ground", "ground swarm", "high_near_vents_and_caves", ["ember_resin"], ["Ash Dust", "Mite Mandible", "Swarm Queen Scale"]),
    ("ember_crow", "ambient_air", "ambient_air", "free flight", "medium_sky", [], ["Char Feather", "Cinder Beak"]),
    ("magma_lizard", "small_hostile", "hostile_melee_ground", "ground scramble", "medium_hot_rock", ["volcanic_glass_shard"], ["Heat Scale", "Warm Blood Vial"]),
    ("furnace_beetle", "hostile", "hostile_melee_ground", "ground crawl", "medium_low", ["furnace_chitin"], ["Smolder Gland", "Beetle Core Fragment"]),
    ("char_wolf", "hostile_pack", "hostile_pack", "ground pack run", "medium_packs", [], ["Char Pelt", "Ember Fang", "Pack Cinder Mark"]),
    ("cinder_lynx", "elite_hunter", "hostile_melee_ground", "ground stalk and pursue", "low", ["heatstone"], ["Cinder Pelt", "Lynx Claw"]),
    ("ash_ram", "neutral_territorial", "neutral_retaliatory", "ground roam and retaliate", "low_plateaus", ["basalt_core"], ["Ash Wool", "Ram Horn Curve"]),
    ("soot_stag", "neutral_rare", "neutral_rare", "ground roam and retaliate", "low_plateaus", ["fire_bloom_seed"], ["Soot Antler", "Char Hide", "Stag Heart Cinder"]),
    ("basalt_tortoise", "tank_neutral", "neutral_retaliatory", "slow ground roam and retaliate", "rare", ["basalt_core"], ["Shell Plate"]),
    ("ash_drake", "chapter_apex", "legacy_ash_boss_cast", "arena aerial and landing phases", "arena_only_extremely_rare", ["ash_drake_horn", "basalt_core", "heatstone", "ember_resin", "furnace_chitin", "volcanic_glass_shard", "ash_crystal", "ember_forge_core"], ["Drake Scale", "Ember Sinew"]),
]

PLANTS = [
    ("cinder_grass", "fiber and tinder"),
    ("ash_fern", "bandages under ash"),
    ("smoke_reed", "arrow shafts and ash repeater ammo body"),
    ("char_shrub", "fuel"),
    ("soot_mushroom", "risky food"),
    ("magma_moss", "heat dye and resist salve"),
    ("glow_root", "cave light"),
    ("basalt_flower", "rare catalyst"),
    ("ember_vine", "rope under heat"),
    ("fire_bloom", "consumable and seed"),
]

BLOCKS = [
    "ash_log", "char_planks", "ash_soil", "cinder_gravel", "smolder_stone",
    "basalt_brick", "basalt_pillar", "heat_bark", "ember_moss", "volcanic_glass_block",
]

RESOURCES = [
    ("smolder_bark", "C", "harvested from approved Ashen bark source"),
    ("charbone", "C-U", "creature or structure economy"),
    ("sulfur_cluster", "U", "yellow crust resource node"),
    ("volcanic_glass_shard", "U", "cooled-flow node and creature loot"),
    ("ember_resin", "U-R", "creature, totem, and structure economy"),
    ("heatstone", "U-R", "vent-adjacent node and creature loot"),
    ("furnace_chitin", "U-R", "furnace beetle and boss loot"),
    ("basalt_core", "R", "deep-stone node, tortoise, and boss loot"),
    ("ash_crystal", "R", "rare structure and bridge resource"),
    ("fire_bloom_seed", "U", "fire bloom and soot stag source"),
]

STRUCTURES = [
    ("fire_totem", "uncommon_clusters", None, False),
    ("burned_camp", "uncommon_edges", "ah_to_cm_teaser", False),
    ("char_wagon", "uncommon_routes", None, False),
    ("broken_bridge", "ravine_gated", None, False),
    ("basalt_arch", "rare_landmark", None, False),
    ("ash_watchtower", "rare_ridges", None, False),
    ("ancient_kiln", "rare", None, False),
    ("ember_forge", "very_rare_one_per_highlands_realm", None, True),
    ("lava_shrine", "rare_vents", None, False),
    ("ash_cave", "uncommon_faces", None, False),
]

EQUIPMENT = [
    ("basalt_hammer", "weapon", "anti-tank; stun/structure/armored-foe fantasy"),
    ("ember_great_axe", "weapon", "wide heat pressure and apex preparation"),
    ("ash_repeater", "weapon", "ranged heat with ammo economy"),
    ("ashen_helmet", "armor", "Ashen set heat-face piece"),
    ("ashen_chest", "armor", "Ashen set vent-core piece"),
    ("ashen_legs", "armor", "Ashen set plated-mobility piece"),
    ("ashen_boots", "armor", "Ashen set cooled-tread piece"),
    ("basalt_pick", "tool", "hard stone and ore"),
    ("ember_hammer", "tool", "forge smash and basalt"),
    ("ore_chisel", "tool", "precision node harvest"),
    ("ember_totem", "accessory", "heat ward"),
    ("briar_ring", "accessory", "existing thorn chip base; AH tempering remains deferred"),
    ("ash_drake_horn", "trophy", "chapter-two progression seal and display"),
    ("ember_forge_core", "trophy", "structure seal / forge-event reward identity"),
]

NON_WAREHOUSE_TERMS = [
    "Ash Dust", "Ash Wool", "Beetle Core Fragment", "Char Feather", "Char Hide",
    "Char Pelt", "Cinder Beak", "Cinder Pelt", "Drake Scale", "Ember Fang",
    "Ember Sinew", "Heat Scale", "Lynx Claw", "Mite Mandible", "Pack Cinder Mark",
    "Ram Horn Curve", "Shell Plate", "Smolder Gland", "Soot Antler",
    "Stag Heart Cinder", "Swarm Queen Scale", "Warm Blood Vial",
]


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE_COMMIT}:{path}"])


def base_present(path: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{BASE_COMMIT}:{path}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def normalization_index() -> dict[tuple[str, str], dict]:
    payload = json.loads(git_bytes("engineering/normalization/PACKET_NORMALIZATION_INVENTORY.json"))
    return {(row["packet_id"], row["warehouse_id"]): row for row in payload["assets"]}


def normalized_evidence(index: dict[tuple[str, str], dict], packet: str, asset_id: str) -> dict:
    row = index[(packet, asset_id)]
    return {
        "packet_id": packet,
        "warehouse_id": asset_id,
        "category": row["category"],
        "runtime_id": row["runtime_id"],
        "status": row["status"],
        "issues": row["issues"],
        "canonical_hashes": {key: value["sha256"] for key, value in sorted(row["canonical"].items())},
        "native_roundtrip_risk": row["normalization"]["native_roundtrip_risk"],
        "declared_animation_gap": row["normalization"]["animation_gap"],
        "native_locator_gap": row["normalization"]["native_locator_gap"],
    }


def target(path: str, owner: str) -> dict:
    return {"path": path, "owner": owner, "present_at_base": base_present(path)}


def creature_rows(index: dict[tuple[str, str], dict]) -> list[dict]:
    rows = []
    for asset_id, role, pattern, motion, density, warehouse, withheld in CREATURES:
        is_boss = asset_id == "ash_drake"
        path, sha = TEMPLATE_EVIDENCE[pattern]
        owner = "ASHEN_ENTITY_RUNTIME"
        dedicated = [
            target(f"behavior_pack/entities/{asset_id}.entity.json", owner),
            target(f"behavior_pack/loot_tables/entities/{asset_id}.json", "ASHEN_ECONOMY"),
            target(f"resource_pack/entity/{asset_id}.entity.json", "ASHEN_ASSET_RUNTIME"),
            target(f"resource_pack/models/aionbound/ashen/{asset_id}.geo.json", "ASHEN_ASSET_RUNTIME"),
            target(f"resource_pack/animations/aionbound/ashen/{asset_id}.animation.json", "ASHEN_ASSET_RUNTIME"),
            target(f"resource_pack/animation_controllers/aionbound/ashen/{asset_id}.animation_controller.json", "ASHEN_ASSET_RUNTIME"),
            target(f"resource_pack/textures/aionbound/ashen/{asset_id}.png", "ASHEN_ASSET_RUNTIME"),
        ]
        if not is_boss:
            dedicated.insert(1, target(f"behavior_pack/spawn_rules/{asset_id}.spawn_rules.json", "ASHEN_WORLDGEN"))
        rows.append({
            "id": asset_id,
            "role": role,
            "classification": "SUPERSEDE" if is_boss else "REFINE",
            "classification_reason": (
                "Approved ash_drake identity supersedes the legacy ash_sovereign_wyrm cast; the generic legacy values are not transferred."
                if is_boss else "New approved identity refines a named, proven declarative role pattern without inheriting its numbers or cast identity."
            ),
            "runtime_class": "boss" if is_boss else ("ambient" if role == "ambient_air" else "neutral" if "neutral" in role else "hostile"),
            "motion_requirement": motion,
            "ai_bar": (
                ["arena admission", "readable phase motion", "aerial traversal", "target composition", "reset", "terminal handling"]
                if is_boss else ["roam", "readable reaction"] + ([] if role == "ambient_air" else ["acquire or retaliate as role requires", "navigate", "attack", "recover or disengage"])
            ),
            "g7_or_whisperwood_pattern": {"name": pattern, "path": path, "sha256": sha, "values_transfer": False},
            "spawn": {
                "design_density": density,
                "natural": not is_boss,
                "exact_weight": "ENGINEERING_TUNING_WITHIN_GLOBAL_BUDGET_NOT_SELECTED_HERE",
                "group_size": "NOT_SELECTED_HERE",
                "loaded_area_cap": "SHARED_NATURAL_ENTITIES_TARGET_40_NOT_INCREASED",
            },
            "loot": {
                "approved_warehouse_identities": warehouse,
                "withheld_nonwarehouse_identities": withheld,
                "probabilities_and_quantities": "DEFER_W1_CREATIVE_004_LATER_REGIONS",
            },
            "persistence": {
                "ordinary_entity_restart_persistence": "NOT_REQUIRED_BY_CURRENT_AUTHORITY" if not is_boss else "N/A_BOSS_USES_ENCOUNTER_STATE",
                "encounter_or_reward_state": "DEFER_W1_CREATIVE_003_AND_004" if is_boss else "NONE",
            },
            "codex_hooks": ["observed_or_encountered", "defeated_if_role_appropriate"] + (["chapter_two_terminal"] if is_boss else []),
            "source_targets": dedicated,
            "normalization_evidence": normalized_evidence(index, "002", asset_id),
            "implementation_gate": "DEFER_KILN_SKY_ENVELOPE" if is_boss else "READY_AFTER_ASSET_AND_LOOT_AUTHORITY",
        })
    return rows


def plant_rows(index: dict[tuple[str, str], dict]) -> list[dict]:
    return [{
        "id": asset_id,
        "purpose": purpose,
        "classification": "REFINE",
        "pattern_evidence": ["behavior_pack/blocks/star_grass.block.json", "behavior_pack/features/ww_ecology_star_grass.feature.json", "behavior_pack/feature_rules/ww_ecology_star_grass.feature_rule.json"],
        "harvest_identity": asset_id,
        "placement_numbers": "ENGINEERING_TUNING_NOT_SELECTED_HERE",
        "regrowth": "DEFER_NO_ASHEN_REGROWTH_AUTHORITY",
        "persistence": "NONE",
        "codex_hooks": ["recognized_proximity", "harvested"],
        "source_targets": [
            target(f"behavior_pack/blocks/{asset_id}.block.json", "ASHEN_PLANT_RUNTIME"),
            target(f"behavior_pack/loot_tables/blocks/{asset_id}.json", "ASHEN_ECONOMY"),
            target(f"behavior_pack/features/ah_ecology_{asset_id}.feature.json", "ASHEN_WORLDGEN"),
            target(f"behavior_pack/feature_rules/ah_ecology_{asset_id}.feature_rule.json", "ASHEN_WORLDGEN"),
            target(f"resource_pack/models/aionbound/ashen/plants/{asset_id}.geo.json", "ASHEN_ASSET_RUNTIME"),
            target(f"resource_pack/textures/aionbound/ashen/plants/{asset_id}.png", "ASHEN_ASSET_RUNTIME"),
        ],
        "normalization_evidence": normalized_evidence(index, "002", asset_id),
        "implementation_gate": "NATIVE_REPAIR_AND_PLACEMENT_TUNING",
    } for asset_id, purpose in PLANTS]


def block_rows(index: dict[tuple[str, str], dict]) -> list[dict]:
    return [{
        "id": asset_id,
        "classification": "REFINE",
        "pattern_evidence": ["behavior_pack/blocks/whisperwood_log.block.json", "resource_pack/blocks.json"],
        "natural_distribution": "BIND_ONLY_WHERE_CREATIVE_TERRAIN_OR_RESOURCE_RELATIONSHIP_REQUIRES",
        "persistence": "NONE",
        "codex_hooks": ["harvested_or_crafted"],
        "source_targets": [
            target(f"behavior_pack/blocks/{asset_id}.block.json", "ASHEN_BLOCK_RESOURCE_RUNTIME"),
            target(f"behavior_pack/loot_tables/blocks/{asset_id}.json", "ASHEN_ECONOMY"),
            target(f"resource_pack/textures/aionbound/ashen/blocks/{asset_id}.png", "ASHEN_ASSET_RUNTIME"),
        ],
        "normalization_evidence": normalized_evidence(index, "002", asset_id),
        "implementation_gate": "STATIC_BLOCK_REGISTRY_AND_AFFECTED_WORLDGEN_CLOSURE",
    } for asset_id in BLOCKS]


def resource_rows(index: dict[tuple[str, str], dict]) -> list[dict]:
    return [{
        "id": asset_id,
        "rarity": rarity,
        "acquisition_authority": acquisition,
        "classification": "REFINE",
        "pattern_evidence": ["behavior_pack/items/hollow_amber.item.json", "behavior_pack/loot_tables/entities/rot_wolf.json"],
        "probabilities_and_quantities": "DEFER_W1_CREATIVE_004_LATER_REGIONS",
        "persistence": "NONE",
        "codex_hooks": ["first_acquired", "harvested_if_node"],
        "source_targets": [
            target(f"behavior_pack/items/{asset_id}.item.json", "ASHEN_BLOCK_RESOURCE_RUNTIME"),
            target(f"resource_pack/textures/items/{asset_id}.png", "ASHEN_PRESENTATION"),
        ],
        "normalization_evidence": normalized_evidence(index, "002", asset_id),
        "implementation_gate": "IDENTITY_READY_NUMERIC_LOOT_DEFERRED",
    } for asset_id, rarity, acquisition in RESOURCES]


def structure_rows(index: dict[tuple[str, str], dict]) -> list[dict]:
    return [{
        "id": asset_id,
        "rarity_and_placement": rarity,
        "transition": transition,
        "goal_structure": goal,
        "classification": "REFINE",
        "classification_reason": "Reuse the proven structure-template pipeline, but author approved Ashen assembly bytes, placement predicates, and identity-specific rewards.",
        "packet_prop_is_not_structure_assembly": True,
        "persistence": "PER_PLAYER_DISCOVERY_AND_CLAIM_GUARD" if not goal else "DEFER_FORGE_AND_BOSS_OWNERSHIP_SEMANTICS",
        "codex_hooks": ["recognized_proximity", "first_successful_activation"] + (["cm_rumor"] if transition else []),
        "source_targets": [
            target(f"behavior_pack/structures/aionbound/{asset_id}.mcstructure", "ASHEN_STRUCTURE_ASSEMBLY"),
            target(f"behavior_pack/features/{asset_id}.structure_feature.json", "ASHEN_WORLDGEN"),
            target(f"behavior_pack/feature_rules/{asset_id}.structure_feature_rule.json", "ASHEN_WORLDGEN"),
            target(f"behavior_pack/loot_tables/chests/ashen/{asset_id}.json", "ASHEN_ECONOMY"),
        ],
        "normalization_evidence": normalized_evidence(index, "002", asset_id),
        "implementation_gate": "KILN_SKY_ENVELOPE_AND_REWARD_AUTHORITY" if goal else "NATIVE_REPAIR_ASSEMBLY_AND_LOOT_AUTHORITY",
    } for asset_id, rarity, transition, goal in STRUCTURES]


def equipment_rows(index: dict[tuple[str, str], dict]) -> list[dict]:
    rows = []
    for asset_id, category, role in EQUIPMENT:
        existing = asset_id == "briar_ring"
        display = category == "trophy"
        source_targets = [
            target(f"behavior_pack/items/{asset_id}.item.json", "ASHEN_EQUIPMENT_RUNTIME"),
            target(f"behavior_pack/recipes/{asset_id}.recipe.json", "ASHEN_ECONOMY"),
            target(f"resource_pack/attachables/{asset_id}.attachable.json", "ASHEN_ASSET_RUNTIME"),
            target(f"resource_pack/models/aionbound/ashen/equipment/{asset_id}.geo.json", "ASHEN_ASSET_RUNTIME"),
            target(f"resource_pack/animations/aionbound/ashen/equipment/{asset_id}.animation.json", "ASHEN_ASSET_RUNTIME"),
            target(f"resource_pack/textures/items/{asset_id}.png", "ASHEN_PRESENTATION"),
        ]
        if display:
            source_targets.extend([
                target(f"behavior_pack/blocks/{asset_id}.block.json", "ASHEN_EQUIPMENT_RUNTIME"),
                target(f"behavior_pack/loot_tables/blocks/{asset_id}.json", "ASHEN_ECONOMY"),
            ])
        rows.append({
            "id": asset_id,
            "category": category,
            "role": role,
            "classification": "KEEP" if existing else "REPLACE",
            "classification_reason": (
                "The base briar_ring identity, recipe, art, and bounded thorn-chip role already exist; any AH-tempered extension remains deferred."
                if existing else "Approved Packet 006 identity replaces legacy active-content identity while refining the shared equipment framework."
            ),
            "framework_classification": "REFINE",
            "acquisition": "CRAFT_OR_REWARD_GRAPH_REQUIRED",
            "durability_and_repair": "REQUIRED_WHERE_APPLICABLE_VALUES_NOT_SELECTED_HERE",
            "sidegrade_sibling_identity": "DEFER_W1_CREATIVE_005" if asset_id in {"basalt_hammer", "briar_ring"} else "NOT_REQUESTED",
            "boss_reward_grant": "DEFER_W1_CREATIVE_003_AND_004" if asset_id in {"ash_drake_horn", "ember_forge_core"} else "N/A",
            "codex_hooks": ["recipe_or_reward_discovered", "first_craft_or_grant"],
            "source_targets": source_targets,
            "normalization_evidence": normalized_evidence(index, "006", asset_id),
            "implementation_gate": "KEEP_BASE_ONLY" if existing else "ASSET_REPAIR_ECONOMY_AND_ROLE_SEMANTICS",
        })
    return rows


def build() -> dict:
    index = normalization_index()
    creatures = creature_rows(index)
    plants = plant_rows(index)
    blocks = block_rows(index)
    resources = resource_rows(index)
    structures = structure_rows(index)
    equipment = equipment_rows(index)
    payload = {
        "schema": "aionbound.wave1.ashen_runtime_implementation_map.v1",
        "status": "SOURCE_OWNERSHIP_MAP_COMPLETE_IMPLEMENTATION_BLOCKED_ON_RATIFICATION_AND_ASSET_REPAIR",
        "proof_boundary": {
            "bp_rp_edits": "NOT_PERFORMED",
            "build": "NOT_RUN",
            "bds": "NOT_RUN",
            "client": "NOT_RUN",
            "runtime_behavior": "NOT_PROVEN",
        },
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE, "g7_immutable": True, "checkpoint_1_passed_at_base": True},
        "authority": [{"path": path, "sha256": sha} for path, sha in AUTHORITY],
        "companion_lane_evidence": [
            {
                "scope": "Packet 002 binding authority and implementation gates",
                "commit": "8bd48a13ff3448f062c2752f9fc8d26668da2bbf",
                "tree": "87ab1fff18d04d323ff0104662f741121d4d85e0",
                "path": "engineering/ashen-intake/authority/ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json",
                "integration_note": "separate sibling-lane commit; integrator reviews and cherry-picks independently",
            },
            {
                "scope": "Packet 002 native/static readiness",
                "commit": "f3c39dd5766bfa5ba56486b2b804e2d6efdfa88f",
                "tree": "567925c0cefef0052e963960be2ef9b42754c575",
                "path": "engineering/native-assets/ashen/intake/ASHEN_PACKET_002_NATIVE_READINESS.json",
                "integration_note": "separate sibling-lane commit; integrator reviews and cherry-picks independently",
            },
        ],
        "classification_vocabulary": sorted(ALLOWED),
        "system_reconciliation": [
            {"system": "runtime_composition_and_router", "classification": "KEEP", "evidence": ["behavior_pack/scripts/runtime.js", "behavior_pack/scripts/router.js"], "rule": "compose Ashen handlers; never reintroduce an early-return suppression class"},
            {"system": "persistence_schema", "classification": "REFINE", "evidence": ["behavior_pack/scripts/state.js"], "rule": "append idempotent AH discovery, claim, boss, and reward state only after ownership authority"},
            {"system": "runtime_budgets", "classification": "REFINE", "evidence": ["behavior_pack/scripts/budgets.js"], "rule": "naturalEntitiesTarget remains 40; tune spawn locality before any cap request"},
            {"system": "legacy_g7_entity_cast", "classification": "SUPERSEDE", "evidence": ["engineering/reconciliation/G7_TO_WAVE1_RECONCILIATION_MATRIX.json"], "rule": "Packet 002 identities own active Ashen ecology; only role architecture is reusable"},
            {"system": "natural_spawn_rules", "classification": "REPLACE", "evidence": ["engineering/reconciliation/G7_TO_WAVE1_RECONCILIATION_MATRIX.json"], "rule": "nine natural Ashen rules plus arena-only Ash Drake; registry growth does not raise loaded density"},
            {"system": "structure_runtime_service", "classification": "KEEP", "evidence": ["behavior_pack/scripts/structures.js"], "rule": "keep bounded placement and claim architecture"},
            {"system": "structure_assemblies_and_placement", "classification": "REFINE", "evidence": ["behavior_pack/features/ancient_totem.structure_feature.json", "behavior_pack/feature_rules/ancient_totem.structure_feature_rule.json"], "rule": "author ten Ashen assemblies and region-specific rules; no G7 layout relabeling"},
            {"system": "loot_and_recipe_content", "classification": "REPLACE", "evidence": ["engineering/reconciliation/G7_TO_WAVE1_RECONCILIATION_MATRIX.json"], "rule": "approved Ashen identities own the economy after W1-CREATIVE-001/004 ratification"},
            {"system": "codex_schema", "classification": "KEEP", "evidence": ["behavior_pack/scripts/codex.js"], "rule": "append AH category pages and events without reordering existing indices"},
            {"system": "codex_and_progression_content", "classification": "REPLACE", "evidence": ["behavior_pack/scripts/wave1_codex_data.js"], "rule": "bind AH and CM-rumor content to Creative authority"},
            {"system": "equipment_framework", "classification": "REFINE", "evidence": ["behavior_pack/scripts/wave1_equipment_roles.js"], "rule": "Packet 006 roles replace legacy content and remain lateral"},
            {"system": "kiln_sky_boss_shell_and_rewards", "classification": "DEFER", "evidence": ["engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json", "behavior_pack/scripts/thorn_court.js"], "rule": "reuse architecture only after separate Kiln Sky envelope and Ashen loot ratification; never transfer Thorn Court values"},
        ],
        "blockers": [
            {
                "id": "W1-CREATIVE-001-ASHEN",
                "blocking": True,
                "scope": "later-region non-warehouse item identity",
                "terms": NON_WAREHOUSE_TERMS,
                "rule": "do not register these as items; curiosities remain Codex-only unless promoted",
            },
            {
                "id": "W1-CREATIVE-003-KILN-SKY",
                "blocking": True,
                "scope": "phase thresholds, timing, leash/timeout/wipe/reset/re-entry, add caps, multiplayer ownership/scaling, late join/disconnect, persistence, terminal grant, recovery, and repeat-clear semantics",
                "rule": "phase and attack names are binding identity, not executable numeric authority",
            },
            {
                "id": "W1-CREATIVE-004-ASHEN",
                "blocking": True,
                "scope": "creature/structure/boss probabilities, quantities, rolls, guarantees, and alternate seal semantics",
                "rule": "wire no final Ashen economy values before ratification",
            },
            {
                "id": "W1-CREATIVE-005",
                "blocking": False,
                "scope": "equipment sidegrade sibling identity",
                "rule": "keep approved base IDs; do not introduce Summit Hammer or AH-tempered sibling IDs",
            },
            {
                "id": "PACKET-002-NATIVE-REPAIR",
                "blocking": True,
                "scope": "custom-geometry creatures, plants, and structures",
                "counts": {
                    "native_repair_required": 30,
                    "native_full_cube_or_flat_item_blockbench_not_applicable": 20,
                    "real_editable_locator_assets": 0,
                    "declared_clip_sets_matching_exports": 0,
                    "texture_contract_compatible": 2,
                    "texture_contract_mismatch": 48,
                },
                "representative_gates": ["ash_drake", "ember_crow", "ash_ram", "fire_bloom", "smoke_reed", "ember_forge", "ancient_kiln"],
                "rule": "native locator round-trip, exact role-clip coverage, texture-contract disposition, native export equivalence, and Golden evidence are required before scaling custom-geometry construction; blocks/resources remain Blockbench-N/A only when shipped as native full cubes/flat items",
            },
        ],
        "worldgen_budget": {
            "classification": "REFINE",
            "global_natural_entities_target": 40,
            "global_structure_queue": 4,
            "global_structures_active": 1,
            "global_structure_blocks": 4096,
            "design_density_order": ["ash_mite", "ember_crow", "magma_lizard", "furnace_beetle", "char_wolf", "cinder_lynx", "ash_ram_and_soot_stag", "basalt_tortoise", "ash_drake_arena_only"],
            "soft_cell_targets": {"path_props": "4-10", "camps_and_wagons": "1-2", "major_landmarks": "0-1", "apex_arena": "1_per_biome_realm"},
            "ember_forge": "1_per_highlands_realm",
            "exact_spawn_weights": "NOT_SELECTED_HERE",
            "cap_change": "NONE",
        },
        "boss_boundary": {
            "identity": "Kiln Sky",
            "entity": "aionbound:ash_drake",
            "structure_link": "aionbound:ember_forge",
            "seal": "aionbound:ash_drake_horn",
            "phase_names": ["Ash Landing", "Vent Choir", "Glass Wing", "Kiln Heart"],
            "attack_names": ["Cinder Breath", "Tail Slag", "Thermal Dive", "Mite Shake", "Basalt Quake", "Glass Feather Storm"],
            "classification": "DEFER",
            "reusable_architecture": ["session-scoped encounter entity tagging", "bounded participant set", "idempotent world/player journals", "recovery-aware physical reward delivery"],
            "nontransferable_from_thorn_court": ["health", "damage", "phase thresholds", "timers", "leash", "reset", "scaling", "ownership", "reward rolls", "repeat semantics"],
            "source_targets_after_ratification": [
                target("behavior_pack/scripts/kiln_sky.js", "ASHEN_BOSS_RUNTIME"),
                target("behavior_pack/scripts/ashen_rewards.js", "ASHEN_BOSS_RUNTIME"),
                target("behavior_pack/loot_tables/encounters/ashen/kiln_sky_materials.json", "ASHEN_ECONOMY"),
                target("behavior_pack/loot_tables/chests/ashen/ember_forge.json", "ASHEN_ECONOMY"),
            ],
        },
        "codex_progression": {
            "classification": "REFINE",
            "entry_scope": ["10 creatures", "10 plants", "10 blocks", "10 resources", "10 structures", "14 Ashen-facing equipment links", "Kiln Sky", "Ashen chapter", "Crystal Marsh rumor"],
            "hooks": ["WW ashen_rumor consumed as invitation only", "AH discovery and acquisition events", "burned_camp CM rumor", "ash_drake terminal seal credit after ratification"],
            "sandbox_rule": "AH trophy or heat-resistant kit remains a soft transition, not a mandatory linear lock",
            "shared_integration_targets": [
                target("behavior_pack/scripts/wave1_ashen_codex_data.js", "ASHEN_CODEX_PROGRESSION"),
                target("behavior_pack/scripts/ashen_progression.js", "ASHEN_CODEX_PROGRESSION"),
                target("behavior_pack/scripts/wave1_codex_data.js", "PRIMARY_INTEGRATOR_ONLY"),
                target("behavior_pack/scripts/runtime.js", "PRIMARY_INTEGRATOR_ONLY"),
                target("behavior_pack/scripts/state.js", "PRIMARY_INTEGRATOR_ONLY"),
            ],
        },
        "shared_target_ownership": [
            {"path": "behavior_pack/scripts/catalog.js", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "register approved interaction and encounter routes"},
            {"path": "behavior_pack/scripts/runtime.js", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "compose Ashen services and events"},
            {"path": "behavior_pack/scripts/state.js", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "append-only schema/capacity migration"},
            {"path": "behavior_pack/scripts/wave1_codex_data.js", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "append Ashen data module without reordering existing indices"},
            {"path": "behavior_pack/scripts/wave1_equipment_roles.js", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "compose Packet 006 Ashen roles or import dedicated module"},
            {"path": "resource_pack/blocks.json", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "merge block registrations"},
            {"path": "resource_pack/textures/terrain_texture.json", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "merge terrain atlas keys"},
            {"path": "resource_pack/textures/item_texture.json", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "merge item atlas keys"},
            {"path": "resource_pack/texts/en_US.lang", "owner": "PRIMARY_INTEGRATOR_ONLY", "purpose": "merge approved display names"},
        ],
        "creatures": creatures,
        "plants": plants,
        "blocks": blocks,
        "resources": resources,
        "structures": structures,
        "equipment": equipment,
        "counts": {
            "creatures": len(creatures), "plants": len(plants), "blocks": len(blocks),
            "resources": len(resources), "structures": len(structures), "equipment_links": len(equipment),
            "packet_002_assets": len(creatures) + len(plants) + len(blocks) + len(resources) + len(structures),
            "unratified_nonwarehouse_terms": len(NON_WAREHOUSE_TERMS),
        },
        "implementation_order_after_authority": [
            "asset native repair and normalized runtime exports",
            "blocks, plants, resources, and bounded worldgen",
            "nine natural creature roles with loot withheld until ratified",
            "ten authored structures and structure-specific discovery",
            "Packet 006 Ashen-facing equipment and economy",
            "Kiln Sky shell, persistence, and recovery only after W1-CREATIVE-003/004",
            "Codex/progression composition and bounded vertical smoke",
        ],
        "not_authorized_or_proven": ["BP/RP construction by this lane", "Ashen build", "Ashen BDS", "client animation", "client UI", "multiplayer", "console", "PS4"],
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("ASHEN_RUNTIME_IMPLEMENTATION_MAP.json"))
    args = parser.parse_args()
    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
