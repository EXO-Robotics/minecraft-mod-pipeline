#!/usr/bin/env python3
"""Generate the exact-base, ratified Packet 002 implementation ownership map."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


BASE_COMMIT = "9c2880863ff260410028284228f5995b59dcacfc"
BASE_TREE = "91d7ed5ffbe94d693c5d37848942b2702edfbd69"
ALLOWED = {"KEEP", "REFINE", "REPLACE", "SUPERSEDE", "DEFER"}

LEDGER = ("engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json", "b554db9fab3fe16e59e2e3b36dfc310ff462078b170f14e1f9fe8a46999bbd0c")
PROPOSALS = {
    "W1-001-AH": ("engineering/authority/support-proposals/ashen/W1-001-AH.json", "dd26a683f7f3e5301b66d7f2861454b5bf6b79818d12e0e8e1b22b6f07217774"),
    "W1-003-KILN-SKY": ("engineering/authority/support-proposals/ashen/W1-003-KILN-SKY.json", "1b2d5f77185a1461040d7559d0d8ecdaf803d7727e419ceac32636865be85d7c"),
    "W1-004-AH": ("engineering/authority/support-proposals/ashen/W1-004-AH.json", "93736ff800b1c90c8a6547d84336a6650f8ae32750f262de8e460385a7a26889"),
}
AUTHORITY = [
    ("engineering/normalization/PACKET_NORMALIZATION_INVENTORY.json", "4a65ccbc10f47a86e3aec649874916a9d4ad5cb9feef7817d75a527774a3a842"),
    ("engineering/reconciliation/G7_TO_WAVE1_RECONCILIATION_MATRIX.json", "6093e69d0e924e8330ec6bd2eb0682fb29f328cc1758d78c5ac57b7e3c166705"),
    LEDGER,
    *PROPOSALS.values(),
    ("engineering/ashen-intake/authority/ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json", "ffa63451feda80fb078f897e2cd8270e1c1e0b4928c17bbc0fdcd10b572ffc7b"),
    ("engineering/native-assets/ashen/intake/ASHEN_PACKET_002_NATIVE_READINESS.json", "7ae160464a3c013a767587b1dc2d16150b2467b97eff012232c59eb2cc1a8690"),
    ("engineering/native-assets/ashen/representative/ASHEN_REPRESENTATIVE_NATIVE_REPORT.json", "ea4bc1c78f1dd532076b73c5620103c9043da170a519fbf3d531585d12481131"),
]

CREATURES = [
    ("ash_mite", "swarm_hostile", "ground swarm", "high_near_vents_and_caves", ["ember_resin"], ["Ash Dust", "Mite Mandible", "Swarm Queen Scale"]),
    ("ember_crow", "ambient_air", "free flight", "medium_sky", [], ["Char Feather", "Cinder Beak"]),
    ("magma_lizard", "small_hostile", "ground scramble", "medium_hot_rock", ["volcanic_glass_shard"], ["Heat Scale", "Warm Blood Vial"]),
    ("furnace_beetle", "hostile", "ground crawl", "medium_low", ["furnace_chitin"], ["Smolder Gland", "Beetle Core Fragment"]),
    ("char_wolf", "hostile_pack", "ground pack run", "medium_packs", [], ["Char Pelt", "Ember Fang", "Pack Cinder Mark"]),
    ("cinder_lynx", "elite_hunter", "ground stalk and pursue", "low", ["heatstone"], ["Cinder Pelt", "Lynx Claw"]),
    ("ash_ram", "neutral_territorial", "ground roam and retaliate", "low_plateaus", ["basalt_core"], ["Ash Wool", "Ram Horn Curve"]),
    ("soot_stag", "neutral_rare", "ground roam and retaliate", "low_plateaus", ["fire_bloom_seed"], ["Soot Antler", "Char Hide", "Stag Heart Cinder"]),
    ("basalt_tortoise", "tank_neutral", "slow ground roam and retaliate", "rare", ["basalt_core"], ["Shell Plate"]),
    ("ash_drake", "chapter_apex", "arena aerial and landing phases", "arena_only", ["ash_drake_horn", "basalt_core", "heatstone", "ember_resin", "furnace_chitin", "volcanic_glass_shard", "ash_crystal", "ember_forge_core"], ["Drake Scale", "Ember Sinew"]),
]
PLANTS = [("cinder_grass", "fiber and tinder"), ("ash_fern", "bandages under ash"), ("smoke_reed", "arrow shafts"), ("char_shrub", "fuel"), ("soot_mushroom", "risky food"), ("magma_moss", "heat dye and resist salve"), ("glow_root", "cave light"), ("basalt_flower", "rare catalyst"), ("ember_vine", "rope under heat"), ("fire_bloom", "consumable and seed")]
BLOCKS = ["ash_log", "char_planks", "ash_soil", "cinder_gravel", "smolder_stone", "basalt_brick", "basalt_pillar", "heat_bark", "ember_moss", "volcanic_glass_block"]
RESOURCES = [("smolder_bark", "C"), ("charbone", "C-U"), ("sulfur_cluster", "U"), ("volcanic_glass_shard", "U"), ("ember_resin", "U-R"), ("heatstone", "U-R"), ("furnace_chitin", "U-R"), ("basalt_core", "R"), ("ash_crystal", "R"), ("fire_bloom_seed", "U")]
STRUCTURES = [("fire_totem", "uncommon_clusters", False), ("burned_camp", "uncommon_edges", False), ("char_wagon", "uncommon_routes", False), ("broken_bridge", "ravine_gated", False), ("basalt_arch", "rare_landmark", False), ("ash_watchtower", "rare_ridges", False), ("ancient_kiln", "rare", False), ("ember_forge", "very_rare_one_per_highlands_realm", True), ("lava_shrine", "rare_vents", False), ("ash_cave", "uncommon_faces", False)]
EQUIPMENT = [("basalt_hammer", "weapon"), ("ember_great_axe", "weapon"), ("ash_repeater", "weapon"), ("ashen_helmet", "armor"), ("ashen_chest", "armor"), ("ashen_legs", "armor"), ("ashen_boots", "armor"), ("basalt_pick", "tool"), ("ember_hammer", "tool"), ("ore_chisel", "tool"), ("ember_totem", "accessory"), ("briar_ring", "accessory"), ("ash_drake_horn", "trophy"), ("ember_forge_core", "trophy")]
NATIVE_PASS = {"ash_drake", "ember_crow", "ash_ram", "fire_bloom", "smoke_reed", "ember_forge", "ancient_kiln"}


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE_COMMIT}:{path}"])


def exact_json(path: str) -> dict:
    return json.loads(git_bytes(path))


def present(path: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{BASE_COMMIT}:{path}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def target(path: str, owner: str) -> dict:
    return {"path": path, "owner": owner, "present_at_base": present(path)}


def normalization_index() -> dict:
    data = exact_json("engineering/normalization/PACKET_NORMALIZATION_INVENTORY.json")
    return {(r["packet_id"], r["warehouse_id"]): r for r in data["assets"]}


def normalization(index: dict, packet: str, asset: str) -> dict:
    row = index[(packet, asset)]
    return {"packet_id": packet, "runtime_id": row["runtime_id"], "historical_initial_status": row["status"], "canonical_hashes": {k: v["sha256"] for k, v in sorted(row["canonical"].items())}}


def native_gate(asset: str, custom: bool = True) -> str:
    if asset in NATIVE_PASS:
        return "READY_NATIVE_REPRESENTATIVE_PASS"
    if custom:
        return "NATIVE_REPAIR_PENDING"
    return "READY_STATIC_TEXTURE_NORMALIZATION_BLOCKBENCH_NA_IF_NATIVE_CUBE_OR_FLAT_ITEM"


def identity_disposition(term: str, p001: dict) -> dict:
    for group in p001["aliases"]:
        if term in group["terms"]:
            return {"term": term, "disposition": "EXISTING_ASSET_ALIAS", "canonical_id": group["canonical_id"]}
    for row in p001["new_required_items"]:
        if term == row["term"]:
            return {"term": term, "disposition": "SELECTED_EXISTING_NEW_REQUIRED_ITEM", "canonical_id": row["id"], "craft_home": row["craft_home"], "sidegrade_authority": "NONE_W1-CREATIVE-005_DEFERRED"}
    if term in p001["narrative_codex_only"]:
        return {"term": term, "disposition": "NARRATIVE_CODEX_ONLY"}
    raise ValueError(f"unratified Ashen prose term: {term}")


def build() -> dict:
    index = normalization_index()
    proposals = {ticket: exact_json(path)["proposal"] for ticket, (path, _) in PROPOSALS.items()}
    p001, p003, p004 = proposals["W1-001-AH"], proposals["W1-003-KILN-SKY"], proposals["W1-004-AH"]

    creatures = []
    for asset, role, motion, density, warehouse, prose in CREATURES:
        boss = asset == "ash_drake"
        creatures.append({
            "id": asset, "role": role, "classification": "SUPERSEDE" if boss else "REFINE",
            "classification_reason": "Approved Ash Drake supersedes legacy cast; no legacy or Whisperwood values transfer." if boss else "Reuse proven role architecture without transferring identity or tuning.",
            "motion_requirement": motion,
            "ai_bar": ["arena admission", "phase motion", "aerial traversal", "target composition", "reset", "terminal handling"] if boss else (["roam", "idle variation", "readable reaction"] if role == "ambient_air" else ["roam", "react", "acquire or retaliate", "navigate", "attack", "recover or disengage"]),
            "spawn": {"natural": not boss, "design_density": density, "exact_weight": "ASHEN_ENGINEERING_TUNING_NOT_SELECTED", "group_size": "ASHEN_ENGINEERING_TUNING_NOT_SELECTED", "loaded_area_cap": "SHARED_TARGET_40_NO_INCREASE", "whisperwood_tuning_transfer": False},
            "loot": {"warehouse_identities": [f"aionbound:{x}" for x in warehouse], "ratified_prose_dispositions": [identity_disposition(x, p001) for x in prose], "numeric_authority": "W1-004-AH_CLOSED_INTERVAL_ENGINEERING_SELECTION_REQUIRED"},
            "persistence": {"ordinary_restart": "NOT_REQUIRED" if not boss else "ENCOUNTER_STATE_ONLY", "encounter_reward": "NONE" if not boss else "READY_W1-003-KILN-SKY_AND_W1-004-AH"},
            "codex_hooks": ["observed_or_encountered", "defeated_if_applicable"] + (["chapter_two_terminal"] if boss else []),
            "source_targets": [target(f"behavior_pack/entities/{asset}.entity.json", "ASHEN_ENTITY_RUNTIME"), target(f"behavior_pack/loot_tables/entities/{asset}.json", "ASHEN_ECONOMY"), target(f"resource_pack/entity/{asset}.entity.json", "ASHEN_ASSET_RUNTIME"), target(f"resource_pack/models/aionbound/ashen/{asset}.geo.json", "ASHEN_ASSET_RUNTIME"), target(f"resource_pack/animations/aionbound/ashen/{asset}.animation.json", "ASHEN_ASSET_RUNTIME")],
            "normalization_evidence": normalization(index, "002", asset), "implementation_gate": native_gate(asset),
        })

    plants = [{"id": a, "purpose": purpose, "classification": "REFINE", "placement_numbers": "ASHEN_ENGINEERING_TUNING_NOT_SELECTED", "regrowth": "DEFER_NO_ASHEN_REGROWTH_AUTHORITY", "whisperwood_tuning_transfer": False, "persistence": "NONE", "codex_hooks": ["recognized_proximity", "harvested"], "source_targets": [target(f"behavior_pack/blocks/{a}.block.json", "ASHEN_PLANT_RUNTIME"), target(f"behavior_pack/features/ah_ecology_{a}.feature.json", "ASHEN_WORLDGEN"), target(f"behavior_pack/feature_rules/ah_ecology_{a}.feature_rule.json", "ASHEN_WORLDGEN"), target(f"resource_pack/models/aionbound/ashen/plants/{a}.geo.json", "ASHEN_ASSET_RUNTIME")], "normalization_evidence": normalization(index, "002", a), "implementation_gate": native_gate(a)} for a, purpose in PLANTS]
    blocks = [{"id": a, "classification": "REFINE", "worldgen": "ONLY_WHERE_ASHEN_AUTHORITY_REQUIRES", "persistence": "NONE", "codex_hooks": ["harvested_or_crafted"], "source_targets": [target(f"behavior_pack/blocks/{a}.block.json", "ASHEN_BLOCK_RESOURCE_RUNTIME"), target(f"behavior_pack/loot_tables/blocks/{a}.json", "ASHEN_ECONOMY"), target(f"resource_pack/textures/aionbound/ashen/blocks/{a}.png", "ASHEN_ASSET_RUNTIME")], "normalization_evidence": normalization(index, "002", a), "implementation_gate": native_gate(a, False)} for a in BLOCKS]
    resources = [{"id": a, "rarity": rarity, "classification": "REFINE", "loot_numeric_authority": "W1-004-AH_CLOSED_INTERVAL_ENGINEERING_SELECTION_REQUIRED", "persistence": "NONE", "codex_hooks": ["first_acquired", "harvested_if_node"], "source_targets": [target(f"behavior_pack/items/{a}.item.json", "ASHEN_BLOCK_RESOURCE_RUNTIME"), target(f"resource_pack/textures/items/{a}.png", "ASHEN_PRESENTATION")], "normalization_evidence": normalization(index, "002", a), "implementation_gate": native_gate(a, False)} for a, rarity in RESOURCES]
    structures = [{"id": a, "rarity_and_placement": rarity, "goal_structure": goal, "classification": "REFINE", "assembly_rule": "Packet prop is visual input, not .mcstructure authority", "loot_numeric_authority": "W1-004-AH_CLOSED_INTERVAL_ENGINEERING_SELECTION_REQUIRED", "persistence": "W1-003-KILN-SKY_AND_W1-004-AH" if goal else "PER_PLAYER_DISCOVERY_AND_CLAIM_GUARD", "codex_hooks": ["recognized_proximity", "first_successful_activation"], "source_targets": [target(f"behavior_pack/structures/aionbound/{a}.mcstructure", "ASHEN_STRUCTURE_ASSEMBLY"), target(f"behavior_pack/features/{a}.structure_feature.json", "ASHEN_WORLDGEN"), target(f"behavior_pack/feature_rules/{a}.structure_feature_rule.json", "ASHEN_WORLDGEN"), target(f"behavior_pack/loot_tables/chests/ashen/{a}.json", "ASHEN_ECONOMY")], "normalization_evidence": normalization(index, "002", a), "implementation_gate": native_gate(a)} for a, rarity, goal in STRUCTURES]
    equipment = [{"id": a, "category": cat, "classification": "KEEP" if a == "briar_ring" else "REPLACE", "framework_classification": "REFINE", "acquisition": "CRAFT_OR_RATIFIED_REWARD_GRAPH_REQUIRED", "durability_and_repair": "REQUIRED_WHERE_APPLICABLE_VALUES_NOT_SELECTED", "sidegrade_sibling_identity": "DEFER_W1-CREATIVE-005" if a in {"basalt_hammer", "briar_ring"} else "NOT_REQUESTED", "boss_reward_grant": "READY_W1-004-AH" if a in {"ash_drake_horn", "ember_forge_core"} else "N/A", "codex_hooks": ["recipe_or_reward_discovered", "first_craft_or_grant"], "source_targets": [target(f"behavior_pack/items/{a}.item.json", "ASHEN_EQUIPMENT_RUNTIME"), target(f"behavior_pack/recipes/{a}.recipe.json", "ASHEN_ECONOMY"), target(f"resource_pack/textures/items/{a}.png", "ASHEN_PRESENTATION")], "normalization_evidence": normalization(index, "006", a), "implementation_gate": "KEEP_BASE_ONLY" if a == "briar_ring" else "PACKET006_ASSET_ECONOMY_AND_ROLE_WORK_PENDING"} for a, cat in EQUIPMENT]

    ratifications = {ticket: {"status": "RATIFIED_BY_DECISION_LEDGER_V3", "path": path, "sha256": sha, "proposal_bytes_preserved": True, "proposal": proposals[ticket]} for ticket, (path, sha) in PROPOSALS.items()}
    return {
        "schema": "aionbound.wave1.ashen_runtime_implementation_map.v2", "status": "RATIFIED_IMPLEMENTATION_OWNERSHIP_MAP_READY_WITH_ASSET_AND_PROOF_GAPS",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE, "g7_immutable": True, "g8_active_successor": True, "whisperwood_checkpoint_1_passed": True},
        "proof_boundary": {"bp_rp_edits": "NOT_PERFORMED", "build": "NOT_RUN", "bds": "NOT_RUN", "client": "NOT_RUN", "runtime_behavior": "NOT_PROVEN", "golden_promotion": "WITHHELD"},
        "authority": [{"path": p, "sha256": s} for p, s in AUTHORITY], "ratifications": ratifications, "classification_vocabulary": sorted(ALLOWED),
        "system_reconciliation": [
            {"system": "runtime_composition_and_router", "classification": "KEEP", "rule": "compose Ashen handlers; no early-return suppression"},
            {"system": "persistence_schema", "classification": "REFINE", "rule": "append idempotent AH discovery, encounter, entitlement, seal, and physical-claim state"},
            {"system": "runtime_budgets", "classification": "REFINE", "rule": "natural target remains 40; Ashen tuning is independent"},
            {"system": "legacy_g7_entity_cast", "classification": "SUPERSEDE", "rule": "Packet 002 identities own active Ashen ecology"},
            {"system": "natural_spawn_rules", "classification": "REPLACE", "rule": "nine natural Ashen roles; Ash Drake arena-only"},
            {"system": "structure_runtime_service", "classification": "KEEP", "rule": "retain bounded placement/claim architecture"},
            {"system": "loot_and_recipe_content", "classification": "REPLACE", "rule": "use W1-001-AH identities and select values only inside W1-004-AH intervals"},
            {"system": "codex_schema", "classification": "KEEP", "rule": "append indices; do not reorder existing state"},
            {"system": "codex_and_progression_content", "classification": "REPLACE", "rule": "bind AH discovery, CM rumor, and sole Ash Drake seal"},
            {"system": "equipment_framework", "classification": "REFINE", "rule": "base roles proceed; W1-CREATIVE-005 siblings remain deferred"},
            {"system": "kiln_sky_boss_shell_and_rewards", "classification": "REFINE", "rule": "implement exact W1-003/W1-004 envelopes; never transfer Whisperwood tuning"},
            {"system": "ashen_regrowth", "classification": "DEFER", "rule": "no Ashen regrowth authority; do not copy Whisperwood sapling semantics"},
        ],
        "authority_status": [
            {"id": "W1-001-AH", "blocking": False, "status": "READY_AS_RATIFIED", "scope": "20 aliases, Pack Cinder Mark narrative-only, drake_scale existing selected identity"},
            {"id": "W1-003-KILN-SKY", "blocking": False, "status": "READY_AS_RATIFIED", "scope": "exact encounter envelope; damage and radii remain explicit nondecisions"},
            {"id": "W1-004-AH", "blocking": False, "status": "READY_AS_RATIFIED", "scope": "closed loot intervals, sole seal, recovery, optional mastery semantics"},
            {"id": "W1-CREATIVE-005", "blocking": False, "status": "DEFER", "scope": "sidegrade siblings only; base vertical may proceed"},
        ],
        "asset_gates": {"representative_native_pass": sorted(NATIVE_PASS), "representative_pass_count": 7, "remaining_custom_geometry_native_repair": 23, "block_or_resource_blockbench_na_conditional": 20, "golden_and_client_visual_promotion": "WITHHELD", "implementation_rule": "bind passed representatives only after integrator adoption; repair each remaining custom asset before shipping use"},
        "worldgen_budget": {"classification": "REFINE", "global_natural_entities_target": 40, "global_structure_queue": 4, "global_structures_active": 1, "global_structure_blocks": 4096, "exact_spawn_weights": "ASHEN_ENGINEERING_TUNING_NOT_SELECTED", "cap_change": "NONE", "whisperwood_tuning_transfer": False},
        "boss_boundary": {"classification": "REFINE", "implementation_status": "READY_AS_RATIFIED", "encounter": p003["encounter_id"], "entity": p003["boss_entity_id"], "structure_link": p003["arena_link"], "arena_tag": p003["arena_vs_ecology_separation"]["arena_apex_tag"], "health": p003["health"], "phases": p003["phases"], "persistence": p003["persistence"], "terminal": p003["terminal_semantics"], "reward_resolution": p004["ashen_resolution"], "explicit_nondecisions": p003["explicit_nondecisions"], "whisperwood_tuning_transfer": False, "source_targets": [target("behavior_pack/scripts/kiln_sky.js", "ASHEN_BOSS_RUNTIME"), target("behavior_pack/scripts/ashen_rewards.js", "ASHEN_BOSS_RUNTIME"), target("behavior_pack/loot_tables/encounters/ashen/kiln_sky_materials.json", "ASHEN_ECONOMY")]},
        "codex_progression": {"classification": "REFINE", "entry_scope": ["10 creatures", "10 plants", "10 blocks", "10 resources", "10 structures", "14 equipment links", "Kiln Sky", "Ashen chapter", "Crystal Marsh rumor"], "hooks": ["WW Ashen rumor is invitation only", "AH discovery and acquisition", "burned camp CM rumor", "Kiln Sky terminal seal credit"], "sandbox_rule": "heat-resistant kit is soft transition; sole seal is arena Ash Drake horn credit"},
        "shared_target_ownership": [{"path": p, "owner": "PRIMARY_INTEGRATOR_ONLY"} for p in ["behavior_pack/scripts/catalog.js", "behavior_pack/scripts/runtime.js", "behavior_pack/scripts/state.js", "behavior_pack/scripts/wave1_codex_data.js", "behavior_pack/scripts/wave1_equipment_roles.js", "resource_pack/blocks.json", "resource_pack/textures/terrain_texture.json", "resource_pack/textures/item_texture.json", "resource_pack/texts/en_US.lang"]],
        "creatures": creatures, "plants": plants, "blocks": blocks, "resources": resources, "structures": structures, "equipment": equipment,
        "counts": {"creatures": 10, "plants": 10, "blocks": 10, "resources": 10, "structures": 10, "equipment_links": 14, "packet_002_assets": 50, "ratified_ashen_prose_terms": 22, "unratified_ashen_identity_terms": 0},
        "implementation_order": ["bind seven native representatives and repair remaining custom assets by class", "blocks/resources and bounded Ashen worldgen", "nine natural creature roles with W1-001/W1-004 economy", "ten authored structures and discovery", "Packet 006 base equipment roles", "Kiln Sky exact ratified session/persistence/reward envelope", "Codex/progression composition", "bounded Ashen vertical smoke when exit criteria are met"],
        "not_authorized_or_proven": ["BP/RP construction by this lane", "Ashen build", "Ashen BDS", "client animation/UI", "Golden promotion", "multiplayer", "console", "PS4", "Marketplace", "release"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("ASHEN_RUNTIME_IMPLEMENTATION_MAP.json"))
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
