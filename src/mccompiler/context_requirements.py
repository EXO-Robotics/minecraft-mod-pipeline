from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal


ContextName = Literal["actor", "target", "block", "item", "projectile", "dimension", "event_source"]


@dataclass(frozen=True)
class ContextContract:
    required: frozenset[ContextName] = frozenset()


TRIGGER_CONTEXT: dict[str, ContextContract] = {
    "item_use": ContextContract(frozenset({"item", "event_source"})),
    "item_use_on_block": ContextContract(frozenset({"block", "item", "event_source"})),
    "item_used_on_entity": ContextContract(frozenset({"item", "target", "event_source"})),
    "block_interact": ContextContract(frozenset({"block", "event_source"})),
    "block_break": ContextContract(frozenset({"block", "event_source"})),
    "entity_hit": ContextContract(frozenset({"actor", "target", "event_source"})),
    "entity_hurt": ContextContract(frozenset({"target", "event_source"})),
    "entity_death": ContextContract(frozenset({"target", "event_source"})),
    "entity_spawn": ContextContract(frozenset({"target", "event_source"})),
    "player_join": ContextContract(frozenset({"actor", "event_source"})),
    "player_spawn": ContextContract(frozenset({"actor", "event_source"})),
    "player_death": ContextContract(frozenset({"target", "event_source"})),
    "block_place": ContextContract(frozenset({"actor", "block", "item", "event_source"})),
    "projectile_impact": ContextContract(frozenset({"projectile", "target", "event_source"})),
    "projectile_block_impact": ContextContract(frozenset({"projectile", "block", "event_source"})),
    "object_tick": ContextContract(frozenset({"event_source"})),
    "scheduled_tick": ContextContract(frozenset({"event_source"})),
    "processing_complete": ContextContract(frozenset({"event_source"})),
    "state_transition": ContextContract(frozenset({"event_source"})),
}

CONDITION_CONTEXT: dict[str, ContextContract] = {
    "player_sneaking": ContextContract(frozenset({"actor"})),
    "held_item_match": ContextContract(frozenset({"item"})),
    "equipped_armor_match": ContextContract(frozenset({"actor"})),
    "target_entity_match": ContextContract(frozenset({"target"})),
    "block_match": ContextContract(frozenset({"block"})),
    "dimension_match": ContextContract(frozenset({"dimension"})),
    "random_probability": ContextContract(),
    "cooldown_ready": ContextContract(frozenset({"actor"})),
    "state_comparison": ContextContract(),
    "health_threshold": ContextContract(frozenset({"target"})),
    "distance_threshold": ContextContract(frozenset({"actor", "target"})),
    "time_or_tick": ContextContract(frozenset({"dimension"})),
    "permission_or_ownership": ContextContract(frozenset({"actor"})),
    "client_server_side": ContextContract(),
    "configuration_flag": ContextContract(),
    "dependency_presence": ContextContract(),
}

ACTION_CONTEXT: dict[str, ContextContract] = {
    "spawn_entity": ContextContract(frozenset({"dimension"})),
    "spawn_projectile": ContextContract(frozenset({"actor", "dimension"})),
    "remove_entity": ContextContract(),
    "create_explosion": ContextContract(frozenset({"dimension"})),
    "damage": ContextContract(),
    "heal": ContextContract(),
    "apply_effect": ContextContract(),
    "remove_effect": ContextContract(),
    "play_sound": ContextContract(frozenset({"dimension"})),
    "spawn_particles": ContextContract(frozenset({"dimension"})),
    "set_block": ContextContract(frozenset({"block"})),
    "replace_block": ContextContract(frozenset({"block"})),
    "break_block": ContextContract(frozenset({"block"})),
    "place_structure": ContextContract(frozenset({"dimension"})),
    "teleport": ContextContract(frozenset({"actor", "dimension"})),
    "apply_velocity": ContextContract(frozenset({"actor"})),
    "modify_item_durability": ContextContract(frozenset({"item"})),
    "add_item": ContextContract(),
    "remove_item": ContextContract(),
    "update_persistent_state": ContextContract(),
    "start_cooldown": ContextContract(frozenset({"actor"})),
    "set_entity_phase": ContextContract(),
    "trigger_behavior": ContextContract(),
    "send_player_feedback": ContextContract(frozenset({"actor"})),
    "open_interaction_ui": ContextContract(frozenset({"actor"})),
    "schedule_delayed_action": ContextContract(),
}

