from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from mccompiler.reconstruction.diagnostics import (
    DECOMPOSITION_CATEGORIES,
    DIAGNOSTIC_REPORT_FILENAMES,
    EXPRESSION_CATEGORIES,
    PS4_DIMENSIONS,
    diagnose_reconstruction_wave,
)


FEATURE_ORDER = (
    "mossback_forager", "resonance_sling", "signal_ruin",
    "thornwarden_elite", "forest_attunement", "sporefall_event",
)
ROLE = {
    "mossback_forager": "baseline passive regional creature",
    "resonance_sling": "first unusual ranged equipment upgrade",
    "signal_ruin": "discoverable forest landmark and encounter initializer",
    "thornwarden_elite": "gated elite encounter",
    "forest_attunement": "persistent distinctive progression unlock",
    "sporefall_event": "bounded deterministic chaos event",
}
SCOPE = {
    "mossback_forager": 5, "resonance_sling": 6, "signal_ruin": 7,
    "thornwarden_elite": 8, "forest_attunement": 5, "sporefall_event": 7,
}
RELEVANT_DISPOSITIONS: dict[str, dict[str, str]] = {
    "mossback_forager": {
        "identity": "REDESIGNED", "name_and_branding": "REDESIGNED",
        "visual_presentation": "REDESIGNED", "model": "REDESIGNED",
        "texture": "REDESIGNED", "animation": "RECONSTRUCTED",
        "audio": "REDESIGNED", "registration": "DIRECT",
        "entity_behavior": "RECONSTRUCTED", "navigation": "DIRECT",
        "combat": "RECONSTRUCTED", "loot": "DIRECT", "spawn_rules": "DIRECT",
        "state_ownership": "RECONSTRUCTED", "multiplayer_behavior": "RECONSTRUCTED",
        "cleanup": "DIRECT", "performance_characteristics": "REDESIGNED",
        "block_interaction": "SCRIPTED",
    },
    "resonance_sling": {
        "identity": "REDESIGNED", "name_and_branding": "REDESIGNED",
        "visual_presentation": "REDESIGNED", "model": "REDESIGNED",
        "texture": "REDESIGNED", "animation": "RECONSTRUCTED",
        "audio": "REDESIGNED", "registration": "DIRECT",
        "recipe_or_acquisition": "DIRECT", "item_use": "RECONSTRUCTED",
        "projectile_behavior": "SCRIPTED", "event_subscriptions": "SCRIPTED",
        "combat": "RECONSTRUCTED", "cleanup": "SCRIPTED",
        "multiplayer_behavior": "SCRIPTED", "performance_characteristics": "REDESIGNED",
    },
    "signal_ruin": {
        "identity": "REDESIGNED", "name_and_branding": "REDESIGNED",
        "visual_presentation": "REDESIGNED", "model": "REDESIGNED",
        "texture": "REDESIGNED", "audio": "REDESIGNED",
        "registration": "DIRECT", "world_generation": "DEFERRED",
        "structure_layout": "REDESIGNED", "loot": "DIRECT",
        "event_subscriptions": "SCRIPTED", "state_ownership": "SCRIPTED",
        "persistence": "SCRIPTED", "migration": "SCRIPTED",
        "multiplayer_behavior": "SCRIPTED", "failure_handling": "SCRIPTED",
        "cleanup": "SCRIPTED", "performance_characteristics": "REDESIGNED",
    },
    "thornwarden_elite": {
        "identity": "REDESIGNED", "name_and_branding": "REDESIGNED",
        "visual_presentation": "REDESIGNED", "model": "REDESIGNED",
        "texture": "REDESIGNED", "animation": "RECONSTRUCTED",
        "audio": "REDESIGNED", "registration": "DIRECT",
        "entity_behavior": "SCRIPTED", "navigation": "DIRECT",
        "combat": "SCRIPTED", "event_subscriptions": "SCRIPTED",
        "loot": "DIRECT", "state_ownership": "SCRIPTED",
        "persistence": "SCRIPTED", "migration": "SCRIPTED",
        "multiplayer_behavior": "SCRIPTED", "cleanup": "SCRIPTED",
        "dependencies": "DEFERRED", "performance_characteristics": "REDESIGNED",
    },
    "forest_attunement": {
        "identity": "REDESIGNED", "name_and_branding": "REDESIGNED",
        "visual_presentation": "REDESIGNED", "audio": "REDESIGNED",
        "progression": "SCRIPTED", "state_ownership": "SCRIPTED",
        "persistence": "SCRIPTED", "migration": "SCRIPTED",
        "multiplayer_behavior": "SCRIPTED", "failure_handling": "SCRIPTED",
        "cleanup": "DIRECT", "dependencies": "RECONSTRUCTED",
        "performance_characteristics": "REDESIGNED",
    },
    "sporefall_event": {
        "identity": "REDESIGNED", "name_and_branding": "REDESIGNED",
        "visual_presentation": "REDESIGNED", "animation": "RECONSTRUCTED",
        "audio": "REDESIGNED", "registration": "DIRECT",
        "entity_behavior": "SCRIPTED", "navigation": "DIRECT",
        "combat": "SCRIPTED", "projectile_behavior": "DEFERRED",
        "event_subscriptions": "SCRIPTED", "spawn_rules": "SCRIPTED",
        "progression": "SCRIPTED", "state_ownership": "SCRIPTED",
        "persistence": "SCRIPTED", "migration": "SCRIPTED",
        "multiplayer_behavior": "SCRIPTED", "failure_handling": "SCRIPTED",
        "cleanup": "SCRIPTED", "dependencies": "RECONSTRUCTED",
        "performance_characteristics": "REDESIGNED",
    },
}
PS4_VALUES = {
    "mossback_forager": [6, 7, 5, 6, 7, 5, 6, 7, 5, 6, 7, 5],
    "resonance_sling": [6, 7, 8, 6, 7, 8, 6, 7, 6, 6, 7, 8],
    "signal_ruin": [9, 7, 8, 6, 7, 8, 9, 7, 6, 8, 7, 8],
    "thornwarden_elite": [8, 8, 8, 6, 8, 8, 8, 8, 6, 8, 8, 10],
    "forest_attunement": [6, 7, 5, 6, 7, 5, 6, 7, 5, 6, 7, 5],
    "sporefall_event": [9, 7, 8, 6, 7, 8, 9, 7, 6, 8, 7, 8],
}
ARTIFACTS: dict[str, list[tuple[str, str, str]]] = {
    "mossback_forager": [
        ("bedrock/behavior_pack/entities/ccoriginal_cc/mossback_forager.json", "behavior", "GENERATED"),
        ("bedrock/behavior_pack/spawn_rules/ccoriginal_cc/mossback_forager.json", "behavior", "GENERATED"),
        ("bedrock/behavior_pack/loot_tables/ccoriginal_cc/entities/mossback_forager.json", "behavior", "GENERATED"),
        ("bedrock/resource_pack/entity/mossback_forager.entity.json", "resource", "GENERATED"),
        ("bedrock/resource_pack/models/entity/mossback_forager.geo.json", "asset", "GENERATED"),
        ("bedrock/resource_pack/textures/entity/mossback_forager.png", "asset", "AUTHORED_ORIGINAL"),
        ("bedrock/resource_pack/animations/mossback_forager.animation.json", "asset", "AUTHORED_ORIGINAL"),
        ("assets/blockbench/mossback_forager/mossback_forager.bbmodel", "internal_asset", "AUTHORED_ORIGINAL"),
    ],
    "resonance_sling": [
        ("bedrock/behavior_pack/items/ccoriginal_cc/resonance_sling.json", "behavior", "GENERATED"),
        ("bedrock/behavior_pack/entities/ccoriginal_cc/resonance_projectile.json", "behavior", "GENERATED"),
        ("bedrock/behavior_pack/recipes/ccoriginal_cc/resonance_sling.json", "behavior", "GENERATED"),
        ("bedrock/behavior_pack/scripts/features/resonance_sling.ts", "script", "GENERATED"),
        ("bedrock/resource_pack/attachables/resonance_sling.attachable.json", "resource", "GENERATED"),
        ("bedrock/resource_pack/models/entity/resonance_sling.geo.json", "asset", "GENERATED"),
        ("bedrock/resource_pack/textures/items/resonance_sling.png", "asset", "AUTHORED_ORIGINAL"),
        ("assets/blockbench/resonance_sling/resonance_sling.bbmodel", "internal_asset", "AUTHORED_ORIGINAL"),
    ],
    "signal_ruin": [
        ("bedrock/behavior_pack/structures/ccoriginal_cc/signal_ruin.mcstructure", "structure", "AUTHORED_ORIGINAL"),
        ("bedrock/behavior_pack/loot_tables/ccoriginal_cc/chests/signal_ruin.json", "behavior", "GENERATED"),
        ("bedrock/behavior_pack/scripts/features/signal_ruin.ts", "script", "GENERATED"),
        ("bedrock/behavior_pack/scripts/state/signal_ruin_state.ts", "script", "GENERATED"),
        ("production/design-contracts/signal_ruin-layout.json", "internal_record", "AUTHORED_ORIGINAL"),
    ],
    "thornwarden_elite": [
        ("bedrock/behavior_pack/entities/ccoriginal_cc/thornwarden_elite.json", "behavior", "GENERATED"),
        ("bedrock/behavior_pack/scripts/features/thornwarden_elite.ts", "script", "GENERATED"),
        ("bedrock/behavior_pack/loot_tables/ccoriginal_cc/entities/thornwarden_elite.json", "behavior", "GENERATED"),
        ("bedrock/resource_pack/entity/thornwarden_elite.entity.json", "resource", "GENERATED"),
        ("bedrock/resource_pack/models/entity/thornwarden_elite.geo.json", "asset", "GENERATED"),
        ("bedrock/resource_pack/textures/entity/thornwarden_elite.png", "asset", "AUTHORED_ORIGINAL"),
        ("bedrock/resource_pack/animations/thornwarden_elite.animation.json", "asset", "AUTHORED_ORIGINAL"),
        ("assets/blockbench/thornwarden_elite/thornwarden_elite.bbmodel", "internal_asset", "AUTHORED_ORIGINAL"),
    ],
    "forest_attunement": [
        ("bedrock/behavior_pack/scripts/features/forest_attunement.ts", "script", "GENERATED"),
        ("bedrock/behavior_pack/scripts/state/forest_attunement_state.ts", "script", "GENERATED"),
        ("bedrock/behavior_pack/recipes/ccoriginal_cc/attuned_recipes.json", "behavior", "GENERATED"),
        ("production/design-contracts/forest_attunement-state-v1.json", "internal_record", "GENERATED"),
        ("production/design-contracts/forest_attunement-migration-v1.json", "internal_record", "GENERATED"),
    ],
    "sporefall_event": [
        ("bedrock/behavior_pack/scripts/features/sporefall_event.ts", "script", "GENERATED"),
        ("bedrock/behavior_pack/scripts/state/sporefall_event_state.ts", "script", "GENERATED"),
        ("bedrock/behavior_pack/functions/ccoriginal_cc/sporefall/cleanup.mcfunction", "behavior", "GENERATED"),
        ("bedrock/resource_pack/particles/sporefall.json", "asset", "AUTHORED_ORIGINAL"),
        ("bedrock/resource_pack/sounds/sound_definitions.json", "resource", "MODIFY_GENERATED"),
        ("production/design-contracts/sporefall-event-caps.json", "internal_record", "GENERATED"),
    ],
}


