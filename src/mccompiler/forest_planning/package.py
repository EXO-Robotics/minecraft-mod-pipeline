from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .acceptance import AcceptanceGraph, AcceptanceNode, EvidenceState
from .waves import Budget, DIMENSIONS, ForestElement, ProductionWavePlanner


NODE_IDS = (
    "entry_motivation", "environmental_identity", "navigation_landmark",
    "baseline_regional_creature", "secondary_regional_creature",
    "escalating_regional_threat", "equipment_upgrade_one",
    "equipment_upgrade_two", "elite_encounter", "distinctive_reward",
    "progression_unlock", "bounded_chaos_event", "reason_to_revisit",
    "repeatable_reward_loop", "multiplayer_safe_state", "restart_safe_state",
    "cleanup_complete", "worst_credible_load_qualified",
)
MANDATORY = frozenset({
    "entry_motivation", "progression_unlock", "multiplayer_safe_state",
    "restart_safe_state", "cleanup_complete", "worst_credible_load_qualified",
})
ELEMENT_NODES = {
    "signal_ruin": ("entry_motivation", "navigation_landmark"),
    "bramblehorn": ("environmental_identity", "secondary_regional_creature", "worst_credible_load_qualified"),
    "mossback_forager": ("baseline_regional_creature",),
    "gloamwing_stalker": ("escalating_regional_threat",),
    "resonance_sling": ("equipment_upgrade_one",),
    "barkguard_charm": ("equipment_upgrade_two",),
    "thornwarden_elite": ("elite_encounter",),
    "forest_attunement": ("distinctive_reward", "progression_unlock", "restart_safe_state"),
    "sporefall_event": ("bounded_chaos_event", "cleanup_complete"),
    "renewed_trail_loop": ("reason_to_revisit", "repeatable_reward_loop", "multiplayer_safe_state"),
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _costs(index: int, scope_units: int, *, bramblehorn: bool) -> dict[str, int]:
    if bramblehorn:
        return {
            "script_tick_workload": 0, "active_entities": 20,
            "pathfinding_pressure": 20, "projectiles": 0, "particles": 0,
            "texture_memory": 1, "geometry_complexity": 18,
            "animation_controller_complexity": 15, "persistence_growth": 0,
            "multiplayer_multiplier": 2, "cleanup_latency": 20,
            "worst_credible_scene": 20,
        }
    return {
        dimension: min(scope_units + ((index + offset) % 3), cap)
        for offset, (dimension, cap) in enumerate(zip(
            DIMENSIONS, (12, 8, 8, 6, 8, 8, 12, 8, 6, 8, 8, 14),
        ))
    }


def build_package(
    contract: Mapping[str, Any],
    *,
    bramblehorn_registry: Mapping[str, Any],
    bramblehorn_readiness: Mapping[str, Any],
    bramblehorn_cost: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = contract["elements"]
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError("forest contract requires exactly 10 product elements")
    budget_raw = contract["budget"]
    budget = Budget(budget_raw["hard_caps"], budget_raw["reserves"])
    elements: list[ForestElement] = []
    element_documents: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        element_id = str(raw["id"])
        is_bramblehorn = element_id == "bramblehorn"
        evidence = (
            EvidenceState.SERVER_QUALIFIED
            if is_bramblehorn else EvidenceState.CONTRACT_ONLY
        )
        costs = _costs(index, int(raw["scope_units"]), bramblehorn=is_bramblehorn)
        contract_ref = (
            "prototypes/blockbench/bramblehorn/asset-manifest.json"
            if is_bramblehorn
            else f"production/planning/controlled-chaos-forest/contracts/{element_id}/clean-room-design.json"
        )
        qualification_ref = (
            "prototypes/blockbench/bramblehorn/readiness-matrix.json"
            if is_bramblehorn
            else f"production/planning/controlled-chaos-forest/contracts/{element_id}/qualification.json"
        )
        element = ForestElement(
            element_id, int(raw["priority"]), costs, int(raw["scope_units"]),
            tuple(raw["dependencies"]), evidence, contract_ref, qualification_ref,
        )
        elements.append(element)
        element_documents.append({
            "product_id": element_id,
            "abstract_gameplay_role": {
                "bramblehorn": "bounded hostile regional creature",
                "mossback_forager": "baseline passive regional creature",
                "gloamwing_stalker": "escalating nocturnal regional threat",
                "resonance_sling": "first unusual ranged equipment upgrade",
                "barkguard_charm": "defensive equipment upgrade",
                "signal_ruin": "discoverable forest landmark and encounter initializer",
                "thornwarden_elite": "gated elite encounter",
                "forest_attunement": "persistent distinctive progression unlock",
                "sporefall_event": "bounded deterministic chaos event",
                "renewed_trail_loop": "repeatable revisit and reward loop",
            }[element_id],
            "clean_room_design_contract": contract_ref,
            "gameplay_intent_ir_ref": (
                "prototypes/blockbench/bramblehorn/asset-manifest.json"
                if is_bramblehorn
                else f"analysis/gameplay-intent/controlled-chaos-forest/{element_id}.json"
            ),
            "rights_disposition": "ORIGINAL_AUTHORED"
            if is_bramblehorn else "CLEAN_ROOM_CONTRACT_PENDING_IMPLEMENTATION",
            "originality_requirements": [
                "original name, silhouette, textures, sounds, and authored behavior",
                "no copied third-party expression or source assets",
            ],
            "similarity_screening_requirement": "REQUIRED_BEFORE_STATIC_QUALIFICATION",
            "experience_nodes_satisfied": list(ELEMENT_NODES[element_id]),
            "progression_dependencies": list(element.dependencies),
            "asset_contract": (
                "prototypes/blockbench/bramblehorn/asset-manifest.json"
                if is_bramblehorn
                else f"production/planning/controlled-chaos-forest/contracts/{element_id}/asset.json"
            ),
            "behavior_contract": (
                "prototypes/blockbench/bramblehorn/addon/behavior_pack/entities/bramblehorn.json"
                if is_bramblehorn
                else f"production/planning/controlled-chaos-forest/contracts/{element_id}/behavior.json"
            ),
            "structure_or_encounter_contract": (
                f"production/planning/controlled-chaos-forest/contracts/{element_id}/encounter.json"
                if element_id in {
                    "signal_ruin", "thornwarden_elite", "sporefall_event",
                    "renewed_trail_loop",
                } else None
            ),
            "production_effort": {
                "scope_units": element.scope_units,
                "classification": "AUTHORED_AND_SERVER_QUALIFIED"
                if is_bramblehorn else "PLANNING_ESTIMATE_ONLY",
            },
            "ps4_cost_dimensions": costs,
            "multiplayer_requirements": [
                "server-authoritative attribution",
                "no duplicate rewards under contention",
                "late join observes consistent shared state",
            ],
            "persistence_requirements": [
                "versioned state",
                "restart-safe restoration",
                "safe missing or corrupt-state fallback",
            ],
            "cleanup_policy": {
                "bounded": True,
                "require_zero_stale_entities": True,
                "receipt_required": True,
            },
            "qualification_plan": {
                "static": "REQUIRED",
                "stable_bds": "PASSED" if is_bramblehorn else "PENDING",
                "client": "PENDING",
                "physical_ps4": "PENDING",
                "reference": qualification_ref,
            },
            "current_status": evidence.value,
        })
    total_scope = sum(row.scope_units for row in elements)
    if total_scope != 62:
        raise ValueError("forest product elements must allocate exactly 62 scope units")

    element_by_node = {
        node_id: element_id
        for element_id, node_ids in ELEMENT_NODES.items()
        for node_id in node_ids
    }
    element_state = {row.element_id: row.evidence for row in elements}
    dependencies: dict[str, tuple[str, ...]] = {
        "entry_motivation": (),
        "environmental_identity": (),
        "navigation_landmark": ("entry_motivation",),
        "baseline_regional_creature": ("environmental_identity",),
        "secondary_regional_creature": ("environmental_identity",),
        "escalating_regional_threat": (
            "baseline_regional_creature", "secondary_regional_creature",
        ),
        "equipment_upgrade_one": ("entry_motivation",),
        "equipment_upgrade_two": ("equipment_upgrade_one",),
        "elite_encounter": (
            "escalating_regional_threat", "equipment_upgrade_two",
        ),
        "distinctive_reward": ("elite_encounter",),
        "progression_unlock": ("distinctive_reward",),
        "bounded_chaos_event": ("progression_unlock",),
        "reason_to_revisit": ("bounded_chaos_event",),
        "repeatable_reward_loop": ("reason_to_revisit",),
        "multiplayer_safe_state": ("repeatable_reward_loop",),
        "restart_safe_state": ("progression_unlock",),
        "cleanup_complete": ("bounded_chaos_event",),
        "worst_credible_load_qualified": ("secondary_regional_creature",),
    }
    nodes = [
        AcceptanceNode(
            node_id, 100 if node_id in MANDATORY else 50,
            dependencies[node_id], element_state[element_by_node[node_id]],
            EvidenceState.SERVER_QUALIFIED, node_id in MANDATORY,
        )
        for node_id in NODE_IDS
    ]
    graph = AcceptanceGraph(nodes)
    graph_document = {
        "schema_version": "1.0.0",
        "nodes": [{
            "node_id": node.node_id,
            "weight": node.weight,
            "mandatory": node.mandatory,
            "acceptance_requirements": [
                f"qualify {node.node_id} at {node.required.value.lower()} or higher",
                *[f"accept dependency {dependency}" for dependency in node.dependencies],
            ],
            "implementation_refs": (
                ["prototypes/blockbench/bramblehorn/authoring-report.json"]
                if element_by_node[node.node_id] == "bramblehorn" else []
            ),
            "contract_refs": [
                next(
                    row["clean_room_design_contract"]
                    for row in element_documents
                    if row["product_id"] == element_by_node[node.node_id]
                )
            ],
            "evidence_refs": (
                [
                    "prototypes/blockbench/bramblehorn/asset-registry.json",
                    "prototypes/blockbench/bramblehorn/readiness-matrix.json",
                    "prototypes/blockbench/bramblehorn/qualification/stable-bds-result.json",
                ]
                if element_by_node[node.node_id] == "bramblehorn" else []
            ),
            "qualification_requirements": [
                "static qualification",
                "stable server qualification",
                "physical client qualification remains separately required",
            ],
            "current_status": {
                EvidenceState.PLANNED: "planned",
                EvidenceState.CONTRACT_ONLY: "contracted",
                EvidenceState.IMPLEMENTED: "implemented",
                EvidenceState.STATIC_QUALIFIED: "static_qualified",
                EvidenceState.SERVER_QUALIFIED: "server_qualified",
                EvidenceState.CLIENT_QUALIFIED: "client_qualified",
                EvidenceState.PHYSICAL_QUALIFIED: "physical_qualified",
            }[node.evidence],
            "confidence": "high"
            if node.evidence is EvidenceState.SERVER_QUALIFIED else "low",
            "blocking_findings": (
                ["physical client and PS4 qualification pending"]
                if node.evidence is EvidenceState.SERVER_QUALIFIED
                else ["implementation and qualification evidence pending"]
            ),
        } for node in nodes],
    }
    coverage = graph.coverage_report()
    wave_plan = ProductionWavePlanner(budget).plan(elements)
    bramble_asset = next(
        row for row in bramblehorn_registry["assets"]
        if row["asset_id"] == "ccoriginal:creature.bramblehorn"
    )
    evidence_document = {
        "bramblehorn": {
            "asset_id": bramble_asset["asset_id"],
            "runtime_identifier": bramble_asset["runtime_identifier"],
            "status": bramblehorn_readiness["status"],
            "gates": bramblehorn_readiness["gates"],
            "cost_classification": bramblehorn_cost["classification"],
            "references": {
                "asset_registry": "prototypes/blockbench/asset-registry.json",
                "authoring_operation": "author_blockbench_asset",
                "authoring_report": "prototypes/blockbench/bramblehorn/authoring-report.json",
                "geometry": "prototypes/blockbench/bramblehorn/bramblehorn.geo.json",
                "texture": "prototypes/blockbench/bramblehorn/bramblehorn_texture.png",
                "rig_and_locators": "prototypes/blockbench/bramblehorn/asset-manifest.json",
                "animations": "prototypes/blockbench/bramblehorn/addon/resource_pack/animations/bramblehorn.animation.json",
                "animation_controller": "prototypes/blockbench/bramblehorn/addon/resource_pack/animation_controllers/bramblehorn.animation_controllers.json",
                "behavior": "prototypes/blockbench/bramblehorn/addon/behavior_pack/entities/bramblehorn.json",
                "spawn": "prototypes/blockbench/bramblehorn/addon/behavior_pack/spawn_rules/bramblehorn.json",
                "loot": "prototypes/blockbench/bramblehorn/addon/behavior_pack/loot_tables/ccoriginal_cc/entities/bramblehorn.json",
                "stable_bds": "prototypes/blockbench/bramblehorn/qualification/stable-bds-result.json",
                "ps4_cost": "prototypes/blockbench/bramblehorn/cost-report.json",
                "readiness": "prototypes/blockbench/bramblehorn/readiness-matrix.json"
            },
            "pending_checks": [
                "BEDROCK_DESKTOP",
                "PERSISTENCE_MULTIPLAYER",
                "PS4_PHYSICAL"
            ],
            "physical_ps4": "PENDING"
        },
        "all_other_elements": "CONTRACT_ONLY",
    }
    components = {
        "experience-acceptance-graph.json": graph_document,
        "experience-coverage-report.json": coverage,
        "production-wave-plan.json": wave_plan,
        "forest-elements.json": element_documents,
        "evidence.json": evidence_document,
    }
    component_hashes = {name: sha(value) for name, value in sorted(components.items())}
    package = {
        "schema_version": "1.0.0", "seed": int(contract["seed"]),
        "components": components, "component_hashes": component_hashes,
        "package_sha256": sha(component_hashes),
    }
    errors: list[str] = []
    if wave_plan["deferred"]:
        errors.append("production plan has deferred elements")
    authoritative_scope = wave_plan.get("authoritative_scope")
    if not isinstance(authoritative_scope, Mapping):
        errors.append("authoritative scope is missing")
    elif authoritative_scope.get("reserve_consumed"):
        errors.append("protected reserve was consumed")
    validation = {
        "schema_version": "1.0.0", "valid": not errors, "errors": errors,
        "package_sha256": package["package_sha256"],
        "component_hashes": component_hashes,
    }
    return package, validation


def load_repository_package(root: Path, contract_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    def read(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain an object")
        return value
    return build_package(
        read(contract_path),
        bramblehorn_registry=read(root / "prototypes/blockbench/asset-registry.json"),
        bramblehorn_readiness=read(root / "prototypes/blockbench/bramblehorn/readiness-matrix.json"),
        bramblehorn_cost=read(root / "prototypes/blockbench/bramblehorn/cost-report.json"),
    )