TARGETED_ACTIONS = frozenset({"remove_entity", "damage", "heal", "apply_effect", "remove_effect", "set_entity_phase"})


def _action_requirements(action: dict[str, Any]) -> set[ContextName]:
    kind = str(action.get("type"))
    if kind not in ACTION_CONTEXT:
        raise ValueError(f"unmapped context requirements for action: {kind}")
    required: set[ContextName] = set(ACTION_CONTEXT[kind].required)
    if kind in TARGETED_ACTIONS:
        recipient = action.get("target")
        if recipient == "actor":
            required.add("actor")
        elif recipient == "target":
            required.add("target")
        elif recipient not in {None, "actor", "target"}:
            raise ValueError(f"unmapped action target: {recipient}")
    nested_condition = action.get("condition")
    if isinstance(nested_condition, dict):
        condition_kind = str(nested_condition.get("type"))
        if condition_kind not in CONDITION_CONTEXT:
            raise ValueError(f"unmapped context requirements for condition: {condition_kind}")
        required.update(CONDITION_CONTEXT[condition_kind].required)
    for nested in action.get("actions", []):
        if not isinstance(nested, dict):
            raise ValueError(f"invalid nested action in {kind}")
        required.update(_action_requirements(nested))
    return required


def behavior_context_requirements(behavior: dict[str, Any]) -> frozenset[ContextName]:
    trigger = str((behavior.get("trigger") or {}).get("type"))
    if trigger not in TRIGGER_CONTEXT:
        raise ValueError(f"unmapped required trigger context: {trigger}")
    required: set[ContextName] = set(TRIGGER_CONTEXT[trigger].required)
    owner = behavior.get("owner") or {}
    if owner.get("kind") == "player_state":
        required.add("actor")
    for condition in behavior.get("conditions", []):
        kind = str(condition.get("type"))
        if kind not in CONDITION_CONTEXT:
            raise ValueError(f"unmapped context requirements for condition: {kind}")
        required.update(CONDITION_CONTEXT[kind].required)
    for action in behavior.get("actions", []):
        required.update(_action_requirements(action))
        if action.get("type") in {"add_item", "remove_item"}:
            if owner.get("kind") == "block":
                required.add("block")
            elif action.get("target") == "world":
                required.add("dimension")
            else:
                required.add("actor")
    return frozenset(required)


def validate_context_contracts(behaviors: list[dict[str, Any]]) -> None:
    for behavior in behaviors:
        behavior_context_requirements(behavior)


def context_is_complete(requirements: frozenset[ContextName], present: set[ContextName]) -> bool:
    return requirements <= present


def javascript_context_contract(behaviors: list[dict[str, Any]]) -> str:
    contracts = {
        str(behavior.get("id")): sorted(behavior_context_requirements(behavior))
        for behavior in sorted(behaviors, key=lambda row: str(row.get("id")))
    }
    encoded = json.dumps(contracts, sort_keys=True, separators=(",", ":"))
    return (
        f"const contextRequirements={encoded};\n"
        "const hasContext=(name,c)=>name==='actor'?!!(c.source||c.player||c.damagingEntity):"
        "name==='target'?!!(c.hitEntity||c.hurtEntity||c.deadEntity||c.target||c.entity):"
        "name==='block'?!!c.block:name==='item'?!!c.itemStack:name==='projectile'?!!c.projectile:"
        "name==='dimension'?!!(c.dimension||c.block?.dimension||c.source?.dimension||c.player?.dimension||"
        "c.damagingEntity?.dimension||c.hitEntity?.dimension||c.hurtEntity?.dimension||c.deadEntity?.dimension||"
        "c.target?.dimension||c.entity?.dimension):name==='event_source'?!!c.eventSource:false;\n"
        "const contextComplete=(b,c)=>(contextRequirements[b.id]||[]).every(name=>hasContext(name,c));\n"
    )