def _planning_paths(feature_id: str) -> list[str]:
    base = f"production/planning/controlled-chaos-forest/contracts/{feature_id}"
    paths = [
        f"analysis/gameplay-intent/controlled-chaos-forest/{feature_id}.json",
        f"{base}/asset.json", f"{base}/behavior.json",
        f"{base}/clean-room-design.json", f"{base}/qualification.json",
    ]
    if feature_id in {"signal_ruin", "thornwarden_elite", "sporefall_event"}:
        paths.append(f"{base}/encounter.json")
    return paths


def _part(feature_id: str, category: str) -> dict[str, Any]:
    disposition = RELEVANT_DISPOSITIONS[feature_id].get(category, "DEFERRED")
    is_deferred = disposition == "DEFERRED"
    implementation = {
        "mossback_forager": "native entity components first; bounded event-driven resource interaction only after evidence",
        "resonance_sling": "native item/projectile definitions plus bounded owner-attributed impact script",
        "signal_ruin": "original mcstructure with revisioned idempotent placement and initialization",
        "thornwarden_elite": "encounter-only entity with bounded scripted phase state machine",
        "forest_attunement": "player-scoped versioned dynamic property with world revision index",
        "sporefall_event": "region-scoped bounded event controller with explicit caps and cleanup",
    }[feature_id]
    return {
        "category": category,
        "claim_state": "unknown" if is_deferred else "inferred",
        "disposition": disposition,
        "evidence_basis": (
            "no authorized Java evidence; category retained for explicit gap tracking"
            if is_deferred
            else "internal planning contract supports only the abstract role; Bedrock mapping is proposed"
        ),
        "rights_basis": "source expression has no registered production permission; clean-room replacement required",
        "bedrock_implementation": "not selected pending evidence" if is_deferred else implementation,
        "fidelity_impact": "unknown until authorized observations exist",
        "risks": [
            "source mechanic may differ from proposed mapping",
            "client and physical-console behavior remains untested",
        ],
        "required_tests": ["evidence-to-intent trace", "rights/taint audit", "feature-specific static and runtime qualification"],
        "execution_may_proceed": False,
    }


