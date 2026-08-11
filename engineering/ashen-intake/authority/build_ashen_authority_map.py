#!/usr/bin/env python3
"""Build the deterministic, source-hash-bound Packet 002 intake authority map."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


BASE_COMMIT = "9acf1b0f62ade90b59ba65e0a9e0618852ff3159"
PACKET_REL = Path("program/crazycraft-pack-production-v1/studio-prep/sprints/asset-sprint-002-ashen-highlands")
CREATIVE_REL = Path("program/crazycraft-pack-production-v1/studio-prep/creative")
ASHEN_PROPOSAL_REL = Path("engineering/authority/support-proposals/ashen")

SOURCE_AUTHORITIES = [
    (PACKET_REL / "MANIFEST_FULL.json", "exact Packet 002 visual roster and visual-only claim boundary"),
    (PACKET_REL / "SPRINT_002_COMPLETE.md", "50/50 category receipt and canonical source layout"),
    (CREATIVE_REL / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json", "machine-readable Packet 002 inventory and completion contract"),
    (CREATIVE_REL / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md", "human implementation authority and per-asset relationships"),
    (CREATIVE_REL / "01_progression/PLAYER_JOURNEY.md", "chapter order and soft-gate progression"),
    (CREATIVE_REL / "02_loot/LOOT_ASHEN.md", "loot identities and purposes, with values bounded by ratified W1-004-AH"),
    (CREATIVE_REL / "03_crafting/CRAFTING_TREE.md", "material-to-component-to-equipment graph"),
    (CREATIVE_REL / "04_equipment/EQUIPMENT_PROGRESSION.md", "equipment roles and sidegrade philosophy"),
    (CREATIVE_REL / "05_structures/STRUCTURES_DESIGN.md", "structure purpose, visit, loot identity, story, and progression"),
    (CREATIVE_REL / "06_world_gen/WORLD_GENERATION.md", "ecology, placement, and rarity intent"),
    (CREATIVE_REL / "07_bosses/BOSS_PROGRESSION.md", "Kiln Sky identity, phase kit, attacks, and reward identities"),
    (CREATIVE_REL / "08_codex/CODEX_ENTRIES_CREATURES.md", "ten creature discovery/crafting/hint entries"),
    (ASHEN_PROPOSAL_REL / "W1-001-AH.json", "ratified refined Ashen identity dispositions"),
    (ASHEN_PROPOSAL_REL / "W1-003-KILN-SKY.json", "ratified refined Kiln Sky encounter envelope"),
    (ASHEN_PROPOSAL_REL / "W1-004-AH.json", "ratified refined Ashen loot and reward envelope"),
]

CREATURES = {
    "ash_mite": {
        "role": "swarm_hostile", "acquisition": ["vents", "caves"],
        "loot": ["Ash Dust", "Mite Mandible", "ember_resin", "Swarm Queen Scale"],
        "crafting": ["forge flux", "ore_chisel", "heat binding", "ashen_boots"],
        "codex_discovery": "swarm contact", "progression": ["heatstone locator hint", "hazard economy"],
    },
    "ember_crow": {
        "role": "ambient_air", "acquisition": ["sky", "towers"],
        "loot": ["Char Feather", "Cinder Beak", "Scorched Message Tube"],
        "crafting": ["ash_repeater fletching", "small tool tips", "Codex traveler notes"],
        "codex_discovery": "observe sky", "progression": ["ash_repeater path", "cooled-kill discovery hint"],
    },
    "magma_lizard": {
        "role": "small_hostile", "acquisition": ["hot rock"],
        "loot": ["Heat Scale", "volcanic_glass_shard", "Warm Blood Vial"],
        "crafting": ["ashen_legs padding", "edges and panes", "heat-resist precursor"],
        "codex_discovery": "defeat on basalt", "progression": ["safe-path environmental hint", "ranged and tool path"],
    },
    "furnace_beetle": {
        "role": "hostile", "acquisition": ["forge-language areas"],
        "loot": ["furnace_chitin", "Smolder Gland", "Beetle Core Fragment"],
        "crafting": ["ashen_chest plates", "ember_totem fuel", "basalt_hammer face inlay"],
        "codex_discovery": "defeat", "progression": ["ashen armor set", "ember accessory path"],
    },
    "char_wolf": {
        "role": "hostile_pack", "acquisition": ["night ash"],
        "loot": ["Char Pelt", "Ember Fang", "Pack Cinder Mark"],
        "crafting": ["ashen lining", "dagger or axe teeth", "Codex pack record"],
        "codex_discovery": "pack fight", "progression": ["AH hostile ecology", "tower story link"],
    },
    "cinder_lynx": {
        "role": "elite_hunter", "acquisition": ["ridges"],
        "loot": ["Cinder Pelt", "Lynx Claw", "heatstone", "Lynx Eye Gem"],
        "crafting": ["silent boot pads", "ash_repeater mechanism", "heatstone path", "talisman curiosity"],
        "codex_discovery": "elite hunt", "progression": ["ash_repeater path", "elite heatstone source"],
    },
    "ash_ram": {
        "role": "neutral_territorial", "acquisition": ["plateaus"],
        "loot": ["basalt_core", "Ash Wool", "Ram Horn Curve"],
        "crafting": ["basalt_hammer haft ring", "armor padding", "trophy mount or helmet crest"],
        "codex_discovery": "territorial clash", "progression": ["basalt force path"],
    },
    "soot_stag": {
        "role": "neutral_rare", "acquisition": ["high plateaus"],
        "loot": ["Soot Antler", "Char Hide", "fire_bloom_seed", "Stag Heart Cinder"],
        "crafting": ["staff or hammer ornament", "armor", "planting", "ember_great_axe catalyst"],
        "codex_discovery": "rare plateau sighting", "progression": ["ember_great_axe path", "fire_bloom path"],
    },
    "basalt_tortoise": {
        "role": "tank_neutral", "acquisition": ["basalt fields"],
        "loot": ["basalt_core", "Shell Plate", "Slow Stone"],
        "crafting": ["heavy weapons and tools", "ashen chest or shield-analogue plate", "Codex geology"],
        "codex_discovery": "patient engagement", "progression": ["force path", "heavy weapon origin"],
    },
    "ash_drake": {
        "role": "chapter_apex", "acquisition": ["arena or nest sky", "ember_forge encounter link"],
        "loot": ["Drake Scale", "Ember Sinew", "volcanic_glass_shard", "ash_drake_horn", "heatstone", "ember_resin", "ember_forge_core"],
        "crafting": ["ashen set finish", "ember_great_axe binding", "bulk glass", "chapter seal", "forge materials"],
        "codex_discovery": "apex victory", "progression": ["Chapter 2 seal", "CM maps unlock harder", "Pilgrim assembly"],
    },
}

RESOURCES = {
    "smolder_bark": ("ash logs or harvest", "C", ["char_planks", "heat-safe handles"], "AH wood language"),
    "charbone": ("creatures or ash fields", "C-U", ["tool spines", "ore_chisel", "grim inlays"], "grim craft"),
    "sulfur_cluster": ("crust nodes", "U", ["flux", "heat crafts"], "hazard economy"),
    "volcanic_glass_shard": ("cooled flows or magma_lizard", "U", ["edges", "tips", "ash_repeater"], "ranged and tool path"),
    "ember_resin": ("beetles or nodes", "U-R", ["Ember Heart", "ember_great_axe", "ember_totem", "regional repair binder"], "ember path"),
    "heatstone": ("vents or elites", "U-R", ["Heat Core", "basalt_pick", "ember_hammer"], "tool path"),
    "furnace_chitin": ("furnace_beetle", "U-R", ["Chitin Plate", "ashen armor", "ore_chisel tip"], "set path"),
    "basalt_core": ("basalt_tortoise, deep stone, or basalt_arch cache", "R", ["Heavy Head", "basalt_hammer", "basalt_pick", "Trophy Edge catalyst bundle"], "force path and Pilgrim assembly"),
    "ash_crystal": ("rare nodes or ash_watchtower", "R", ["Twin Mineral Lens with flood_crystal"], "Crystal Marsh bridge hybrid"),
    "fire_bloom_seed": ("fire_bloom or soot_stag", "U", ["planting", "consumable", "heat salve"], "heat salve path"),
}

BLOCKS = {
    "ash_log": ("dead heat wood", ["char_planks"], "char forest"),
    "char_planks": ("worked ash wood", ["builds", "handles", "furniture", "ash_repeater stock"], "worked ash"),
    "ash_soil": ("ground cover", ["terrain"], "ash fields"),
    "cinder_gravel": ("paths and hazards", ["terrain"], "cinder waste"),
    "smolder_stone": ("stone body", ["builds"], "hot stone"),
    "basalt_brick": ("structures", ["kiln pads", "forge pads", "bridge repair"], "civilization"),
    "basalt_pillar": ("landmarks", ["massing"], "vertical basalt"),
    "heat_bark": ("accent", ["detail"], "heat bark"),
    "ember_moss": ("hazard or accent flora block", ["detail"], "living heat"),
    "volcanic_glass_block": ("luxury and windows", ["glass builds"], "cooled fire"),
}

PLANTS = {
    "cinder_grass": ("fields", "fiber and tinder", ["early AH craft"]),
    "ash_fern": ("ash understory", "bandage under ash", ["soft materials"]),
    "smoke_reed": ("near vents", "arrow or repeater shafts", ["ash_repeater"]),
    "char_shrub": ("scrub", "fuel", ["camp craft"]),
    "soot_mushroom": ("shade ash", "risky food", ["consumable"]),
    "magma_moss": ("hot rock", "heat dye or resist salve", ["heat resist path"]),
    "glow_root": ("caves", "cave light", ["cave navigation"]),
    "basalt_flower": ("rare stone", "rare catalyst", ["rare craft"]),
    "ember_vine": ("cliffs and heat", "heat rope", ["binding"]),
    "fire_bloom": ("flower patches", "consumable and seed", ["fire_bloom_seed"]),
}

STRUCTURES = {
    "fire_totem": ("uncommon clusters", ["ember_resin", "sulfur_cluster", "First Fire prayer strip"], ["ember_totem path", "ambient AH"]),
    "burned_camp": ("uncommon edges", ["charred tools", "Char Pelt", "CM teaser map", "ashen_boots pattern scraps"], ["AH onboarding", "CM rumor"]),
    "char_wagon": ("uncommon routes", ["trade slag", "sulfur_cluster", "volcanic_glass_shard", "ash_repeater stock wood"], ["mid-AH economy", "CM map reward identity"]),
    "broken_bridge": ("ravine-gated", ["basalt_brick", "char_planks", "volcanic_glass_shard", "furnace_chitin"], ["traversal or gear check"]),
    "basalt_arch": ("rare landmark", ["basalt_core chance"], ["route spoiler toward nest or forge"]),
    "ash_watchtower": ("rare ridges", ["survey notes", "trail_compass calibration", "ash_crystal"], ["long-sight Codex stamp", "drake watch"]),
    "ancient_kiln": ("rare", ["slag", "heatstone", "ember_forge_core rare", "unfinished basalt tool heads"], ["pre-boss forge language"]),
    "ember_forge": ("very rare goal; design says one per highlands realm", ["slag", "heatstone", "ember_forge_core", "unfinished basalt tool heads"], ["primary AH structure goal", "Ash Drake co-requisite"]),
    "lava_shrine": ("rare vents", ["ritual curios", "ember_totem component"], ["accessory and heat-ward story"]),
    "ash_cave": ("uncommon faces", ["heatstone veins", "ash_mite nests", "basalt_core rare"], ["mid-late AH", "Drake juvenile tease"]),
}

EQUIPMENT_LINKS = {
    "weapons": ["basalt_hammer", "ember_great_axe", "ash_repeater"],
    "armor": ["ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots"],
    "tools": ["basalt_pick", "ember_hammer", "ore_chisel"],
    "accessories": ["ember_totem", "briar_ring"],
    "trophies": ["ash_drake_horn", "ember_forge_core"],
}

EQUIPMENT_BY_ASSET = {
    "ash_mite": ["ore_chisel", "ashen_boots"],
    "ember_crow": ["ash_repeater"],
    "magma_lizard": ["ashen_legs", "ash_repeater"],
    "furnace_beetle": ["ashen_chest", "ember_totem", "basalt_hammer", "ore_chisel"],
    "char_wolf": ["ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots"],
    "cinder_lynx": ["ashen_boots", "ash_repeater"],
    "ash_ram": ["basalt_hammer"],
    "soot_stag": ["ember_great_axe"],
    "basalt_tortoise": ["basalt_hammer", "basalt_pick", "ashen_chest"],
    "ash_drake": ["ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots", "ember_great_axe", "ash_drake_horn"],
    "smolder_bark": ["basalt_hammer", "basalt_pick", "ash_repeater"],
    "charbone": ["ember_hammer", "ore_chisel"],
    "volcanic_glass_shard": ["basalt_hammer", "basalt_pick", "ash_repeater"],
    "ember_resin": ["ember_great_axe", "ember_hammer", "ember_totem", "ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots"],
    "heatstone": ["basalt_pick", "ember_hammer"],
    "furnace_chitin": ["ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots", "ore_chisel"],
    "basalt_core": ["basalt_hammer", "basalt_pick", "ashen_helmet", "ashen_chest", "ashen_legs", "ashen_boots"],
    "char_planks": ["basalt_hammer", "basalt_pick", "ash_repeater"],
    "smoke_reed": ["ash_repeater"],
    "fire_totem": ["ember_totem"],
    "burned_camp": ["ashen_boots"],
    "char_wagon": ["ash_repeater"],
    "ash_watchtower": ["trail_compass"],
    "ancient_kiln": ["ember_forge_core", "basalt_hammer", "basalt_pick"],
    "ember_forge": ["ember_forge_core", "basalt_hammer", "basalt_pick", "ember_hammer", "ore_chisel"],
    "lava_shrine": ["ember_totem"],
}

ASHEN_UNRESOLVED_TERMS = [
    "Ash Dust", "Ash Wool", "Beetle Core Fragment", "Char Feather", "Char Hide", "Char Pelt",
    "Cinder Beak", "Cinder Pelt", "Drake Scale", "Ember Fang", "Ember Sinew", "Heat Scale",
    "Lynx Claw", "Mite Mandible", "Pack Cinder Mark", "Ram Horn Curve", "Shell Plate",
    "Smolder Gland", "Soot Antler", "Stag Heart Cinder", "Swarm Queen Scale", "Warm Blood Vial",
]

RATIFIED_DERIVED = {
    "Heat Core": "aionbound:heat_core",
    "Heavy Head": "aionbound:heavy_head",
    "Chitin Plate": "aionbound:chitin_plate",
    "Ember Heart": "aionbound:ember_heart",
}

RATIFIED_ALIASES = {"mite_resin language": "aionbound:ember_resin"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def source_files(packet_root: Path, asset_id: str) -> dict:
    candidates = {
        "brief": packet_root / "assets" / "briefs" / f"{asset_id}.json",
        "editable_bbmodel": packet_root / "assets" / "editable" / f"{asset_id}.bbmodel",
        "editable_png": packet_root / "assets" / "editable" / f"{asset_id}.png",
        "export_geometry": packet_root / "assets" / "export" / "models" / f"{asset_id}.geo.json",
        "export_animation": packet_root / "assets" / "export" / "animations" / f"{asset_id}.animation.json",
        "export_texture": packet_root / "assets" / "export" / "textures" / f"{asset_id}.png",
    }
    result = {}
    for label, path in candidates.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        result[label] = {"path": path.as_posix().split("/bedrock-server/", 1)[-1], "sha256": sha256(path)}
    return result


def targets(category: str, asset_id: str) -> dict:
    shared = ["behavior_pack/scripts/catalog.js", "behavior_pack/scripts/codex.js", "resource_pack/texts/en_US.lang"]
    if category == "creatures":
        create = [
            f"behavior_pack/entities/{asset_id}.entity.json",
            f"behavior_pack/loot_tables/entities/{asset_id}.json",
            f"resource_pack/entity/{asset_id}.entity.json",
            f"resource_pack/models/aionbound/ashen_highlands/{asset_id}.geo.json",
            f"resource_pack/animations/aionbound/ashen_highlands/{asset_id}.animation.json",
            f"resource_pack/textures/aionbound/ashen_highlands/{asset_id}.png",
        ]
        if asset_id != "ash_drake":
            create.append(f"behavior_pack/spawn_rules/{asset_id}.spawn_rules.json")
        return {"create": sorted(create), "update_shared": shared}
    if category == "resources":
        return {
            "create": [f"behavior_pack/items/{asset_id}.item.json", f"resource_pack/textures/aionbound/ashen_highlands/items/{asset_id}.png"],
            "update_shared": shared + ["resource_pack/textures/item_texture.json"],
        }
    if category in {"blocks", "plants"}:
        subdir = "plants" if category == "plants" else "blocks"
        return {
            "create": [
                f"behavior_pack/blocks/{asset_id}.block.json",
                f"behavior_pack/loot_tables/blocks/{asset_id}.json",
                f"resource_pack/textures/aionbound/ashen_highlands/{subdir}/{asset_id}.png",
            ],
            "update_shared": shared + ["resource_pack/blocks.json", "resource_pack/textures/terrain_texture.json"],
        }
    return {
        "create": [
            f"behavior_pack/blocks/{asset_id}.block.json",
            f"behavior_pack/structures/aionbound/{asset_id}.mcstructure",
            f"behavior_pack/features/{asset_id}.feature.json",
            f"behavior_pack/feature_rules/{asset_id}.feature_rule.json",
            f"resource_pack/models/aionbound/ashen_highlands/{asset_id}.geo.json",
            f"resource_pack/textures/aionbound/ashen_highlands/structures/{asset_id}.png",
        ],
        "update_shared": shared + ["behavior_pack/scripts/structures.js", "resource_pack/blocks.json", "resource_pack/textures/terrain_texture.json"],
    }


def build(root: Path, ledger_path: Path) -> dict:
    packet_root = root / PACKET_REL
    manifest = json.loads((packet_root / "MANIFEST_FULL.json").read_text())
    contract = json.loads((root / CREATIVE_REL / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json").read_text())
    ledger = json.loads(ledger_path.read_text())
    approved = {row["tranche"]: row for row in ledger["ratifications"]["approved"]}
    required_ashen = {"W1-001-AH", "W1-003-KILN-SKY", "W1-004-AH"}
    if not required_ashen <= approved.keys():
        raise AssertionError("Ashen ratification missing from replacement ledger")
    for tranche in required_ashen:
        proposal_path = ledger_path.parents[2] / approved[tranche]["proposal"]
        if sha256(proposal_path) != approved[tranche]["proposal_sha256"]:
            raise AssertionError(f"ratified proposal drift: {tranche}")

    expected = {
        "creatures": list(CREATURES), "resources": list(RESOURCES), "blocks": list(BLOCKS),
        "plants": list(PLANTS), "structures": list(STRUCTURES),
    }
    manifest_by_tier = {}
    tier_to_category = {"CREATURE": "creatures", "RESOURCE": "resources", "BLOCK": "blocks", "PLANT": "plants", "LANDMARK": "structures"}
    for entry in manifest["assets"]:
        manifest_by_tier.setdefault(tier_to_category[entry["tier"]], []).append(entry["name"])
    for category, ids in expected.items():
        if set(ids) != set(manifest_by_tier.get(category, [])):
            raise AssertionError(f"{category} roster mismatch")
    if manifest["count"] != 50 or not manifest["all_ok"] or manifest["claims_boundary"] != "Visual production only.":
        raise AssertionError("Packet manifest boundary mismatch")

    contract_packet = contract["packets"]["002_ashen_highlands"]
    contract_ids = {
        "creatures": [x["id"] for x in contract_packet["creatures"]],
        "resources": [x["id"] for x in contract_packet["resources"]],
        "blocks": contract_packet["blocks"], "plants": contract_packet["plants"],
        "structures": [x["id"] for x in contract_packet["structures"]],
    }
    for category, ids in expected.items():
        if set(ids) != set(contract_ids[category]):
            raise AssertionError(f"contract {category} roster mismatch")

    assets = []
    for category, ids in expected.items():
        for asset_id in ids:
            if category == "creatures":
                dependencies = CREATURES[asset_id]
            elif category == "resources":
                acquisition, rarity, crafting, progression = RESOURCES[asset_id]
                dependencies = {"acquisition": [acquisition], "rarity": rarity, "loot": [], "crafting": crafting, "codex_discovery": "first obtain", "progression": [progression]}
            elif category == "blocks":
                purpose, crafting, identity = BLOCKS[asset_id]
                dependencies = {"acquisition": ["craft or natural terrain as Creative specifies"], "loot": [], "crafting": crafting, "codex_discovery": "first encounter or obtain", "progression": [purpose, identity]}
            elif category == "plants":
                where, purpose, crafting = PLANTS[asset_id]
                dependencies = {"acquisition": [where], "loot": [asset_id], "crafting": crafting, "codex_discovery": "first harvest", "progression": [purpose]}
            else:
                placement, loot, progression = STRUCTURES[asset_id]
                dependencies = {"acquisition": [placement], "loot": loot, "crafting": [], "codex_discovery": "structure visit or activation", "progression": progression}
            dependencies["equipment"] = EQUIPMENT_BY_ASSET.get(asset_id, [])
            dependencies["codex"] = {
                "coverage": "REQUIRED",
                "discovery": dependencies.pop("codex_discovery"),
                "relationship_links": sorted(set(dependencies.get("crafting", []) + dependencies.get("progression", []) + dependencies["equipment"])),
            }
            assets.append({
                "warehouse_id": asset_id,
                "runtime_id": f"aionbound:{asset_id}",
                "category": category,
                "source_files": source_files(packet_root, asset_id),
                "shipping_targets": targets(category, asset_id),
                "dependencies": dependencies,
                "authority_state": {
                    "identity": "RATIFIED_WAREHOUSE_ID",
                    "visual": "HASH_BOUND_PACKET_002_VISUAL_SOURCE",
                    "gameplay_relationships": "BINDING_CREATIVE_IDENTITY_AND_ROLE",
                    "numeric_loot_values": "RATIFIED_W1_004_AH_EXACT_REFINED_ENVELOPES",
                    "new_nonwarehouse_item_dependencies": "RATIFIED_W1_001_AH_EXACT_DISPOSITIONS",
                    "sidegrade_identity": "WITHHELD_W1_CREATIVE_005" if asset_id in {"basalt_core", "volcanic_glass_shard", "ember_resin", "ash_crystal"} else "NOT_APPLICABLE_OR_NO_SIDEGRADE_DECISION_HERE",
                },
            })

    result = {
        "schema": "aionbound.wave1.ashen-authority-intake.v2.0.0",
        "status": "PACKET_002_AUTHORITY_RATIFIED_IMPLEMENTATION_AUTHORIZED",
        "base_commit": BASE_COMMIT,
        "scope": "Packet 002 authority intake only; no BP/RP implementation or qualification claim",
        "source_authorities": [
            {"path": rel.as_posix(), "sha256": sha256((ledger_path.parents[2] if rel.parts[0] == "engineering" else root) / rel), "role": role}
            for rel, role in SOURCE_AUTHORITIES
        ] + [{"path": "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json", "sha256": sha256(ledger_path), "role": "ratified and deferred engineering decision state"}],
        "packet": {
            "id": "002", "name": "Ashen Highlands", "source_namespace": manifest["namespace"],
            "shipping_namespace": "aionbound", "count": 50,
            "category_counts": {key: 10 for key in expected},
            "visual_claim_boundary": manifest["claims_boundary"],
            "definition_of_done": contract_packet["definition_of_done"],
        },
        "ratified_terms": {
            "warehouse_runtime_rule": "aionbound:<immutable_warehouse_id>",
            "aliases": RATIFIED_ALIASES,
            "derived_components": RATIFIED_DERIVED,
            "equipment_links": EQUIPMENT_LINKS,
            "loot_identity_and_purpose": "Creative LOOT_ASHEN identities and purposes are binding; implementation values must remain inside W1-004-AH.",
            "kiln_sky_nonnumeric_kit": {
                "boss": "aionbound:ash_drake", "arena_link": "aionbound:ember_forge",
                "phases": ["Ash Landing", "Vent Choir", "Glass Wing", "Kiln Heart"],
                "attacks": ["Cinder Breath", "Tail Slag", "Thermal Dive", "Mite Shake", "Basalt Quake", "Glass Feather Storm"],
                "reward_identities": ["aionbound:ash_drake_horn", "forge materials", "aionbound:ember_forge_core chance"],
            },
            "ashen_identity_authority": "W1-001-AH_APPROVED_EXACT_REFINED_BYTES",
            "kiln_sky_authority": "W1-003-KILN-SKY_APPROVED_EXACT_REFINED_BYTES",
            "ashen_loot_reward_authority": "W1-004-AH_APPROVED_EXACT_REFINED_BYTES",
        },
        "unresolved_terms": {
            "W1-CREATIVE-001_CRYSTAL_SKY": {"status": "DEFERRED_UNTIL_SEPARATE_RATIFICATION"},
            "curiosities_default": {"status": "NARRATIVE_CODEX_ONLY_UNLESS_PROMOTED", "terms": ["Scorched Message Tube", "Lynx Eye Gem", "Slow Stone", "First Fire prayer strip", "survey notes", "ritual curios", "CM teaser map", "ashen_boots pattern scraps", "unfinished basalt tool heads"]},
            "W1-CREATIVE-003_OTHER_BOSSES": {"status": "DEFERRED_EXCLUDING_RATIFIED_THORN_COURT_AND_KILN_SKY", "missing": ledger["boss_behavior"]["required_ticket_fields"]},
            "W1-CREATIVE-004_CRYSTAL_SKY": {"status": "DEFERRED", "missing": ledger["loot"]["required_ticket_fields"]},
            "W1-CREATIVE-005": {"status": "DEFERRED_BY_USER", "scope": "equipment sidegrade item identity", "rule": "No sibling ID, NBT/lore identity, or sidegrade implementation may be selected here."},
            "additional_unbound_recipe_language": ["fire_totem ash", "glass tip", "heat wrap", "char handle", "char stock", "chitin tip", "basalt studs", "ember_resin vents", "Firestitched Cord", "heatstone dust"],
        },
        "safe_now_withheld": {
            "safe_now": [
                "Normalize all 50 source identities from aionforge_ah to aionbound without changing visual identity.",
                "Copy hash-bound source/export bytes into the canonical shipping target families.",
                "Author schema and reference-closure scaffolding for the 50 ratified warehouse IDs.",
                "Bind Creative-approved acquisition sources, roles, Codex relationships, progression relationships, and equipment dependency edges without inventing values or identities.",
                "Implement Kiln Sky exactly inside the ratified W1-003-KILN-SKY behavior, ownership, persistence, reset, and terminal envelope.",
                "Implement Ashen loot, recipes, reward guards, and recovery exactly inside W1-001-AH and W1-004-AH.",
                "Use Packet 006 equipment IDs as dependency targets without choosing sidegrade representation.",
            ],
            "withheld": [
                "Any identity or numeric value outside the exact refined Ashen proposals.",
                "Any gameplay item for curiosity prose unless separately promoted.",
                "Kiln Sky damage values, attack-effect radii, or arena-radius numbers not created by the refined proposal.",
                "Any claim that ash_drake naturally spawns; Creative binds it to an arena or nest-sky apex path.",
                "Any sidegrade identity or representation covered by deferred W1-CREATIVE-005.",
                "Checkpoint, candidate, BDS, client, console, or gameplay proof from this intake map.",
            ],
        },
        "assets": assets,
        "counts": {"assets": len(assets), "by_category": {category: sum(1 for a in assets if a["category"] == category) for category in expected}},
    }
    digest_view = dict(result)
    result["authority_digest_sha256"] = hashlib.sha256(canonical_json_bytes(digest_view)).hexdigest()
    return result


def render_markdown(data: dict) -> str:
    lines = [
        "# Packet 002 Ashen Highlands — Engineering Authority Intake",
        "",
        f"**Status:** `{data['status']}`",
        f"**Base:** `{data['base_commit']}`",
        f"**Authority digest:** `{data['authority_digest_sha256']}`",
        "**Scope:** Authority intake only. This does not implement BP/RP content or prove runtime behavior.",
        "",
        "## Locked boundaries",
        "",
        "- All 50 Packet 002 warehouse identities normalize to `aionbound:<warehouse_id>`.",
        "- Packet 002 art is visual-production evidence only.",
        "- Exact refined Ashen identity, loot/reward, and Kiln Sky envelopes are ratified and hash-bound.",
        "- Kiln Sky damage values, attack-effect radii, and a new arena-radius number remain outside the ratified proposal.",
        "- `W1-CREATIVE-005` remains `DEFERRED_BY_USER`; no sidegrade representation is selected.",
        "",
        "## Exact roster and dependency summary",
        "",
        "| Category | Warehouse ID | Acquisition / placement | Loot / harvest identity | Progression / equipment dependency |",
        "|---|---|---|---|---|",
    ]
    for asset in data["assets"]:
        dep = asset["dependencies"]
        acquisition = "; ".join(dep.get("acquisition", []))
        loot = "; ".join(dep.get("loot", [])) or "none specified"
        progression = "; ".join(dep.get("progression", []) + dep.get("crafting", []) + dep.get("equipment", []))
        lines.append(f"| {asset['category']} | `{asset['warehouse_id']}` | {acquisition} | {loot} | {progression} |")
    lines += ["", "## Safe now", ""] + [f"- {x}" for x in data["safe_now_withheld"]["safe_now"]]
    lines += ["", "## Withheld", ""] + [f"- {x}" for x in data["safe_now_withheld"]["withheld"]]
    lines += [
        "", "## Authority notes", "",
        "- Ratified derived components: `heat_core`, `heavy_head`, `chitin_plate`, `ember_heart`.",
        "- Ratified alias: mite-resin language resolves to `aionbound:ember_resin`.",
        "- Ashen non-warehouse terms follow the exact W1-001-AH alias, narrative, context-only, and `drake_scale` dispositions.",
        "- Curiosity prose remains narrative/Codex-only unless Creative separately promotes it.",
        "- Canonical file targets are planning destinations. Their presence or validation is not claimed by this document.",
        "", "## Source bindings", "",
        "| Source | SHA-256 | Role |", "|---|---|---|",
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
    ledger = args.repo_root / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"
    data = build(args.bedrock_root.resolve(), ledger.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.json").write_bytes(json.dumps(data, indent=2, ensure_ascii=False).encode() + b"\n")
    (args.output_dir / "ASHEN_HIGHLANDS_VERTICAL_INTAKE_MAP.md").write_text(render_markdown(data))


if __name__ == "__main__":
    main()
