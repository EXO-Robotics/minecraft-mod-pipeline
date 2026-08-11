#!/usr/bin/env python3
"""Build the deterministic, source-hash-bound Packet 003 authority intake map."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


BASE_COMMIT = "bcd65076900a3688dd797d54719263d88afd501c"
PACKET_REL = Path("program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-003-crystal-marsh")
EQUIPMENT_REL = Path("program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-006-equipment-progression")
CREATIVE_REL = Path("program/crazycraft-pack-production-v1/studio-prep/creative")

SOURCE_AUTHORITIES = [
    (PACKET_REL / "MANIFEST_FULL.json", "exact Packet 003 visual roster"),
    (PACKET_REL / "SPRINT_003_COMPLETE.md", "50/50 visual receipt, palette lock, source layout, and visual-only boundary"),
    (EQUIPMENT_REL / "MANIFEST_FULL.json", "Packet 006 roster for Crystal-facing equipment identity closure"),
    (CREATIVE_REL / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json", "machine-readable Packet 003 inventory, equipment links, and definition of done"),
    (CREATIVE_REL / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md", "human Packet 003 implementation relationships and Wave C contract"),
    (CREATIVE_REL / "01_progression/PLAYER_JOURNEY.md", "Crystal chapter order, soft gates, and Skyreach handoff"),
    (CREATIVE_REL / "02_loot/LOOT_CRYSTAL_MARSH.md", "binding loot identities and purposes; numeric envelopes remain deferred"),
    (CREATIVE_REL / "03_crafting/CRAFTING_TREE.md", "Crystal material, equipment, trophy, and cross-craft graph"),
    (CREATIVE_REL / "04_equipment/EQUIPMENT_PROGRESSION.md", "Crystal equipment roles, repair binder intent, and deferred sidegrade identity"),
    (CREATIVE_REL / "05_structures/STRUCTURES_DESIGN.md", "Crystal structure purpose, visit, loot identity, story, and progression"),
    (CREATIVE_REL / "06_world_gen/WORLD_GENERATION.md", "Crystal ecology, placement, rarity, and resource-node intent"),
    (CREATIVE_REL / "07_bosses/BOSS_PROGRESSION.md", "Pearl Depths identity, phase names, attacks, and reward identities only"),
    (CREATIVE_REL / "08_codex/CODEX_ENTRIES_CREATURES.md", "ten Crystal creature discovery, crafting, and hint entries"),
    (CREATIVE_REL / "08_codex/CODEX_DESIGN.md", "Codex schema, unlock rules, full-category coverage, and system links"),
]

CREATURES = {
    "prism_frog": ("ambient", ["shallows"], ["Prism Mucus", "Tiny Prism Chip", "Frog Song Stone"], ["crystal_talisman"]),
    "crystal_newt": ("ambient", ["banks"], ["wet_chitin", "Glass Algae Film", "Newt Tail Crystal"], ["crystal_circlet"]),
    "crystal_dragonfly": ("ambient_air", ["open marsh"], ["Prism Wing", "Iridescent Dust", "Dragonfly Pin"], ["prism_bow"]),
    "bloom_crab": ("neutral_pinch", ["shores"], ["wet_chitin", "Crab Pearl Grain", "Marsh Resin Blob", "Claw"], ["marsh_sickle", "crystal_talisman"]),
    "mire_turtle": ("neutral_tank", ["channels"], ["Mire Shell Plate", "silt_core", "Algae Scrap", "Turtle Breath Stone"], ["crystal_shovel"]),
    "glass_heron": ("neutral_rare", ["islets"], ["Glass Feather", "Long Beak Shard", "Heron Nest Token"], ["crystal_pike", "prism_bow"]),
    "reed_serpent": ("hostile", ["reeds"], ["crystal_reed_item", "Serpent Scale", "Venom Crystal", "Shed Skin Ribbon"], ["crystal_pike"]),
    "silt_crocodile": ("hostile_elite", ["deep channels"], ["Croc Hide", "Silt Fang", "silt_core", "Croc Eye Pearl"], ["explorer_cloak", "crystal_shovel"]),
    "bog_watcher": ("elite_ambush", ["fog"], ["Watcher Lens", "Flood Crystal Shard", "Bog Tendril", "Watcher Journal Scrap"], ["crystal_circlet", "surveyor_staff"]),
    "marsh_wight": ("chapter_apex", ["deep pool or sunken shrine encounter only"], ["Wight Shroud Cloth", "prism_pearl", "moon_pearl", "marsh_wight_mask", "flood_crystal", "crystal_root_item"], ["crystal_circlet", "explorer_cloak", "marsh_wight_mask"]),
}

RESOURCES = {
    "glass_algae": ("water or harvest", "C", ["polish", "food-risk", "algae_block", "prism_bow"], ["prism_bow"]),
    "marsh_resin": ("crabs or nodes", "C-U", ["wet bind", "Wet Plate", "sickle blank", "regional repair binder"], ["marsh_sickle", "marsh_idol"]),
    "crystal_reed_item": ("serpents or reeds", "U", ["Crystal Pole", "poles", "shafts"], ["crystal_pike"]),
    "crystal_root_item": ("nodes or marsh_wight", "U-R", ["Living Crystal Core", "living weapon cores"], ["crystal_circlet", "crystal_talisman"]),
    "wet_chitin": ("crystal_newt, bloom_crab, or fight", "U", ["Wet Plate", "sickle blank", "light armor", "circlet band"], ["marsh_sickle", "crystal_circlet"]),
    "silt_core": ("mire_turtle, silt_crocodile, or deep mud", "U-R", ["crystal_shovel head", "weight tools"], ["crystal_shovel"]),
    "flood_crystal": ("spikes or elites", "U-R", ["Crystal Pole", "weapon cores", "Twin Mineral Lens"], ["crystal_pike", "prism_bow", "surveyor_staff"]),
    "mire_bloom_item": ("plants", "U", ["dye", "consumable"], []),
    "moon_pearl": ("pools, silt_crocodile, or marsh_wight", "R", ["Living Crystal Core", "moon_pearl_pedestal", "hybrid staff ornaments"], ["crystal_circlet", "crystal_talisman", "moon_pearl_pedestal"]),
    "prism_pearl": ("marsh_wight or sunken_shrine", "R-E", ["top polish", "pilgrim catalyst"], ["crystal_circlet"]),
}

BLOCKS = {
    "marsh_soil": ("ground", "wet basin"),
    "wet_clay_block": ("shores or craft", "clay language"),
    "algae_block": ("water mats", "green wet"),
    "crystal_gravel": ("crystal shores", "mineral wet"),
    "crystal_stone": ("spikes or builds", "hard crystal"),
    "crystal_log": ("wet wood family", "flood trees"),
    "marsh_wood": ("wet wood family", "flood trees"),
    "flood_planks": ("builds or docks", "worked wet wood"),
    "glass_root_block": ("root crystal", "living mineral"),
    "prism_brick": ("ruins or obelisk pads", "civilization crystal"),
}

PLANTS = {
    "pearl_grass": ("islets", ["fiber", "pearl dust"]),
    "marsh_fern": ("banks", ["bandages wet"]),
    "flood_reed": ("reed seas", ["shafts", "thatch"]),
    "glass_moss": ("crystal shade", ["soft light"]),
    "glow_kelp": ("deep water", ["underwater light design"]),
    "bubble_pod": ("shallows", ["consumable", "buoyancy narrative"]),
    "crystal_lily": ("pools", ["moon_pearl catalyst helper"]),
    "crystal_vine": ("channels", ["wet rope"]),
    "mire_orchid": ("rare", ["curiosity perfume", "marsh_idol"]),
    "prism_bloom": ("crystal clearings", ["prism dust"]),
}

STRUCTURES = {
    "flooded_dock": ("uncommon shores", "CM entry", ["dock table", "tools", "rope", "reed", "marsh_sickle head"]),
    "ancient_boat": ("rare stranded", "Skyreach teaser", ["boat locker", "wet tools", "Skyreach map rare"]),
    "marsh_broken_bridge": ("channel spans", "mobility check", ["underwater cache", "wet_chitin", "pearls low"]),
    "pearl_cairn": ("uncommon islets", "soft CM rest", ["moon_pearl chance", "curiosities"]),
    "marsh_totem": ("uncommon", "marsh_idol craft home", ["marsh_idol path", "marsh_resin", "curiosities"]),
    "crystal_arch": ("landmark", "biome postcard", ["flood_crystal cache"]),
    "crystal_obelisk": ("rare network", "waystone analogue and circlet path", ["stamp", "crystal_talisman fragment", "small cache"]),
    "sunken_shrine": ("rare flooded", "pre-wight spiritual beat", ["prism_pearl", "marsh_idol component", "Drowned Choir Codex"]),
    "ruined_observatory": ("very rare height", "CM-to-Skyreach hard pointer", ["surveyor_staff lens", "trail maps", "star charts", "floating ruin sketches"]),
    "deep_pool_entrance": ("rare dark water", "apex approach", ["pearls", "silt_core", "marsh_wight tease"]),
}

DIRECT_EQUIPMENT = {
    "weapons": ["crystal_pike", "prism_bow"],
    "armor": ["crystal_circlet", "explorer_cloak"],
    "tools": ["crystal_shovel", "marsh_sickle"],
    "accessories": ["crystal_talisman", "marsh_idol"],
    "trophies": ["marsh_wight_mask", "moon_pearl_pedestal", "crystal_obelisk_fragment"],
}

EQUIPMENT_INPUTS = {
    "crystal_pike": ["crystal_reed_item", "flood_crystal", "glass_heron", "reed_serpent"],
    "prism_bow": ["crystal_dragonfly", "flood_crystal", "glass_algae", "glass_heron"],
    "crystal_circlet": ["crystal_root_item", "moon_pearl", "prism_pearl", "bog_watcher", "crystal_newt", "wet_chitin", "marsh_wight"],
    "explorer_cloak": ["silt_crocodile", "marsh_wight", "glass_algae"],
    "crystal_shovel": ["silt_core", "mire_turtle", "silt_crocodile", "flood_reed"],
    "marsh_sickle": ["wet_chitin", "marsh_resin", "bloom_crab", "flood_reed"],
    "crystal_talisman": ["prism_frog", "bloom_crab", "crystal_root_item", "moon_pearl", "crystal_obelisk"],
    "marsh_idol": ["marsh_totem", "mire_orchid", "marsh_resin", "sunken_shrine"],
    "marsh_wight_mask": ["marsh_wight"],
    "moon_pearl_pedestal": ["moon_pearl", "prism_brick", "sunken_shrine"],
    "crystal_obelisk_fragment": ["crystal_obelisk", "ruined_observatory"],
}

ADJACENT_EQUIPMENT = {
    "surveyor_staff": ["bog_watcher", "flood_crystal", "ruined_observatory"],
    "trail_compass": ["ruined_observatory"],
}

UNRESOLVED_TERMS = [
    "Prism Mucus", "Tiny Prism Chip", "Frog Song Stone", "Glass Algae Film", "Newt Tail Crystal",
    "Prism Wing", "Iridescent Dust", "Dragonfly Pin", "Crab Pearl Grain", "Marsh Resin Blob", "Claw",
    "Mire Shell Plate", "Algae Scrap", "Turtle Breath Stone", "Glass Feather", "Long Beak Shard",
    "Heron Nest Token", "Serpent Scale", "Venom Crystal", "Shed Skin Ribbon", "Croc Hide", "Silt Fang",
    "Croc Eye Pearl", "Watcher Lens", "Flood Crystal Shard", "Bog Tendril", "Watcher Journal Scrap",
    "Wight Shroud Cloth", "Crystal Pole", "Living Crystal Core", "Wet Plate", "sickle blank",
    "crystal_shovel head", "reed haft", "crystal edge", "bow limbs", "prism chips", "pearl grain",
    "totem wood", "CM polish", "marsh_sickle head", "crystal_talisman fragment", "marsh_idol component",
    "surveyor_staff lens", "Twin Mineral Lens", "Drowned Crown", "Gale-strung prism_bow",
]

MINIMUM_TICKETS = [
    {
        "id": "W1-001-CM",
        "owner": "CREATIVE_ASSET_SUPPORT",
        "blocking": "Crystal source-complete item, recipe, acquisition, and loot identity closure",
        "required_decisions": [
            "Classify every unresolved Crystal term as existing asset alias, derived component, new required item, intentionally removed/replaced, or narrative/Codex-only.",
            "Bind slash/alternative recipe language to exact accepted ingredients without creating identities.",
            "Bind the exact source identity for shrine rites, obelisk/talisman fragments, idol components, and observatory lenses.",
        ],
    },
    {
        "id": "W1-003-PEARL-DEPTHS",
        "owner": "CREATIVE_SUPPORT",
        "blocking": "Marsh Wight encounter, completion, persistence, and terminal reward implementation",
        "required_decisions": [
            "phase thresholds", "transition predicates", "telegraph/attack/recovery/cooldown ranges",
            "leash/timeout/wipe/reset/re-entry", "add caps", "multiplayer ownership/scaling",
            "late join/disconnect", "persistence domain", "reward authority",
            "idempotent terminal grant", "repeat-clear semantics",
        ],
    },
    {
        "id": "W1-004-CM",
        "owner": "CREATIVE_SUPPORT",
        "blocking": "Crystal creature, structure, apex, seal, and recovery numeric loot implementation",
        "required_decisions": [
            "C/U/R/E/T/Q probability ranges", "quantity ranges", "chest rolls",
            "guaranteed boss semantics", "arena reward guards", "alternate seal semantics",
            "once-per-player and full-inventory recovery semantics",
        ],
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def rel_source(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def source_files(root: Path, packet_root: Path, asset_id: str) -> dict:
    candidates = {
        "brief": packet_root / "assets/briefs" / f"{asset_id}.json",
        "editable_bbmodel": packet_root / "assets/editable" / f"{asset_id}.bbmodel",
        "editable_png": packet_root / "assets/editable" / f"{asset_id}.png",
        "export_geometry": packet_root / "assets/export/models" / f"{asset_id}.geo.json",
        "export_animation": packet_root / "assets/export/animations" / f"{asset_id}.animation.json",
        "export_texture": packet_root / "assets/export/textures" / f"{asset_id}.png",
    }
    result = {}
    for label, path in candidates.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        result[label] = {"path": rel_source(root, path), "sha256": sha256(path)}
    return result


def targets(category: str, asset_id: str) -> dict:
    shared = ["behavior_pack/scripts/catalog.js", "behavior_pack/scripts/codex.js", "resource_pack/texts/en_US.lang"]
    if category == "creatures":
        create = [
            f"behavior_pack/entities/{asset_id}.entity.json",
            f"behavior_pack/loot_tables/entities/{asset_id}.json",
            f"resource_pack/entity/{asset_id}.entity.json",
            f"resource_pack/models/aionbound/crystal_marsh/{asset_id}.geo.json",
            f"resource_pack/animations/aionbound/crystal_marsh/{asset_id}.animation.json",
            f"resource_pack/textures/aionbound/crystal_marsh/{asset_id}.png",
        ]
        if asset_id != "marsh_wight":
            create.append(f"behavior_pack/spawn_rules/{asset_id}.spawn_rules.json")
        return {"create": sorted(create), "update_shared": shared}
    if category == "resources":
        return {
            "create": [f"behavior_pack/items/{asset_id}.item.json", f"resource_pack/textures/aionbound/crystal_marsh/items/{asset_id}.png"],
            "update_shared": shared + ["resource_pack/textures/item_texture.json"],
        }
    if category in {"blocks", "plants"}:
        subdir = "plants" if category == "plants" else "blocks"
        return {
            "create": [
                f"behavior_pack/blocks/{asset_id}.block.json",
                f"behavior_pack/loot_tables/blocks/{asset_id}.json",
                f"resource_pack/textures/aionbound/crystal_marsh/{subdir}/{asset_id}.png",
            ],
            "update_shared": shared + ["resource_pack/blocks.json", "resource_pack/textures/terrain_texture.json"],
        }
    return {
        "create": [
            f"behavior_pack/blocks/{asset_id}.block.json",
            f"behavior_pack/structures/aionbound/{asset_id}.mcstructure",
            f"behavior_pack/features/{asset_id}.feature.json",
            f"behavior_pack/feature_rules/{asset_id}.feature_rule.json",
            f"resource_pack/models/aionbound/crystal_marsh/{asset_id}.geo.json",
            f"resource_pack/textures/aionbound/crystal_marsh/structures/{asset_id}.png",
        ],
        "update_shared": shared + ["behavior_pack/scripts/structures.js", "resource_pack/blocks.json", "resource_pack/textures/terrain_texture.json"],
    }


def equipment_targets(asset_id: str) -> dict:
    return {
        "create": [
            f"behavior_pack/items/{asset_id}.item.json",
            f"resource_pack/models/aionbound/equipment/{asset_id}.geo.json",
            f"resource_pack/animations/aionbound/equipment/{asset_id}.animation.json",
            f"resource_pack/textures/aionbound/equipment/{asset_id}.png",
        ],
        "update_shared": ["behavior_pack/scripts/catalog.js", "behavior_pack/scripts/codex.js", "resource_pack/textures/item_texture.json", "resource_pack/texts/en_US.lang"],
    }


def equipment_for(asset_id: str) -> list[str]:
    result = [equipment for equipment, inputs in {**EQUIPMENT_INPUTS, **ADJACENT_EQUIPMENT}.items() if asset_id in inputs]
    return sorted(result)


def asset_dependencies(category: str, asset_id: str) -> dict:
    if category == "creatures":
        role, acquisition, loot, direct = CREATURES[asset_id]
        return {"role": role, "acquisition": acquisition, "loot": loot, "crafting": [], "progression": direct}
    if category == "resources":
        acquisition, rarity, crafting, direct = RESOURCES[asset_id]
        return {"acquisition": [acquisition], "rarity": rarity, "loot": [], "crafting": crafting, "progression": direct}
    if category == "blocks":
        purpose, identity = BLOCKS[asset_id]
        return {"acquisition": ["not numerically specified"], "loot": [], "crafting": [], "progression": [purpose, identity]}
    if category == "plants":
        where, roles = PLANTS[asset_id]
        return {"acquisition": [where], "loot": [asset_id], "crafting": roles, "progression": roles}
    placement, role, loot = STRUCTURES[asset_id]
    return {"acquisition": [placement], "loot": loot, "crafting": [], "progression": [role]}


def classification(category: str, asset_id: str) -> dict:
    blockers = []
    if category in {"creatures", "structures"}:
        blockers.append("W1-004-CM")
    if category == "creatures" or any(term in UNRESOLVED_TERMS for term in asset_dependencies(category, asset_id).get("loot", [])):
        blockers.append("W1-001-CM")
    if asset_id == "marsh_wight":
        blockers.append("W1-003-PEARL-DEPTHS")
    blockers = sorted(set(blockers))
    return {
        "ready_now": [
            "warehouse and runtime identity normalization",
            "hash-bound visual source intake",
            "canonical target and dependency mapping",
            "Codex schema and nonnumeric relationship scaffolding",
            "nonnumeric ecology, placement, and role scaffolding",
        ],
        "blocked_until": blockers,
        "state": "STRUCTURAL_INTAKE_READY_RATIFICATION_BLOCKED" if blockers else "STRUCTURAL_INTAKE_READY",
        "native_roundtrip": "REQUIRED_BEFORE_SHIPPING_IF_HERO_OR_ROLE_SPECIFIC_ANIMATION; NOT_CLAIMED_BY_THIS_INTAKE",
    }


def build(root: Path, repo_root: Path) -> dict:
    packet_root = root / PACKET_REL
    equipment_root = root / EQUIPMENT_REL
    ledger_path = repo_root / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"
    manifest = json.loads((packet_root / "MANIFEST_FULL.json").read_text())
    equipment_manifest = json.loads((equipment_root / "MANIFEST_FULL.json").read_text())
    contract = json.loads((root / CREATIVE_REL / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json").read_text())
    ledger = json.loads(ledger_path.read_text())

    expected = {
        "creatures": list(CREATURES), "resources": list(RESOURCES), "blocks": list(BLOCKS),
        "plants": list(PLANTS), "structures": list(STRUCTURES),
    }
    tier_to_category = {"CREATURE": "creatures", "RESOURCE": "resources", "BLOCK": "blocks", "PLANT": "plants", "LANDMARK": "structures"}
    manifest_ids = {category: [] for category in expected}
    for entry in manifest["assets"]:
        manifest_ids[tier_to_category[entry["tier"]]].append(entry["name"])
    if manifest["count"] != 50 or not manifest["all_ok"]:
        raise AssertionError("Packet 003 manifest completion mismatch")
    for category, ids in expected.items():
        if set(ids) != set(manifest_ids[category]):
            raise AssertionError(f"Packet manifest {category} roster mismatch")

    contract_packet = contract["packets"]["003_crystal_marsh"]
    contract_ids = {
        "creatures": [x["id"] for x in contract_packet["creatures"]],
        "resources": [x["id"] for x in contract_packet["resources"]],
        "blocks": contract_packet["blocks"], "plants": contract_packet["plants"],
        "structures": [x["id"] for x in contract_packet["structures"]],
    }
    for category, ids in expected.items():
        if set(ids) != set(contract_ids[category]):
            raise AssertionError(f"Creative contract {category} roster mismatch")
    if contract_packet["equipment_links"] != DIRECT_EQUIPMENT:
        raise AssertionError("Packet 003 direct equipment links drifted")

    support_by_id = {ticket["id"]: ticket for ticket in ledger["support_tickets"]}
    expected_deferred = {
        "W1-CREATIVE-001": "WW_AND_AH_RATIFIED_CRYSTAL_SKY_DEFERRED",
        "W1-CREATIVE-003": "THORN_COURT_AND_KILN_SKY_RATIFIED_OTHER_BOSSES_DEFERRED",
        "W1-CREATIVE-004": "WHISPERWOOD_CHAPTER_1_AND_ASHEN_RATIFIED_CRYSTAL_SKY_DEFERRED",
        "W1-CREATIVE-005": "DEFERRED_BY_USER",
    }
    for ticket_id, state in expected_deferred.items():
        if support_by_id[ticket_id]["status"] != state:
            raise AssertionError(f"engineering ledger disposition drifted: {ticket_id}")

    assets = []
    for category, ids in expected.items():
        for asset_id in ids:
            dependencies = asset_dependencies(category, asset_id)
            dependencies["equipment"] = equipment_for(asset_id)
            dependencies["codex"] = {
                "coverage": "REQUIRED",
                "discovery": "observe/harvest/defeat/activate according to category and Creative Codex order",
                "relationship_links": sorted(set(dependencies.get("crafting", []) + dependencies.get("progression", []) + dependencies["equipment"])),
            }
            assets.append({
                "warehouse_id": asset_id,
                "runtime_id": f"aionbound:{asset_id}",
                "category": category,
                "source_files": source_files(root, packet_root, asset_id),
                "shipping_targets": targets(category, asset_id),
                "dependencies": dependencies,
                "classification": classification(category, asset_id),
            })

    equipment_manifest_ids = {entry["name"] for entry in equipment_manifest["assets"]}
    equipment = []
    for group, ids in DIRECT_EQUIPMENT.items():
        for asset_id in ids:
            if asset_id not in equipment_manifest_ids:
                raise AssertionError(f"Packet 006 identity missing: {asset_id}")
            equipment.append({
                "warehouse_id": asset_id,
                "runtime_id": f"aionbound:{asset_id}",
                "group": group,
                "source_files": source_files(root, equipment_root, asset_id),
                "shipping_targets": equipment_targets(asset_id),
                "inputs": EQUIPMENT_INPUTS[asset_id],
                "classification": "STRUCTURAL_LINK_READY_RECIPE_IDENTITY_OR_VALUES_MAY_REQUIRE_W1-001-CM_OR_W1-004-CM",
            })

    adjacent = []
    for asset_id, inputs in ADJACENT_EQUIPMENT.items():
        if asset_id not in equipment_manifest_ids:
            raise AssertionError(f"Packet 006 adjacent identity missing: {asset_id}")
        adjacent.append({
            "warehouse_id": asset_id,
            "runtime_id": f"aionbound:{asset_id}",
            "reason": "Creative structure/cross-craft reference; not part of contract Packet 003 direct equipment_links",
            "source_files": source_files(root, equipment_root, asset_id),
            "shipping_targets": equipment_targets(asset_id),
            "inputs": inputs,
        })

    source_authorities = []
    for rel, role in SOURCE_AUTHORITIES:
        path = root / rel
        source_authorities.append({"path": rel.as_posix(), "sha256": sha256(path), "role": role})
    source_authorities.append({
        "path": "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json",
        "sha256": sha256(ledger_path),
        "role": "current ratified/deferred engineering decision state",
    })

    result = {
        "schema": "aionbound.wave1.crystal-marsh-authority-intake.v1.0.0",
        "status": "PACKET_003_STRUCTURAL_AUTHORITY_READY_SOURCE_COMPLETE_RATIFICATION_REQUIRED",
        "base_commit": BASE_COMMIT,
        "scope": "Packet 003 authority intake only; no BP/RP mutation, runtime activation, qualification, or BDS claim",
        "source_authorities": source_authorities,
        "packet": {
            "id": "003", "name": "Crystal Marsh", "source_namespace": manifest["namespace"],
            "shipping_namespace": "aionbound", "count": 50,
            "category_counts": {key: 10 for key in expected},
            "visual_claim_boundary": "Visual production only. No Bedrock JSON, AI, or gameplay.",
            "definition_of_done": contract_packet["definition_of_done"],
        },
        "minimum_source_complete_ratifications": MINIMUM_TICKETS,
        "unresolved_terms": {
            "disposition_required_by": "W1-001-CM",
            "terms": UNRESOLVED_TERMS,
            "rule": "Do not promote, alias, derive, remove, or implement these as gameplay identities before exact ratification.",
        },
        "ratification_boundaries": {
            "W1-CREATIVE-005": {
                "status": "DEFERRED_BY_USER",
                "not_minimum_for_base_crystal_vertical": True,
                "blocked_scope": "Gale-strung prism_bow or any distinct sidegrade representation; base crystal_pike and prism_bow links remain structurally mappable.",
            },
            "ashen_runtime_activation": {
                "status": "MANAGED_REVIEWER_ACTIVATION_BLOCKED",
                "relationship": "FINAL_INTEGRATION_DEPENDENCY_ONLY",
                "crystal_dependency": False,
                "rule": "Crystal intake and vertical construction must not call dormant Ashen equipment-role or Kiln Sky services.",
            },
        },
        "safe_before_ratification": [
            "Normalize all 50 immutable warehouse identities from aionforge_cm to aionbound without redesigning visual identity.",
            "Bind and validate canonical Packet 003 briefs, editable sources, exports, paths, and SHA-256 values.",
            "Author schemas, registries, target maps, reference-closure scaffolding, Codex coverage, and nonnumeric relationship edges.",
            "Prepare nonnumeric entity role/AI, movement class, habitat, apex no-natural-spawn, and ecology scaffolding from Creative roles.",
            "Prepare block, plant, resource, and structure registrations and nonnumeric world-discovery placement scaffolding.",
            "Map Packet 006 direct equipment identities and exact Creative input edges without inventing unresolved ingredients or numeric recipes.",
            "Keep CM-to-Skyreach observatory/chart and downstream progression contracts structurally connected.",
        ],
        "withheld_before_ratification": [
            "Gameplay promotion or aliasing of unresolved nonwarehouse Crystal terms.",
            "Final creature/structure/apex loot probabilities, quantities, chest rolls, seal guards, or recovery semantics.",
            "Pearl Depths thresholds, timing, reset, multiplayer ownership/scaling, persistence, completion, or terminal grant semantics.",
            "Any W1-CREATIVE-005 sidegrade representation.",
            "Any substitute gameplay for dormant Ashen runtime services.",
            "Any source-complete, runtime-complete, checkpoint, candidate, BDS, client, console, or release claim.",
        ],
        "equipment_links": {
            "contract_direct": equipment,
            "adjacent_structure_or_crosscraft_references": adjacent,
        },
        "assets": assets,
        "counts": {
            "assets": len(assets),
            "by_category": {category: sum(1 for asset in assets if asset["category"] == category) for category in expected},
            "direct_packet006_links": len(equipment),
            "adjacent_packet006_links": len(adjacent),
            "unresolved_terms": len(UNRESOLVED_TERMS),
            "minimum_tickets": len(MINIMUM_TICKETS),
        },
    }
    digest_view = dict(result)
    result["authority_digest_sha256"] = hashlib.sha256(canonical_json_bytes(digest_view)).hexdigest()
    return result


def render_markdown(data: dict) -> str:
    lines = [
        "# Packet 003 Crystal Marsh — Engineering Authority Intake",
        "",
        f"**Status:** `{data['status']}`  ",
        f"**Base:** `{data['base_commit']}`  ",
        f"**Authority digest:** `{data['authority_digest_sha256']}`  ",
        "**Scope:** Authority intake only. No product-pack mutation or runtime proof is claimed.",
        "",
        "## Ratification boundary",
        "",
        "The exact 50-ID roster, visuals, roles, nonnumeric relationships, Packet 006 links, Codex coverage, and progression shape are available. Crystal cannot become source-complete until these minimum tranches are ratified:",
        "",
        "| Ticket | Blocks |",
        "|---|---|",
    ]
    for ticket in data["minimum_source_complete_ratifications"]:
        lines.append(f"| `{ticket['id']}` | {ticket['blocking']} |")
    lines += [
        "",
        "`W1-CREATIVE-005` remains deferred but is not a minimum blocker for the base Crystal vertical; it withholds only distinct sidegrade representation. The dormant Ashen services are a final-integration dependency only and are not a Crystal implementation dependency.",
        "",
        "## Safe before ratification",
        "",
    ] + [f"- {item}" for item in data["safe_before_ratification"]]
    lines += ["", "## Withheld", ""] + [f"- {item}" for item in data["withheld_before_ratification"]]
    lines += [
        "",
        "## Exact roster, dependencies, and readiness",
        "",
        "| Category | Warehouse ID | Acquisition / placement | Loot / harvest identity | Equipment links | State | Blockers |",
        "|---|---|---|---|---|---|---|",
    ]
    for asset in data["assets"]:
        dep = asset["dependencies"]
        lines.append(
            f"| {asset['category']} | `{asset['warehouse_id']}` | {'; '.join(dep.get('acquisition', []))} | "
            f"{'; '.join(dep.get('loot', [])) or 'none specified'} | {'; '.join(dep.get('equipment', [])) or 'none'} | "
            f"`{asset['classification']['state']}` | {', '.join(asset['classification']['blocked_until']) or 'none'} |"
        )
    lines += [
        "",
        "## Packet 006 Crystal-facing links",
        "",
        "| Group | ID | Bound Crystal inputs |",
        "|---|---|---|",
    ]
    for equipment in data["equipment_links"]["contract_direct"]:
        lines.append(f"| {equipment['group']} | `{equipment['warehouse_id']}` | {', '.join(equipment['inputs'])} |")
    lines += [
        "",
        "Adjacent, non-subset references: `surveyor_staff` from Watcher/flood-crystal/observatory relationships and `trail_compass` from observatory maps. They are not counted among the 11 direct Packet 003 equipment links.",
        "",
        "## Unresolved Crystal terms",
        "",
        "The following terms require exact `W1-001-CM` disposition; no alias or item identity is inferred:",
        "",
        ", ".join(f"`{term}`" for term in data["unresolved_terms"]["terms"]),
        "",
        "## Narrow support tickets",
        "",
    ]
    for ticket in data["minimum_source_complete_ratifications"]:
        lines += [f"### {ticket['id']}", "", f"Blocks: {ticket['blocking']}", ""]
        lines += [f"- {item}" for item in ticket["required_decisions"]]
        lines.append("")
    lines += [
        "## Canonical source and target proof boundary",
        "",
        "Every Packet 003 asset and direct Packet 006 link records six canonical source/export paths and SHA-256 values in the machine twin. Shipping targets are planning destinations only; their existence or validation is not claimed here.",
        "",
        "## Source bindings",
        "",
        "| Source | SHA-256 | Role |",
        "|---|---|---|",
    ]
    for source in data["source_authorities"]:
        lines.append(f"| `{source['path']}` | `{source['sha256']}` | {source['role']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bedrock-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    data = build(args.bedrock_root.resolve(), args.repo_root.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.json").write_bytes(json.dumps(data, indent=2, ensure_ascii=False).encode() + b"\n")
    (args.output_dir / "CRYSTAL_MARSH_VERTICAL_INTAKE_MAP.md").write_text(render_markdown(data))


if __name__ == "__main__":
    main()