def _expressions(feature_id: str) -> list[dict[str, Any]]:
    return [{
        "category": category,
        "disposition": (
            "ABSTRACT_PATTERN_RETAINED"
            if category in {"elite_staging", "progression_combinations"}
            else "CLEAN_ROOM_REPLACEMENT"
        ),
        "source_material_status": "NOT_REGISTERED",
        "production_rule": "author independently; do not inspect or transfer source expression during production",
        "product_identity": feature_id,
    } for category in EXPRESSION_CATEGORIES]


def _runtime(feature_id: str) -> dict[str, Any]:
    planned_systems = {
        "mossback_forager": ["native creature AI", "bounded optional resource interaction"],
        "resonance_sling": ["item use", "owner-attributed projectile", "impact and TTL cleanup"],
        "signal_ruin": ["placement registry", "idempotent initialization", "encounter state"],
        "thornwarden_elite": ["single-instance encounter lock", "phase state machine", "reward transaction"],
        "forest_attunement": ["versioned player unlock", "migration", "administrative recovery"],
        "sporefall_event": ["eligibility/cooldown", "bounded phases", "spawn budget", "cleanup-to-zero"],
    }[feature_id]
    native = {
        "mossback_forager": ["minecraft:movement", "minecraft:navigation.walk", "minecraft:behavior.random_stroll", "minecraft:loot"],
        "resonance_sling": ["minecraft:cooldown", "minecraft:durability", "minecraft:projectile"],
        "signal_ruin": ["mcstructure", "loot_table"],
        "thornwarden_elite": ["minecraft:health", "minecraft:attack", "minecraft:navigation.walk", "minecraft:loot"],
        "forest_attunement": [],
        "sporefall_event": ["spawn_rules"],
    }[feature_id]
    scripted = feature_id != "mossback_forager"
    return {
        "status": "PROPOSED_PENDING_EVIDENCE",
        "planned_systems": planned_systems,
        "stable_components": native,
        "stable_script_api_symbols": (
            ["world.afterEvents", "system.runTimeout", "Entity.getDynamicProperty", "Entity.setDynamicProperty"]
            if scripted else []
        ),
        "event_subscriptions": ["bounded feature-specific after-event subscription"] if scripted else [],
        "scheduled_callbacks": {"cadence": "event-driven; minimum 20 ticks when polling is unavoidable", "global_per_tick_scan": False},
        "entity_query_frequency": "bounded local query on transition only; never full-world per-tick",
        "dynamic_properties": [] if feature_id == "mossback_forager" else [f"ccoriginal_cc:{feature_id}:v1"],
        "scoreboards": [],
        "state_ownership": (
            "player with world revision index" if feature_id == "forest_attunement"
            else "canonical structure instance" if feature_id in {"signal_ruin", "thornwarden_elite"}
            else "bounded event owner and region" if feature_id == "sporefall_event"
            else "projectile owner" if feature_id == "resonance_sling"
            else "entity-local"
        ),
        "state_schema_version": "1",
        "atomic_write": "revision compare, write payload, then commit marker; replay idempotently",
        "migration": "explicit v1 migrator with corrupt/missing-state fallback; no implicit schema drift",
        "multiplayer_locking": "canonical key plus revision/claim token; duplicate rewards rejected",
        "idempotency": "all acquisition, initialization, reward, and cleanup transitions carry stable transaction keys",
        "restart_behavior": "restore valid committed state; roll back incomplete transaction; clean transient entities",
        "cleanup": "bounded selectors/owned IDs; zero-state receipt required",
        "error_handling": "record diagnostic and fail closed without changing vanilla behavior",
        "fail_policy": "FAIL_CLOSED_FOR_ADDON_FEATURE; VANILLA_REMAINS_AVAILABLE",
        "worst_credible_runtime_load": "UNKNOWN until evidence defines behavior and concurrency envelope",
        "preview_or_experimental_apis": [],
    }


