#!/usr/bin/env python3
"""Build the deterministic Packet 004 Skyreach engineering authority intake."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE_COMMIT = "fb86d22ccaadbcdc890a7cc9038be42667159927"
BASE_TREE = "2a1b83fa9e7cc8ed3f584d21027cea74e05d0582"
BEDROCK = next(p for p in HERE.parents if p.name == "bedrock-server")
CREATIVE_REPO = BEDROCK / "program/crazycraft-pack-production-v1"
PACKET = CREATIVE_REPO / "studio-prep/sprints/asset-sprint-004-skyreach-cliffs"
EQUIPMENT = CREATIVE_REPO / "studio-prep/sprints/asset-sprint-006-equipment-progression"
CREATIVE = CREATIVE_REPO / "studio-prep/creative"

SOURCE_AUTHORITIES = [
    (PACKET / "MANIFEST_FULL.json", "exact Packet 004 roster and visual identity"),
    (PACKET / "SPRINT_004_COMPLETE.md", "50-of-50 visual production receipt and visual-only boundary"),
    (EQUIPMENT / "MANIFEST_FULL.json", "Packet 006 equipment roster"),
    (CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json", "machine Packet 004 and Packet 006 contract"),
    (CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md", "human implementation contract"),
    (CREATIVE / "01_progression/PLAYER_JOURNEY.md", "chapter order and Pilgrimage handoff"),
    (CREATIVE / "02_loot/LOOT_SKYREACH.md", "qualitative Skyreach loot identities and roles"),
    (CREATIVE / "02_loot/LOOT_BOSSES.md", "qualitative Storm Nest reward package"),
    (CREATIVE / "02_loot/LOOT_SYSTEM.md", "global loot laws"),
    (CREATIVE / "03_crafting/CRAFTING_TREE.md", "traversal-first craft graph"),
    (CREATIVE / "04_equipment/EQUIPMENT_PROGRESSION.md", "Packet 006 role and sidegrade boundary"),
    (CREATIVE / "05_structures/STRUCTURES_DESIGN.md", "structure roles"),
    (CREATIVE / "06_world_gen/WORLD_GENERATION.md", "ecology and density intent"),
    (CREATIVE / "07_bosses/BOSS_PROGRESSION.md", "Storm Nest qualitative encounter identity"),
    (CREATIVE / "08_codex/CODEX_ENTRIES_CREATURES.md", "creature Codex relationships"),
    (CREATIVE / "08_codex/CODEX_DESIGN.md", "Codex UX contract"),
]

ALIASES = {
    "Cliff Hoof Keratin": "aionbound:cliff_crystal",
    "Hawk Talon": "aionbound:cliff_crystal",
    "Ram Horn Spiral": "aionbound:cliff_crystal",
    "Ruin Talon": "aionbound:cliff_crystal",
    "Stone Beak": "aionbound:cliff_crystal",
    "Dense Muscle Strip": "aionbound:cloud_wool",
    "Soft Sky Fur": "aionbound:cloud_wool",
    "Drake Membrane": "aionbound:wind_silk",
    "Gale Membrane": "aionbound:wind_silk",
    "Ropewing Membrane": "aionbound:wind_silk",
    "Fox Whisker Cord": "aionbound:wind_silk",
    "Glide Scale": "aionbound:float_resin",
    "Navigation Oil": "aionbound:float_resin",
    "Storm Salt": "aionbound:float_resin",
    "Vulture Crop Stone": "aionbound:float_resin",
    "Nest Crown Plume": "aionbound:storm_pinion",
    "Roc Primary Feather": "aionbound:storm_pinion",
    "Nest Twig": "aionbound:sky_vine_item",
}
NARRATIVE_ONLY = ["Sky Ruin Key Fragment", "Sky Ruin Master Key", "Twinbond-scented down"]
NEW_ITEMS = [{"term": "Wing Bone Stay", "id": "aionbound:wing_bone_stay", "craft_home": "glider_panel"}]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(BEDROCK).as_posix()


def target_map(category: str, ident: str) -> dict:
    shared = ["behavior_pack/scripts/catalog.js", "behavior_pack/scripts/codex.js", "resource_pack/texts/en_US.lang"]
    if category == "creatures":
        create = [
            f"behavior_pack/entities/aionbound/skyreach/{ident}.entity.json",
            f"behavior_pack/loot_tables/entities/aionbound/skyreach/{ident}.json",
            f"resource_pack/entity/aionbound/skyreach/{ident}.entity.json",
            f"resource_pack/models/aionbound/skyreach/{ident}.geo.json",
            f"resource_pack/animations/aionbound/skyreach/{ident}.animation.json",
            f"resource_pack/textures/aionbound/skyreach/{ident}.png",
        ]
        if ident != "wind_roc":
            create.append(f"behavior_pack/spawn_rules/aionbound/skyreach/{ident}.spawn_rules.json")
    elif category == "resources":
        create = [f"behavior_pack/items/{ident}.item.json", f"resource_pack/textures/aionbound/skyreach/items/{ident}.png"]
        shared += ["resource_pack/textures/item_texture.json"]
    elif category in {"blocks", "plants"}:
        create = [f"behavior_pack/blocks/{ident}.block.json", f"behavior_pack/loot_tables/blocks/{ident}.json", f"resource_pack/textures/aionbound/skyreach/{category}/{ident}.png"]
        shared += ["resource_pack/blocks.json", "resource_pack/textures/terrain_texture.json"]
    else:
        create = [f"behavior_pack/structures/aionbound/skyreach/{ident}.mcstructure", f"behavior_pack/features/{ident}.feature.json", f"behavior_pack/feature_rules/{ident}.feature_rule.json"]
        shared += ["behavior_pack/scripts/structures.js"]
    return {"create": sorted(create), "update_shared": sorted(set(shared))}


def asset_sources(ident: str) -> dict:
    paths = {
        "brief": PACKET / "assets/briefs" / f"{ident}.json",
        "editable_bbmodel": PACKET / "assets/editable" / f"{ident}.bbmodel",
        "editable_png": PACKET / "assets/editable" / f"{ident}.png",
        "export_geometry": PACKET / "assets/export/models" / f"{ident}.geo.json",
        "export_animation": PACKET / "assets/export/animations" / f"{ident}.animation.json",
        "export_texture": PACKET / "assets/export/textures" / f"{ident}.png",
    }
    return {key: {"path": rel(path), "sha256": sha(path)} for key, path in paths.items()}


def build() -> dict:
    contract = json.loads((CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json").read_text())
    packet = contract["packets"]["004_skyreach_cliffs"]
    manifest = json.loads((PACKET / "MANIFEST_FULL.json").read_text())
    manifest_ids = {row["name"] for row in manifest["assets"]}
    categories = {
        "creatures": [row["id"] for row in packet["creatures"]],
        "resources": [row["id"] for row in packet["resources"]],
        "blocks": packet["blocks"], "plants": packet["plants"],
        "structures": [row["id"] for row in packet["structures"]],
    }
    ids = [ident for category in categories.values() for ident in category]
    assert len(ids) == len(set(ids)) == 50 and set(ids) == manifest_ids
    rows = []
    for category, entries in categories.items():
        for ident in entries:
            rows.append({"id": ident, "category": category, "source_files": asset_sources(ident), "targets": target_map(category, ident), "authority": "SAFE_NOW_VISUAL_AND_QUALITATIVE_CONTRACT_ONLY"})
    source_bindings = [{"path": rel(path), "sha256": sha(path), "role": role} for path, role in SOURCE_AUTHORITIES]
    return {
        "schema": "aionforge.wave1.skyreach.authority_intake.v1",
        "status": "SKYREACH_INTAKE_MAPPED_IMPLEMENTATION_BLOCKERS_DEFERRED",
        "integration_authority": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "packet": {"id": "004_skyreach_cliffs", "asset_count": 50, "category_counts": {k: len(v) for k, v in categories.items()}},
        "source_bindings": source_bindings,
        "assets": rows,
        "packet_006_links": packet["equipment_links"],
        "safe_now": ["normalize and integrate the exact 50 visual IDs", "implement qualitative entity roles and traversal-first ecology", "author nonnumeric Codex and progression relationships", "preserve existing runtime budgets and handler architecture"],
        "minimum_authority_tranches": {
            "W1-001-SR": {"status": "PROPOSED_NOT_RATIFIED", "aliases": [{"term": k, "canonical_id": v} for k, v in sorted(ALIASES.items())], "narrative_codex_only": NARRATIVE_ONLY, "new_required_items": NEW_ITEMS, "additional_identity_authority": "NONE"},
            "W1-003-STORM-NEST": {"status": "PROPOSED_NOT_RATIFIED", "bound_identity": {"encounter": "aionbound:storm_nest", "boss": "aionbound:wind_roc", "arena": "aionbound:nest_platform", "phases": ["Nest Guard", "Wind Roads", "Harpy Dirge", "Storm Crown"], "attacks": ["Wing Buffet", "Talon Pin", "Gale Dive", "Feather Knives", "Call of the Nest", "Storm Screech"]}, "deferred_decisions": ["health and phase thresholds", "telegraph active recovery and cooldown timing", "leash wipe timeout reset and re-entry", "add caps and multiplayer ownership/scaling", "late join disconnect and restart semantics", "persistent completion and reward entitlement semantics"]},
            "W1-004-SR": {"status": "PROPOSED_NOT_RATIFIED", "loot_identities_bound": True, "critical_seal": "aionbound:storm_pinion", "deferred_decisions": ["C/U/R/E/T/Q probability and quantity envelopes", "structure chest rolls and rarity bands", "apex guaranteed package quantities", "once-per-player seal credit and full-inventory recovery", "repeat-clear and optional mastery reward semantics"]},
        },
        "blocker_matrix": [
            {"id": "W1-001-SR", "class": "CREATIVE_IDENTITY_RATIFICATION", "disposition": "DEFERRED_FOR_LATER_INTERPRETATION", "blocks": "final loot recipe and acquisition identity closure"},
            {"id": "W1-003-STORM-NEST", "class": "CREATIVE_ENCOUNTER_NUMBERS", "disposition": "DEFERRED_FOR_LATER_INTERPRETATION", "blocks": "runtime-complete Storm Nest encounter"},
            {"id": "W1-004-SR", "class": "CREATIVE_LOOT_NUMBERS", "disposition": "DEFERRED_FOR_LATER_INTERPRETATION", "blocks": "final numeric loot and reward implementation"},
            {"id": "W1-CREATIVE-005", "class": "SIDEGRADE_IDENTITY", "disposition": "DEFERRED_BY_USER", "blocks": "summit_hammer skywidow_whip gale_prism_bow nest_talon_dagger stormcloak representations only"},
        ],
        "guards": {"pack_edits": False, "script_edits": False, "bds": False, "build": False, "new_numbers_or_identities_invented": False, "g7_immutable": True},
        "proof_boundary": {"proves": ["EXACT_50_ID_SOURCE_CLOSURE", "SOURCE_HASH_BINDING", "IMPLEMENTATION_TARGET_MAP", "DEFERRED_BLOCKER_CLASSIFICATION"], "does_not_prove": ["CREATIVE_RATIFICATION", "PACK_IMPLEMENTATION", "RUNTIME", "BDS", "CLIENT", "CONSOLE", "RELEASE"]},
    }


def main() -> None:
    data = build()
    (HERE / "SKYREACH_VERTICAL_INTAKE_MAP.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    blockers = "\n".join(f"| `{r['id']}` | {r['class']} | {r['disposition']} | {r['blocks']} |" for r in data["blocker_matrix"])
    (HERE / "SKYREACH_VERTICAL_INTAKE_MAP.md").write_text(
        "# Skyreach Vertical Engineering Intake\n\n"
        f"Bound to G8 `{BASE_COMMIT}` / tree `{BASE_TREE}`. Exact Packet 004 closure: **50 assets** (10 per category).\n\n"
        "Visual normalization and qualitative ecosystem work are safe now. The three minimum Creative tranches are preserved as `PROPOSED_NOT_RATIFIED`; no unapproved number or identity is implementation authority.\n\n"
        "| Ticket | Class | Disposition | Exact blocked surface |\n|---|---|---|---|\n" + blockers + "\n\n"
        "`W1-CREATIVE-005` remains deferred. No BP, RP, script, build, BDS, client, console, or release proof is claimed.\n"
    )


if __name__ == "__main__":
    main()
