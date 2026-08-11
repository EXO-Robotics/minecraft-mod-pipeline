#!/usr/bin/env python3
"""Build the evidence-bound Whisperwood entity runtime implementation map."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
PROGRAM = REPO.parents[2]
CREATIVE = PROGRAM / "crazycraft-pack-production-v1/studio-prep/creative"
SOURCE_MAP = REPO / "engineering/whisperwood-intake/WHISPERWOOD_VERTICAL_IMPLEMENTATION_MAP.json"
OUT_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_program(path: Path) -> str:
    return path.relative_to(PROGRAM.parent).as_posix()


BASE = [
    "minecraft:collision_box", "minecraft:health", "minecraft:loot",
    "minecraft:movement", "minecraft:movement.basic", "minecraft:navigation.walk",
    "minecraft:physics", "minecraft:type_family",
]
AMBIENT = BASE + ["minecraft:behavior.random_stroll", "minecraft:behavior.look_at_player"]
NEUTRAL = BASE + [
    "minecraft:attack", "minecraft:behavior.hurt_by_target",
    "minecraft:behavior.melee_attack", "minecraft:behavior.random_stroll",
    "minecraft:behavior.look_at_player",
]
HOSTILE = NEUTRAL + ["minecraft:behavior.nearest_attackable_target"]


SPEC = {
    "mosskip_fawn": {
        "runtime_class": "ambient",
        "movement_intent": "ground bound-hop",
        "approved_ai": ["graze/idle", "roam", "flee"],
        "g7_pattern": "ambient_ground",
        "components": AMBIENT,
        "extensions": ["flee behavior family and target filters"],
        "spawn": ["clearings", "near mosskip_doe"],
        "drops": ["moss_resin", "star_grass"],
        "withheld_drops": ["Mosskip Tuft"],
        "codex_trigger": "observe in sun-flecked clearings",
        "blockers": ["FLEE_TARGET_POLICY", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "mosskip_doe": {
        "runtime_class": "ambient",
        "movement_intent": "ground bound-hop",
        "approved_ai": ["graze/watch", "herd roam", "flee", "light defense of calves"],
        "g7_pattern": "ambient_ground",
        "components": AMBIENT,
        "extensions": ["flee behavior family and target filters", "calf relationship and conditional defense"],
        "spawn": ["herds", "trails"],
        "drops": ["moss_resin"],
        "withheld_drops": ["Lantern-adjacent soft hide scrap", "Mosskip Antler Bud"],
        "codex_trigger": "observe or gentle approach",
        "blockers": ["FLEE_TARGET_POLICY", "HERD_DEFENSE_BINDING", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "mosskip_buck": {
        "runtime_class": "neutral",
        "movement_intent": "ground bound-hop/charge",
        "approved_ai": ["antler display", "herd roam", "retaliate", "defend herd"],
        "g7_pattern": "neutral_retaliatory_ground",
        "components": NEUTRAL,
        "extensions": ["herd relationship and defense target acquisition", "charge presentation tuning"],
        "spawn": ["near mosskip herd"],
        "drops": ["moss_resin", "whisper_bark", "mosskip_trophy"],
        "withheld_drops": ["Hardened Moss Plate", "Mosskip Crown Fragment"],
        "codex_trigger": "defeat or rare peaceful study",
        "blockers": ["HERD_DEFENSE_BINDING", "LOOT_IDENTITY_W1_CREATIVE_001", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "lantern_hare": {
        "runtime_class": "ambient",
        "movement_intent": "ground quick-hop",
        "approved_ai": ["glow idle", "curious roam", "flee"],
        "g7_pattern": "ambient_ground",
        "components": AMBIENT,
        "extensions": ["flee behavior family and target filters", "night glow presentation"],
        "spawn": ["night", "near lantern_bloom", "near lantern_post"],
        "drops": ["lantern_fur"],
        "withheld_drops": ["Glow Soft Pellet", "Hare's Lucky Foot"],
        "codex_trigger": "night observation near blooms",
        "blockers": ["FLEE_TARGET_POLICY", "LOOT_IDENTITY_W1_CREATIVE_001", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "rootback_boar": {
        "runtime_class": "neutral",
        "movement_intent": "ground trundle/charge",
        "approved_ai": ["root dig", "roam", "retaliate with gore"],
        "g7_pattern": "neutral_retaliatory_ground",
        "components": NEUTRAL,
        "extensions": ["charge presentation tuning"],
        "spawn": ["understory"],
        "drops": ["whisper_bark", "root_heart"],
        "withheld_drops": ["Boar Tusk Shard", "Root Plate"],
        "codex_trigger": "defeat when provoked",
        "blockers": ["LOOT_IDENTITY_W1_CREATIVE_001", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "briar_elk": {
        "runtime_class": "neutral",
        "movement_intent": "ground stag gait",
        "approved_ai": ["antler idle", "rare meadow roam", "heavy antler combat"],
        "g7_pattern": "neutral_retaliatory_ground",
        "components": NEUTRAL,
        "extensions": ["mini-apex initiation policy", "heavy-antler presentation tuning"],
        "spawn": ["meadows", "rare"],
        "drops": ["briar_antler", "briar_elk_trophy", "ancient_acorn"],
        "withheld_drops": ["Thick Hide", "Briar Crown"],
        "codex_trigger": "hunt or witness meadow rite",
        "blockers": ["MINI_APEX_TARGET_POLICY", "LOOT_IDENTITY_W1_CREATIVE_001", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "rot_wolf": {
        "runtime_class": "hostile",
        "movement_intent": "ground pack-run",
        "approved_ai": ["pace", "player acquisition", "pursue", "pack melee"],
        "g7_pattern": "hostile_melee_ground",
        "components": HOSTILE,
        "extensions": ["bounded pack coordination and pack cap"],
        "spawn": ["night", "deep trails", "pack grouping"],
        "drops": [],
        "withheld_drops": ["Rot Fang", "Tainted Pelt", "Marrow Scrap", "Pack Alpha Mark"],
        "codex_trigger": "survive a pack",
        "blockers": ["PACK_COORDINATION_BINDING", "LOOT_IDENTITY_W1_CREATIVE_001", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "thorn_stalker": {
        "runtime_class": "boss",
        "movement_intent": "ground stalk/lunge",
        "approved_ai": ["camouflage idle", "stalk", "lunge", "Thorn Court phase kit"],
        "g7_pattern": "hostile_melee_ground_plus_encounter_shell",
        "components": HOSTILE,
        "extensions": ["phase state machine", "telegraphed projectile and area attacks", "bounded add summons", "reset and terminal reward semantics"],
        "spawn": ["deep briar elite ecology", "Thorn Court arena encounter"],
        "drops": ["briar_vine", "thorn_stalker_skull"],
        "withheld_drops": ["Thorn Barb", "Stalker Claw"],
        "codex_trigger": "defeat elite or Thorn Court apex",
        "blockers": ["BOSS_ENVELOPE_W1_CREATIVE_003", "LOOT_IDENTITY_W1_CREATIVE_001", "LOOT_RANGES_W1_CREATIVE_004", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "hollow_widow_spider": {
        "runtime_class": "hostile",
        "movement_intent": "ground plus climb",
        "approved_ai": ["web idle", "player acquisition", "pursue", "silk/bite combat"],
        "g7_pattern": "hostile_melee_ground",
        "components": HOSTILE,
        "extensions": ["minecraft:can_climb", "minecraft:navigation.climb", "silk attack delivery and status semantics"],
        "spawn": ["caves", "giant roots"],
        "drops": ["widow_silk"],
        "withheld_drops": ["Hollow Venom Sac", "Chitin Shard", "Widow Eye"],
        "codex_trigger": "cave encounter",
        "blockers": ["CLIMB_RUNTIME_PATTERN_NOT_IN_G7", "SILK_COMBAT_BINDING", "LOOT_IDENTITY_W1_CREATIVE_001", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
    "bark_wraith": {
        "runtime_class": "hostile",
        "movement_intent": "spectral phase-drift",
        "approved_ai": ["idle sway", "night/totem presence", "soft spectral combat"],
        "g7_pattern": "no_complete_g7_pattern",
        "components": BASE,
        "extensions": ["movement/navigation family for phase drift", "target policy", "soft-spectral attack delivery"],
        "spawn": ["night", "deep forest", "totems", "very low frequency"],
        "drops": ["whisper_bark", "hollow_amber", "moon_sap", "ancient_acorn_display"],
        "withheld_drops": ["Wraith Mask Fragment"],
        "codex_trigger": "night deep-forest or totem encounter",
        "blockers": ["SPECTRAL_MOTION_ARCHITECTURE", "SPECTRAL_TARGET_POLICY", "LOOT_IDENTITY_W1_CREATIVE_001", "PERSISTENCE_SEMANTICS", "ANIMATION_COVERAGE", "NATIVE_ASSET_DISPOSITION"],
    },
}


PATTERNS = {
    "ambient_ground": ["behavior_pack/entities/mosskip.entity.json", "behavior_pack/entities/lanternback.entity.json"],
    "neutral_retaliatory_ground": ["behavior_pack/entities/pebblehorn.entity.json", "behavior_pack/entities/galestrider.entity.json"],
    "hostile_melee_ground": ["behavior_pack/entities/cinder_brood_hatchling.entity.json", "behavior_pack/entities/basalt_behemoth.entity.json"],
    "hostile_melee_ground_plus_encounter_shell": ["behavior_pack/entities/ash_sovereign_wyrm.entity.json", "behavior_pack/scripts/encounters.js", "behavior_pack/scripts/state.js"],
    "no_complete_g7_pattern": [],
}


def authority(path: Path) -> dict:
    return {"path": rel_program(path), "sha256": sha256(path)}


def build() -> dict:
    source = json.loads(SOURCE_MAP.read_text())
    creatures = {a["warehouse_id"]: a for a in source["assets"] if a["category"] == "creatures"}
    assert set(creatures) == set(SPEC)
    result = {
        "schema": "aionbound.wave1.whisperwood.entity_runtime_map.v1",
        "status": "IMPLEMENTATION_MAP_NOT_RUNTIME_PROOF",
        "scope": "Packet 001 ten-creature BP/RP construction plan; no pack bytes are created or changed",
        "base": {
            "commit": "17cd830a0df75bef7aca92dfc1dd3d0dd8b303ec",
            "classification": "G7 successor integration worktree",
        },
        "authorities": [
            authority(CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md"),
            authority(CREATIVE / "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.json"),
            authority(CREATIVE / "02_loot/LOOT_WHISPERWOOD.md"),
            authority(CREATIVE / "06_world_gen/WORLD_GENERATION.md"),
            authority(CREATIVE / "07_bosses/BOSS_PROGRESSION.md"),
            authority(CREATIVE / "08_codex/CODEX_ENTRIES_CREATURES.md"),
            authority(SOURCE_MAP),
        ],
        "g7_patterns": {},
        "global_decisions": {
            "namespace": "aionbound",
            "numeric_policy": "No health, damage, speed, priority, distance, spawn weight, group size, drop chance, or boss threshold is selected here.",
            "g7_reuse_rule": "Reuse only named component families and script responsibilities; G7 numeric values and cast identities do not transfer.",
            "animation_rule": "Generic exported idle/action clips do not satisfy differently named brief-declared role clips.",
            "persistence_rule": "G7 proves player/world encounter journals, not ordinary-creature restart persistence. Entity persistence/despawn semantics require an explicit successor decision.",
            "loot_rule": "Warehouse identities are eligible for wiring; narrative-only drop names remain withheld under W1-CREATIVE-001; probabilities remain withheld under W1-CREATIVE-004.",
            "sound_rule": "Placeholder sounds are allowed only during construction; identity sound assets remain required before Whisperwood Done.",
        },
        "entities": [],
        "global_blockers": [
            "W1-CREATIVE-001 non-warehouse drop identities",
            "W1-CREATIVE-003 Thorn Court numeric/reset/multiplayer/persistence/reward envelope",
            "W1-CREATIVE-004 loot probability and quantity ranges",
            "All ten assets lack brief-declared animation clips in current exports",
            "All ten editable bbmodels require native locator/path round-trip disposition",
            "Ordinary-creature restart persistence conflicts with unspecified despawn/cap semantics",
        ],
        "proof_boundary": {
            "proves": ["authority-bound role map", "target-file map", "G7 component-family provenance", "declared-versus-actual animation gap inventory", "explicit implementation blockers"],
            "does_not_prove": ["schema validity of future pack files", "asset native round-trip", "animation quality", "entity movement", "AI behavior", "spawn ecology", "loot economy", "persistence", "BDS", "client", "console", "multiplayer", "release"],
        },
    }
    for name, files in PATTERNS.items():
        result["g7_patterns"][name] = [
            {"path": f, "sha256": sha256(REPO / f)} for f in files
        ]
    for entity_id in sorted(SPEC):
        spec = SPEC[entity_id]
        src = creatures[entity_id]
        actual = src["static_validation"]["animation"]["animation_names"]
        declared = src["source_brief"]["declared_animations"]
        target = src["target_files"]
        record = {
            "warehouse_id": entity_id,
            "runtime_id": src["runtime_id"],
            "approved_role": src["creative_contract"]["role"],
            "runtime_class": spec["runtime_class"],
            "apex": src["creative_contract"].get("apex", False),
            "creative_evidence": src["creative_evidence"],
            "movement_intent": spec["movement_intent"],
            "approved_ai_intent": spec["approved_ai"],
            "g7_pattern": spec["g7_pattern"],
            "g7_proven_component_families": spec["components"],
            "required_unproven_extensions": spec["extensions"],
            "spawn_dependencies": spec["spawn"],
            "drop_dependencies": {
                "warehouse_identities_eligible_for_wiring": spec["drops"],
                "narrative_only_identities_withheld": spec["withheld_drops"],
                "table_target": f"behavior_pack/loot_tables/entities/{entity_id}.json",
                "probability_status": "WITHHELD_W1_CREATIVE_004",
            },
            "codex_dependency": {
                "trigger_intent": spec["codex_trigger"],
                "targets": ["behavior_pack/scripts/catalog.js", "behavior_pack/scripts/codex.js", "behavior_pack/scripts/state.js"],
                "status": "ENTRY_TEXT_APPROVED_TRIGGER_IMPLEMENTATION_NOT_PROVEN",
            },
            "persistence_dependency": {
                "ordinary_entity": "UNRESOLVED_ENTITY_PERSISTENCE_AND_DESPAWN_POLICY",
                "discovery": "G7_STATE_SCHEMA_REUSABLE_WITH_SUCCESSOR_MIGRATION",
                "boss_encounter": "G7_ENCOUNTER_JOURNAL_REUSABLE_BUT_THORN_SEMANTICS_BLOCKED" if entity_id == "thorn_stalker" else "not_applicable",
            },
            "animations": {
                "brief_declared": declared,
                "exported_actual": actual,
                "missing_declared": declared,
                "generic_exports_not_accepted_as_aliases": actual,
                "status": "BLOCKED_ROLE_CLIPS_ABSENT",
            },
            "source_assets": src["canonical_source"],
            "target_files": {
                "create": target["create"],
                "shared_updates": target["update_shared"],
                "additional_runtime_targets": ["resource_pack/sounds/sound_definitions.json"],
            },
            "blockers": spec["blockers"],
            "construction_status": "SKELETON_FAMILIES_MAPPED_FULL_ENTITY_WITHHELD",
        }
        result["entities"].append(record)
    return result


def render_md(data: dict) -> str:
    lines = [
        "# Whisperwood Entity Runtime Implementation Map", "",
        f"Status: **{data['status']}**", "",
        "This is a construction map for Packet 001's ten creatures. It does not edit BP/RP files and does not claim runtime behavior.", "",
        "## Binding rules", "",
    ]
    for key, value in data["global_decisions"].items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    lines += ["", "## Per-creature map", ""]
    for e in data["entities"]:
        lines += [
            f"### `{e['warehouse_id']}`", "",
            f"- Approved role: `{e['approved_role']}`; runtime class: `{e['runtime_class']}`; apex: `{str(e['apex']).lower()}`",
            f"- Movement: {e['movement_intent']}",
            f"- G7 pattern: `{e['g7_pattern']}`",
            "- Creative evidence: " + ", ".join(
                f"`{x['path']}:{x['line']}`" for x in e["creative_evidence"]
                if "WAVE_1_LIVING_WORLD_IMPLEMENTATION_CONTRACT.md" in x["path"] and x["line"] < 800
            ),
            f"- G7-proven component families: {', '.join(f'`{x}`' for x in e['g7_proven_component_families'])}",
            f"- Required but unproven extensions: {', '.join(e['required_unproven_extensions']) or 'none'}",
            f"- Spawn dependencies: {', '.join(e['spawn_dependencies'])}",
            f"- Warehouse drops eligible for wiring: {', '.join(e['drop_dependencies']['warehouse_identities_eligible_for_wiring']) or 'none'}",
            f"- Narrative-only drops withheld: {', '.join(e['drop_dependencies']['narrative_only_identities_withheld']) or 'none'}",
            f"- Codex trigger: {e['codex_dependency']['trigger_intent']}",
            f"- Declared clips: {', '.join(f'`{x}`' for x in e['animations']['brief_declared'])}",
            f"- Actual clips: {', '.join(f'`{x}`' for x in e['animations']['exported_actual'])}",
            f"- Blockers: {', '.join(f'`{x}`' for x in e['blockers'])}", "",
            "Target creates:", "",
        ]
        lines += [f"- `{p}`" for p in e["target_files"]["create"]]
        lines.append("")
    lines += ["## G7 evidence", ""]
    for name, entries in data["g7_patterns"].items():
        lines.append(f"- `{name}`: " + (", ".join(f"`{x['path']}` (`{x['sha256']}`)" for x in entries) or "no complete pattern"))
    lines += ["", "## Global blockers", ""] + [f"- {b}" for b in data["global_blockers"]]
    lines += ["", "## Proof boundary", "", "This map proves only: " + "; ".join(data["proof_boundary"]["proves"]) + ".", "", "It does **not** prove: " + "; ".join(data["proof_boundary"]["does_not_prove"]) + ".", ""]
    return "\n".join(lines)


def main() -> None:
    data = build()
    json_text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    md_text = render_md(data)
    (OUT_DIR / "WHISPERWOOD_ENTITY_RUNTIME_IMPLEMENTATION_MAP.json").write_text(json_text)
    (OUT_DIR / "WHISPERWOOD_ENTITY_RUNTIME_IMPLEMENTATION_MAP.md").write_text(md_text)
    print(sha256(OUT_DIR / "WHISPERWOOD_ENTITY_RUNTIME_IMPLEMENTATION_MAP.json"))
    print(sha256(OUT_DIR / "WHISPERWOOD_ENTITY_RUNTIME_IMPLEMENTATION_MAP.md"))


if __name__ == "__main__":
    main()