def _artifacts(feature_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, kind, ownership in ARTIFACTS[feature_id]:
        internal = path.startswith(("assets/", "production/"))
        rows.append({
            "path": path,
            "kind": kind,
            "action": "MODIFY" if ownership == "MODIFY_GENERATED" else "CREATE",
            "ownership": "GENERATED" if ownership == "MODIFY_GENERATED" else ownership,
            "consumer_package_inclusion": not internal,
            "internal_only_exclusion": internal,
            "dependencies": [],
            "collision_risks": ["identifier/path collision; fail before write"],
            "protected_custom_region": False,
        })
    for suffix in ("asset-manifest", "originality", "similarity-screening", "cost-report", "qualification-plan"):
        rows.append({
            "path": f"production/reconstruction-waves/forest-wave-1/{feature_id}/{suffix}.json",
            "kind": "internal_record",
            "action": "CREATE",
            "ownership": "GENERATED",
            "consumer_package_inclusion": False,
            "internal_only_exclusion": True,
            "dependencies": [],
            "collision_risks": ["existing record revision collision"],
            "protected_custom_region": False,
        })
    return rows


def _qualification(feature_id: str) -> dict[str, Any]:
    return {
        "static": [
            "schema and JSON validation", "identifier collision validation",
            "rights and taint validation", "stable API validation",
            "asset binding validation", "consumer package audit", "determinism",
        ],
        "asset": [
            "native Blockbench save/reopen", "native geometry/animation export",
            "bone and locator checks", "texture format and bounds",
            "required visual-review captures", "asset cost report",
        ] if feature_id in {"mossback_forager", "resonance_sling", "thornwarden_elite"} else ["original asset validation when design requires assets"],
        "runtime_server": [
            "summon/acquisition/placement", "core behavior and state transitions",
            "spawn/loot/reward idempotency", "restart/persistence/migration",
            "two/four-player contention", "cleanup-to-zero", "stress/endurance/repeat",
        ],
        "client_presentation": [
            "geometry/texture/animation", "first/third person where applicable",
            "particles/audio/bounds/culling", "controller usability",
        ],
        "ps4_planning": ["all 12 dimensions", "named connected scenes", "hard caps and protected reserves"],
        "physical_ps4": ["Realm delivery", "controller-only", "split-screen", "frame pacing/memory", "save/reconnect"],
        "status": "PENDING",
    }


def _feature(feature_id: str, plan_costs: Mapping[str, Any]) -> dict[str, Any]:
    paths = _planning_paths(feature_id)
    missing = [
        "authorized Java registration/symbol evidence",
        "authorized runtime observation",
        "material-level ownership and commercial/Marketplace permissions",
        "source behavior parameters and dependency evidence",
        "source expression inventory and rights disposition",
    ]
    dependency_block = feature_id == "thornwarden_elite"
    evidence = [{
        "evidence_id": f"internal-plan-{feature_id}-v1",
        "kind": "INTERNAL_PLANNING_CONTRACT",
        "paths": paths,
        "authorized_java_evidence": False,
        "proves": [f"selected clean-room role: {ROLE[feature_id]}", "planning-only status", "generic bounded cleanup/multiplayer/persistence requirements"],
        "does_not_prove": ["any Java source mechanic", "source rights", "implementation", "runtime qualification"],
        "rights_disposition": "ANALYSIS_ONLY_INTERNAL_PLAN",
    }]
    if feature_id in {"resonance_sling", "signal_ruin"}:
        evidence.append({
            "evidence_id": f"bedrock-benchmark-{feature_id}-v1",
            "kind": "EXISTING_BEDROCK_TECHNICAL_TEMPLATE",
            "paths": [
                "benchmarks/controlled-chaos-integration/behavior-model/contract.json",
                "benchmarks/controlled-chaos-integration/bedrock/behavior_pack/scripts/main.js",
            ],
            "authorized_java_evidence": False,
            "proves": (
                [
                    "a Bedrock template implements a 20-tick cooldown",
                    "the template caps projectiles at 12 with 100-tick lifetime",
                    "owner-attributed entity/block impact is technically expressible",
                ]
                if feature_id == "resonance_sling" else [
                    "a Bedrock template can place one mcstructure at a controlled location",
                    "world dynamic property can prevent repeat initialization",
                ]
            ),
            "does_not_prove": [
                "the intended Java mechanic", "source rights", "production suitability",
                "controller presentation", "PS4 performance",
            ],
            "rights_disposition": "ANALYSIS_ONLY_TECHNICAL_TEMPLATE",
            "redesign_required": (
                "replace broad periodic projectile scans with bounded owned-entity tracking"
                if feature_id == "resonance_sling"
                else "replace fixed-coordinate/console interaction with approved placement and controller-safe activation"
            ),
        })
    return {
        "feature_id": feature_id,
        "role": ROLE[feature_id],
        "scope_units": SCOPE[feature_id],
        "evidence": evidence,
        "claims": [
            {
                "claim": f"the repository selected {feature_id} for the role {ROLE[feature_id]}",
                "classification": "observed",
                "confidence": 1.0,
                "evidence_refs": paths,
                "rationale": "Directly recorded in the checked-in planning contract.",
                "rights_disposition": "CLEAN_ROOM_INTERNAL_IDENTITY",
            },
            {
                "claim": "the proposed Bedrock strategy can serve the selected abstract role",
                "classification": "inferred",
                "confidence": 0.35,
                "evidence_refs": paths,
                "rationale": "Feasibility proposal based on stable Bedrock patterns, not Java evidence.",
                "rights_disposition": "ABSTRACT_PATTERN_RETAINED",
            },
            {
                "claim": "the intended Java mechanic matches the proposed detailed behavior",
                "classification": "unknown",
                "confidence": 0.0,
                "evidence_refs": [],
                "rationale": "No authorized Java evidence record is registered.",
                "rights_disposition": "RIGHTS_BLOCKED_DIRECT_RECONSTRUCTION",
            },
        ],
        "evidence_gaps": missing,
        "parts": [_part(feature_id, category) for category in DECOMPOSITION_CATEGORIES],
        "expressions": _expressions(feature_id),
        "rights_materials": [{
            "material_id": f"source-{feature_id}-unregistered",
            "material_type": "unknown",
            "ownership": "UNKNOWN",
            "analysis_permission": "UNKNOWN",
            "commercial_permission": "UNKNOWN",
            "marketplace_permission": "UNKNOWN",
            "direct_reuse": "PROHIBITED",
            "clean_room_abstract_mechanic_extraction": "PENDING_AUTHORIZED_EVIDENCE",
        }],
        "runtime": _runtime(feature_id),
        "ps4_cost": {
            dimension: {
                "value": int(plan_costs.get(dimension, PS4_VALUES[feature_id][index])),
                "unit": "uncalibrated_planning_point",
                "classification": "ESTIMATED",
                "confidence": "LOW",
                "basis": "synthetic existing forest planner allocation; not measured feature evidence",
            }
            for index, dimension in enumerate(PS4_DIMENSIONS)
        },
        "artifacts": _artifacts(feature_id),
        "qualification": _qualification(feature_id),
        "transformation_summary": {
            "role": ROLE[feature_id],
            "strategy": "clean-room Bedrock-native reconstruction with original expression",
            "fidelity": "UNKNOWN_PENDING_EVIDENCE",
            "production_state": "NOT_STARTED",
        },
        "readiness": {
            "status": "MORE_EVIDENCE_REQUIRED",
            "blocking_findings": [*missing, *(
                ["current plan requires Gloamwing Stalker and Barkguard Charm before Thornwarden"]
                if dependency_block else []
            )],
            "required_remediation": [
                "register authorized Java evidence and material-level rights",
                "rebuild evidence-backed Gameplay Intent IR",
                "approve detailed clean-room strategy before production",
            ],
            "evidence_confidence": "LOW",
            "rights_status": "UNREGISTERED_SOURCE_MATERIALS",
            "autonomous_production_may_proceed": False,
        },
        "open_questions": [
            f"What authorized Java evidence establishes {feature_id}'s exact behavior and dependencies?",
            "Which source materials, if any, have commercial Marketplace adaptation permission?",
            "Which proposed behavior parameters should be retained, redesigned, or omitted?",
            "What named four-player concurrency envelope must the PS4 model qualify?",
        ],
    }


def build_forest_wave_1_spec(root: Path) -> dict[str, Any]:
    plan_path = root / "production/planning/controlled-chaos-forest/controlled-chaos-forest-production-plan.json"
    package = json.loads(plan_path.read_text(encoding="utf-8"))
    wave_plan = package["components"]["production-wave-plan.json"]
    element_rows = {
        row["product_id"]: row
        for row in package["components"]["forest-elements.json"]
    }
    features = [
        _feature(feature_id, element_rows[feature_id]["ps4_cost_dimensions"])
        for feature_id in FEATURE_ORDER
    ]
    bramblehorn_cost = {
        dimension: {
            "value": int(element_rows["bramblehorn"]["ps4_cost_dimensions"][dimension]),
            "unit": "planning_proxy_point",
            "classification": "MEASURED_FROM_EXISTING_EVIDENCE" if dimension in {
                "active_entities", "pathfinding_pressure", "projectiles", "particles",
                "texture_memory", "geometry_complexity", "animation_controller_complexity",
                "persistence_growth", "script_tick_workload",
            } else "ESTIMATED",
            "confidence": "MEDIUM",
            "basis": "Bramblehorn checked-in asset/cost/BDS records; not physical PS4 evidence",
        } for dimension in PS4_DIMENSIONS
    }
    output_root = "analysis/reconstruction-waves/forest-wave-1"
    return {
        "schema_version": "1.0.0",
        "wave_id": "forest-wave-1",
        "diagnostic_only": True,
        "execution_authorized": False,
        "features": features,
        "dependency_nodes": ["gloamwing_stalker", "barkguard_charm"],
        "dependencies": [
            {"source": "mossback_forager", "target": "bramblehorn", "type": "may_reuse_template", "required": False, "dimensions": ["production", "qualification"], "failure_behavior": "author independent rig and harness"},
            {"source": "thornwarden_elite", "target": "bramblehorn", "type": "may_reuse_template", "required": False, "dimensions": ["production"], "failure_behavior": "author independent rig; never reuse identity"},
            {"source": "thornwarden_elite", "target": "signal_ruin", "type": "must_exist", "required": True, "dimensions": ["runtime"], "failure_behavior": "elite activation remains unavailable"},
            {"source": "thornwarden_elite", "target": "gloamwing_stalker", "type": "must_be_qualified", "required": True, "dimensions": ["production", "qualification"], "failure_behavior": "elite production remains dependency-blocked"},
            {"source": "thornwarden_elite", "target": "barkguard_charm", "type": "must_be_qualified", "required": True, "dimensions": ["production", "qualification"], "failure_behavior": "elite production remains dependency-blocked"},
            {"source": "forest_attunement", "target": "thornwarden_elite", "type": "may_reward", "required": True, "dimensions": ["runtime", "unlock"], "failure_behavior": "attunement cannot be granted"},
            {"source": "sporefall_event", "target": "forest_attunement", "type": "must_be_unlocked", "required": True, "dimensions": ["runtime", "unlock"], "failure_behavior": "event stays ineligible"},
            {"source": "renewed_trail_loop", "target": "sporefall_event", "type": "may_reward", "required": True, "dimensions": ["runtime", "unlock"], "failure_behavior": "revisit loop remains unavailable"},
            {"source": "sporefall_event", "target": "mossback_forager", "type": "may_spawn", "required": False, "dimensions": ["runtime"], "failure_behavior": "omit creature from event table"},
            {"source": "sporefall_event", "target": "bramblehorn", "type": "may_spawn", "required": False, "dimensions": ["runtime"], "failure_behavior": "omit creature from event table"},
        ],
        "evidence_policy": {
            "authorized_java_evidence_found": False,
            "planning_contracts_are_java_evidence": False,
            "existing_bedrock_benchmarks_are_java_evidence": False,
            "source_expression_production_access": "PROHIBITED",
            "missing_evidence_behavior": "FAIL_CLOSED",
        },
        "rights_strategy": {
            "mode": "clean_room_originalization",
            "direct_source_expression_reuse": "prohibited",
            "material_ledger_status": "NO_FEATURE_SOURCE_MATERIALS_REGISTERED",
            "legal_clearance_implied": False,
        },
        "ps4": {
            "current_plan_total_units": wave_plan["authoritative_scope"]["current"],
            "planning_ceiling_units": wave_plan["authoritative_scope"]["planning_ceiling"],
            "hard_ceiling_units": wave_plan["authoritative_scope"]["hard_ceiling"],
            "protected_reserve_units": wave_plan["authoritative_scope"]["protected_minimum"],
            "current_reserve_units": wave_plan["authoritative_scope"]["reserve"],
            "selected_scope_units_already_in_plan": sum(SCOPE.values()),
            "double_charge_selected_scope": False,
            "bramblehorn_cost": bramblehorn_cost,
            "hard_caps": wave_plan["hard_caps"],
            "required_reserves": wave_plan["required_reserves"],
            "connected_additive_model_valid": False,
            "aggregation_remediation": [
                "SUM_STATIC package residency with template deduplication",
                "SUM_CONCURRENT named exploration, ruin, event, and four-player scenes",
                "MAX_MUTUALLY_EXCLUSIVE only with an enforced elite/event lock",
                "CARDINALITY_BOUND world + capped structures + four players",
                "PHYSICAL_ONLY for client memory and frame pacing",
            ],
        },
        "diagnostic_output_paths": [
            f"{output_root}/{name}" for name in (
                "forest-wave-1-evidence-inventory.json",
                "forest-wave-1-feature-decomposition.json",
                "forest-wave-1-transformation-plan.json",
                "forest-wave-1-expression-disposition.json",
                "forest-wave-1-dependency-graph.json",
                "forest-wave-1-rights-report.json",
                "forest-wave-1-runtime-architecture-plan.json",
                "forest-wave-1-ps4-cost-preview.json",
                "forest-wave-1-artifact-manifest-preview.json",
                "forest-wave-1-qualification-plan.json",
                "forest-wave-1-open-questions.json",
                "forest-wave-1-execution-readiness.json",
                "forest-wave-1-execution-manifest.json",
            )
        ],
        "protected_custom_regions": [
            "custom/scripts", "custom/entities", "custom/models", "custom/assets",
        ],
        "planned_blockbench_operations": [
            "author original Mossback model/texture/rig/animations from approved clean-room contract",
            "author original Resonance Sling held/attachable model, texture, animations, and locators",
            "author original Thornwarden visual differentiation and encounter animations",
            "native save/reopen/export and visual evidence for every authored asset",
        ],
        "connected_wave_checks": [
            "all six systems enabled together", "vanilla Minecraft remains functional",
            "no identifier collision", "no competing global state",
            "no unbounded spawning", "no duplicate rewards",
            "no stale encounter state", "four-player worst-credible scene",
            "endurance and restart repeat", "cleanup to zero",
        ],
        "physical_checks": [
            "PS4 Realm installation/delivery", "controller-only progression",
            "frame pacing and memory", "split-screen", "multiplayer/reconnect",
            "persistence", "Marketplace submission and review",
        ],
        "known_limitations": [
            "no authorized Java evidence is registered for the six features",
            "non-Bramblehorn dimension values are synthetic low-confidence planner estimates",
            "connected static/runtime/persistent aggregation is not calibrated",
            "desktop and physical PS4 behavior is untested",
            "Thornwarden current plan depends on out-of-slice Gloamwing Stalker and Barkguard Charm",
        ],
        "rights_restrictions": [
            "no source name, branding, model, texture, animation, audio, lore, layout, or reward identity may enter production",
            "abstract mechanic extraction remains pending authorized evidence",
            "all final expression must be original or separately Marketplace-cleared",
        ],
        "rollback_point": {
            "git_commit": "b910c8d29033434aed988202be46d8c8907e28e3",
            "forest_plan_component_hash": package["component_hashes"]["production-wave-plan.json"],
            "forest_package_sha256": package["package_sha256"],
        },
        "expected_package_outputs": [
            "dist/marketplace-candidate/forest-wave-1.mcaddon",
            "dist/test-world/forest-wave-1.mcworld",
        ],
        "maximum_autonomous_repair_iterations": 3,
        "stop_conditions": [
            "authorized evidence or rights record is missing",
            "source expression contamination is detected",
            "stable Bedrock mapping is unresolved",
            "PS4 hard cap or protected reserve fails",
            "production would require preview-only API",
            "physical/client evidence is being overstated",
        ],
        "failure_conditions": [
            "execution_authorized differs from false",
            "diagnostic writes target production/runtime/world paths",
            "dependency cycle is present",
            "artifact preview path escapes repository",
            "manifest omits a required gate or cleanup path",
        ],
    }


def _write_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _markdown(reports: Mapping[str, Mapping[str, Any]]) -> str:
    evidence = reports["forest-wave-1-evidence-inventory.json"]
    transform = reports["forest-wave-1-transformation-plan.json"]
    dependencies = reports["forest-wave-1-dependency-graph.json"]
    costs = reports["forest-wave-1-ps4-cost-preview.json"]
    readiness = reports["forest-wave-1-execution-readiness.json"]
    manifest = reports["forest-wave-1-execution-manifest.json"]
    lines = [
        "# Forest Wave 1 transformation diagnosis",
        "",
        "Status: **DIAGNOSTIC_ONLY — EXECUTION_NOT_AUTHORIZED**",
        "",
        "This read-only planning diagnosis stops before Blockbench authoring, BP/RP",
        "generation, runtime gameplay, structure creation, packaging, or world mutation.",
        "",
        "## Evidence result",
        "",
        "No authorized Java feature evidence or material-level source-rights records",
        "were found for the six selected features. Existing records prove only the",
        "checked-in clean-room roles, planning scope, and generic safety constraints.",
        "They do not prove source mechanics or authorize production.",
        "",
    ]
    for row in evidence["features"]:
        lines.extend([
            f"### {row['feature_id']}",
            "",
            f"- Evidence found: internal planning contracts only ({len(row['evidence'])} record).",
            f"- Evidence gaps: {'; '.join(row['evidence_gaps'])}.",
            "- Direct Java reconstruction: blocked pending authorized evidence and rights.",
            "",
        ])
    lines.extend([
        "## Proposed transformations",
        "",
        "These are Bedrock-native proposals, not observed Java behavior.",
        "",
    ])
    for row in transform["features"]:
        counts: dict[str, int] = {}
        for part in row["parts"]:
            counts[part["disposition"]] = counts.get(part["disposition"], 0) + 1
        summary = ", ".join(f"{key} {counts[key]}" for key in sorted(counts))
        lines.extend([
            f"- **{row['feature_id']}**: {row['summary']['strategy']}; {summary}.",
        ])
    lines.extend([
        "",
        "## Dependency result",
        "",
        f"Required dependency cycle check: **{dependencies['cycle_check']}**.",
        "Thornwarden remains dependent on Signal Ruin plus the out-of-slice",
        "Gloamwing Stalker and Barkguard Charm under the current plan.",
        "",
        "## PS4 planning preview",
        "",
        f"- Current plan: {costs['current_plan_total_units']}/{costs['hard_ceiling_units']} units.",
        f"- Planning ceiling: {costs['planning_ceiling_units']}.",
        f"- Protected reserve: {costs['protected_reserve_units']}; current reserve: {costs['current_reserve_units']}.",
        "- The six selected features already occupy 38 units inside the current 62-unit plan; no scope is double-charged.",
        "- Non-Bramblehorn dimension values are low-confidence synthetic estimates.",
        "- The naive connected upper bound is not a valid concurrency model and",
        "  exceeds several effective caps. Named static, concurrent, mutually",
        "  exclusive, cardinality-bound, and physical-only profiles are required.",
        "- Reserve consumption proposed: **false**.",
        "- Physical PS4 compatibility claimed: **false**.",
        "",
        "## Readiness",
        "",
    ])
    for row in readiness["features"]:
        lines.extend([
            f"- **{row['feature_id']}**: `{row['status']}` — autonomous production: `{str(row['autonomous_production_may_proceed']).lower()}`.",
        ])
    lines.extend([
        "",
        f"Aggregate readiness: **{readiness['aggregate']['status']}**.",
        "",
        "Production remains stopped until authorized Java evidence and material",
        "rights are registered, evidence-backed Gameplay Intent IR is rebuilt,",
        "dependencies are resolved, and connected PS4 budgets are calibrated.",
        "",
        "## Approval manifest",
        "",
        f"`execution_authorized` is `{str(manifest['execution_authorized']).lower()}` and",
        "cannot be changed by the diagnostic operation. The deterministic JSON",
        "manifest lists every proposed file, original asset, runtime system, test,",
        "stop condition, failure condition, rollback point, and remaining physical gate.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "mccompiler diagnose-reconstruction-wave \\",
        "  --project . \\",
        "  --dry-run \\",
        "  --json",
        "```",
        "",
        "A successful diagnosis with blocking readiness returns exit code 3. Invalid",
        "input or a policy violation returns exit code 2. The operation may write",
        "only this analysis bundle and this document.",
        "",
    ])
    return "\n".join(lines)


def render_forest_wave_1_diagnosis(root: Path) -> tuple[dict[str, dict[str, Any]], list[Path]]:
    root = root.resolve()
    required_markers = (
        root / "pyproject.toml",
        root / "src/mccompiler",
        root / "production/planning/controlled-chaos-forest/controlled-chaos-forest-production-plan.json",
    )
    if not all(path.exists() for path in required_markers):
        raise ValueError("authoritative compiler repository markers are missing")
    reports = diagnose_reconstruction_wave(build_forest_wave_1_spec(root))
    output_root = root / "analysis/reconstruction-waves/forest-wave-1"
    expected = {output_root / filename for filename in DIAGNOSTIC_REPORT_FILENAMES}
    markdown_path = root / "docs/forest-wave-1-transformation-diagnosis.md"
    for path in [*expected, markdown_path]:
        resolved = path.resolve()
        if root not in resolved.parents:
            raise ValueError(f"diagnostic path escapes repository: {path}")
        if resolved.parts[:len(root.parts) + 1] not in {
            (*root.parts, "analysis"),
            (*root.parts, "docs"),
        }:
            raise ValueError(f"diagnostic write is outside analysis/docs: {path}")
    for filename in DIAGNOSTIC_REPORT_FILENAMES:
        _write_atomic(
            output_root / filename,
            json.dumps(reports[filename], indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        )
    _write_atomic(markdown_path, _markdown(reports))
    return reports, [*(output_root / filename for filename in DIAGNOSTIC_REPORT_FILENAMES), markdown_path]
