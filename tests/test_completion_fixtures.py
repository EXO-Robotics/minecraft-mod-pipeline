from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mccompiler.bedrock import compile_bedrock
from mccompiler.planner import plan_conversion
from mccompiler.planner import _database
from mccompiler.scan import scan_path
from mccompiler.validate import validate_output


FIXTURES = Path(__file__).parent / "fixtures"


class CompletionFixtureTests(unittest.TestCase):
    def test_every_effective_capability_has_complete_contract(self):
        required = {"capability_id", "bedrock_version", "status", "native", "scripted", "approximation_strategies", "required_modules", "performance_implications", "multiplayer_safety", "persistence_support", "known_limitations", "reference_implementation", "tests", "deprecation"}
        for identifier, capability in _database()["capabilities"].items():
            self.assertFalse(required - set(capability), (identifier, required - set(capability)))

    def test_representative_fixture_covers_completion_contract(self):
        ir = scan_path(FIXTURES / "representative_mod")
        plan = plan_conversion(ir)
        content = {row["kind"] for row in ir["content"]}
        self.assertTrue({"item", "block", "recipe", "loot_table", "sound", "entity", "spawn_rule", "structure", "player_state"} <= content)
        triggers = {row["trigger"]["type"] for row in ir["behaviors"]}
        self.assertTrue({"item_use", "item_use_on_block", "entity_hit", "block_break", "projectile_impact", "object_tick", "entity_spawn", "entity_hurt", "entity_death", "state_transition", "block_interact"} <= triggers)
        actions = {action["type"] for row in ir["behaviors"] for action in row["actions"]}
        self.assertTrue({"spawn_projectile", "create_explosion", "apply_effect", "start_cooldown", "update_persistent_state", "place_structure", "open_interaction_ui"} <= actions)
        self.assertEqual({"player", "item", "block", "entity"}, {row["scope"] for row in ir["state"]})
        self.assertTrue(ir["registries"])
        self.assertTrue(all("special_inventory" in row["inventory"] for row in ir["mods"]))
        self.assertTrue(ir["ui_intent"])
        self.assertEqual(
            {action["ui"] for row in ir["behaviors"] for action in row["actions"] if action["type"] == "open_interaction_ui"},
            {row["id"] for row in ir["ui_intent"]},
        )
        self.assertTrue(ir["presentation_requirements"])
        self.assertTrue(ir["unsupported_hooks"])
        classes = {row["classification"] for row in plan["features"]}
        self.assertTrue({"DIRECT", "SCRIPTED_EQUIVALENT", "RECONSTRUCTED", "BEHAVIORAL_APPROXIMATION", "UNSUPPORTED"} <= classes)
        self.assertTrue(all(row["evidence"] for row in ir["behaviors"] + ir["content"] + ir["state"]))

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "representative"
            compile_bedrock(ir, plan, output)
            result = validate_output(output, plan)
            self.assertTrue(result["valid"], result)

    def test_mini_modpack_dependency_and_collision_are_explicit(self):
        ir = scan_path(FIXTURES / "mini_modpack")
        self.assertEqual({"representative", "compat_companion"}, {row["id"] for row in ir["mods"]})
        self.assertIn(
            ("compat_companion", "representative"),
            {(row["from"], row["to"]) for row in ir["dependency_graph"]["edges"]},
        )
        conflict = next(row for row in ir["diagnostics"] if row.get("code") == "identifier_conflict")
        self.assertEqual("representative:phase_blade", conflict["feature"])
        self.assertEqual(2, len(conflict["sources"]))
        feature = next(row for row in plan_conversion(ir)["features"] if row["id"] == conflict["feature"])
        self.assertEqual("MANUAL_REDESIGN", feature["classification"])
        self.assertEqual("identifier_conflict", feature["diagnostic"])


if __name__ == "__main__":
    unittest.main()
