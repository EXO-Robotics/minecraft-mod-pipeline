from __future__ import annotations

import unittest

from mccompiler.context_requirements import (
    ACTION_CONTEXT,
    CONDITION_CONTEXT,
    TRIGGER_CONTEXT,
    behavior_context_requirements,
    context_is_complete,
    validate_context_contracts,
)
from mccompiler.semantics import ACTIONS, CONDITIONS, TRIGGERS


def behavior(trigger: str, action: dict[str, object], *, owner_kind: str = "object") -> dict[str, object]:
    return {
        "id": f"fixture:{trigger}/{action['type']}",
        "owner": {"kind": owner_kind, "identifier": "fixture:owner"},
        "trigger": {"type": trigger},
        "conditions": [],
        "actions": [action],
    }


class ContextRequirementTests(unittest.TestCase):
    def test_registry_covers_every_behavior_ir_vocabulary_element(self) -> None:
        self.assertEqual(TRIGGERS, set(TRIGGER_CONTEXT))
        self.assertEqual(CONDITIONS, set(CONDITION_CONTEXT))
        self.assertEqual(ACTIONS, set(ACTION_CONTEXT))

    def assertRequires(self, row: dict[str, object], *names: str) -> None:
        requirements = behavior_context_requirements(row)  # type: ignore[arg-type]
        self.assertTrue(set(names) <= requirements)
        self.assertFalse(context_is_complete(requirements, set(requirements) - set(names)))  # type: ignore[arg-type]

    def assertDoesNotRequire(self, row: dict[str, object], *names: str) -> None:
        self.assertFalse(set(names) & behavior_context_requirements(row))  # type: ignore[arg-type]

    def test_actor_owned_projectile_requires_actor(self) -> None:
        self.assertRequires(behavior("item_use", {"type": "spawn_projectile"}), "actor")

    def test_owner_independent_spawn_allows_missing_actor(self) -> None:
        row = behavior("scheduled_tick", {"type": "spawn_entity"})
        self.assertDoesNotRequire(row, "actor")
        self.assertRequires(row, "dimension")
        requirements = behavior_context_requirements(row)  # type: ignore[arg-type]
        self.assertTrue(context_is_complete(requirements, set(requirements)))

    def test_player_cooldown_and_state_require_actor(self) -> None:
        self.assertRequires(behavior("scheduled_tick", {"type": "start_cooldown"}), "actor")
        self.assertRequires(
            behavior("scheduled_tick", {"type": "update_persistent_state"}, owner_kind="player_state"),
            "actor",
        )

    def test_item_mutation_routes_to_block_or_actor_owner(self) -> None:
        block_owned = behavior("scheduled_tick", {"type": "remove_item"})
        block_owned["owner"] = {"kind": "block", "identifier": "fixture:machine"}
        self.assertRequires(block_owned, "block")
        self.assertDoesNotRequire(block_owned, "actor")
        self.assertRequires(behavior("item_use", {"type": "remove_item"}), "actor")

    def test_form_and_actor_effect_require_actor(self) -> None:
        self.assertRequires(behavior("scheduled_tick", {"type": "open_interaction_ui"}), "actor")
        self.assertRequires(behavior("entity_hurt", {"type": "apply_effect", "target": "actor"}), "actor")

    def test_target_only_effect_allows_missing_actor(self) -> None:
        row = behavior("entity_hurt", {"type": "apply_effect", "target": "target"})
        self.assertRequires(row, "target")
        self.assertDoesNotRequire(row, "actor")

    def test_global_sound_particle_and_schedule_allow_missing_actor(self) -> None:
        for action in (
            {"type": "play_sound"},
            {"type": "spawn_particles"},
            {"type": "schedule_delayed_action"},
        ):
            with self.subTest(action=action["type"]):
                self.assertDoesNotRequire(behavior("scheduled_tick", action), "actor")

    def test_target_damage_requires_target(self) -> None:
        self.assertRequires(behavior("scheduled_tick", {"type": "damage", "target": "target"}), "target")

    def test_block_mutation_requires_block(self) -> None:
        self.assertRequires(behavior("scheduled_tick", {"type": "set_block"}), "block")

    def test_projectile_impact_requires_projectile(self) -> None:
        self.assertRequires(
            behavior("projectile_impact", {"type": "damage", "target": "target"}),
            "projectile",
            "target",
        )

    def test_projectile_block_impact_is_independent(self) -> None:
        row = behavior("projectile_block_impact", {"type": "set_block"})
        self.assertRequires(row, "projectile", "block")
        self.assertDoesNotRequire(row, "target")

    def test_nested_actions_and_conditions_are_checked(self) -> None:
        row = behavior(
            "scheduled_tick",
            {
                "type": "schedule_delayed_action",
                "actions": [{"type": "damage", "target": "target"}],
                "condition": {"type": "cooldown_ready"},
            },
        )
        self.assertRequires(row, "actor", "target")

    def test_unknown_contract_elements_fail_closed(self) -> None:
        for row, message in (
            (behavior("unknown", {"type": "play_sound"}), "trigger"),
            (behavior("scheduled_tick", {"type": "unknown"}), "action"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                validate_context_contracts([row])  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
