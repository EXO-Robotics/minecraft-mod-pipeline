from __future__ import annotations

from typing import Any


PATTERN_CATALOG_VERSION = "2026.07.22.1"


_PATTERNS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], str, str], ...] = (
    ("items/basic-content", "items", tuple(), tuple(), "inventory and hotbar", "data_driven_item"),
    ("weapons/projectile", "weapons", ("item_use",), ("spawn_projectile",), "item use", "stable_script_or_projectile_entity"),
    ("weapons/explosive-staff", "weapons", ("item_use",), ("spawn_projectile", "create_explosion"), "item use", "stable_script"),
    ("weapons/lightning", "weapons", ("item_use",), ("spawn_entity", "play_sound"), "item use", "stable_script"),
    ("tools/area-mining", "tools", ("block_break",), ("break_block", "modify_item_durability"), "hold tool and mine", "stable_script_bounded_queue"),
    ("abilities/teleport-item", "abilities", ("item_use",), ("teleport",), "item use", "stable_script"),
    ("abilities/summoning-item", "abilities", ("item_use",), ("spawn_entity",), "item use", "stable_script_or_entity_event"),
    ("armor/passive-set", "armor", ("scheduled_tick",), ("apply_effect",), "equip armor", "stable_script_staggered"),
    ("armor/active-ability", "armor", ("item_use",), ("apply_effect", "start_cooldown"), "sneak plus item use", "stable_script"),
    ("abilities/cooldown", "abilities", ("item_use",), ("start_cooldown",), "item use", "stable_script"),
    ("cooldowns/player-ability", "cooldowns", ("item_use",), ("start_cooldown",), "item use with visible feedback", "stable_script"),
    ("inventory/random-reward-block", "inventory", ("block_break",), ("add_item",), "break block", "loot_table_or_stable_script"),
    ("machines/processing", "machines", ("object_tick",), ("update_persistent_state", "add_item"), "interact with machine", "stable_script_bounded_registry"),
    ("machines/energy-like", "machines", ("object_tick",), ("update_persistent_state",), "controller form", "stable_script_bounded_registry"),
    ("world/crop-growth", "world", ("scheduled_tick",), ("set_block",), "plant and wait", "data_driven_or_stable_script"),
    ("entities/companion", "entities", ("entity_spawn",), ("send_player_feedback",), "entity interaction", "data_driven_entity"),
    ("vehicles/mount", "vehicles", ("entity_spawn",), ("apply_velocity",), "entity interaction", "data_driven_rideable"),
    ("bosses/multiphase", "bosses", ("state_transition",), ("set_entity_phase",), "combat", "entity_groups_and_stable_script"),
    ("transformations/selector", "transformations", ("state_transition",), ("open_interaction_ui", "set_entity_phase"), "controller form", "stable_script_and_attachments"),
    ("forms/key-binding-replacement", "forms", ("item_use",), ("trigger_behavior",), "item use or sneak plus use", "stable_script"),
    ("forms/java-gui-replacement", "forms", ("block_interact",), ("open_interaction_ui",), "ActionForm or ModalForm", "stable_server_ui"),
    ("world/dimension-approximation", "world", ("state_transition",), ("teleport", "place_structure"), "portal interaction", "structure_based_redesign"),
    ("world/portal-structure-transition", "world", ("block_interact",), ("teleport", "place_structure"), "portal interaction", "structure_based_redesign"),
    ("projectiles/basic", "projectiles", ("item_use",), ("spawn_projectile",), "item use", "projectile_entity"),
    ("effects/status", "effects", ("entity_hit",), ("apply_effect",), "combat", "stable_script_or_entity_component"),
    ("structures/place", "structures", ("player_join",), ("place_structure",), "world discovery", "stable_script_or_feature_rule"),
    ("spawning/custom-entity", "spawning", ("entity_spawn",), tuple(), "world discovery", "spawn_rules"),
    ("progression/player", "progression", ("item_use",), ("update_persistent_state", "send_player_feedback"), "item use", "dynamic_properties_versioned"),
)


def marketplace_patterns() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for identifier, family, triggers, actions, controller, strategy in _PATTERNS:
        records.append({
            "id": identifier,
            "family": family,
            "version": PATTERN_CATALOG_VERSION,
            "required_ir_shape": {"triggers": list(triggers), "actions": list(actions)},
            "marketplace_safe_strategies": [strategy],
            "controller_interaction_design": controller,
            "performance_implications": "bounded; measure entity density and script work for the selected strategy",
            "fidelity_expectations": {"gameplay": ">=0.90 when classified supported", "interaction": ">=0.90", "persistence": "1.0 when saved state is required"},
            "known_limitations": ["Requires mechanic-specific evidence and target validation; pattern selection alone is not proof"],
            "tests": [f"pattern:{identifier}:static", f"pattern:{identifier}:gameplay"],
            "example_output": {"classification": "MANUAL_REDESIGN_REQUIRED until strategy and evidence are accepted"},
        })
    return records


def pattern_families() -> set[str]:
    return {row["family"] for row in marketplace_patterns()}
