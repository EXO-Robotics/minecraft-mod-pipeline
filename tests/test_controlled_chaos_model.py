from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = (
    ROOT
    / "benchmarks/controlled-chaos-integration/behavior-model/controlled_chaos.py"
)
SPEC = importlib.util.spec_from_file_location("controlled_chaos_model", MODEL_PATH)
assert SPEC is not None and SPEC.loader is not None
MODEL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODEL
SPEC.loader.exec_module(MODEL)

BossPhase = MODEL.BossPhase
ControlledChaosModel = MODEL.ControlledChaosModel
run_hostile_damage = MODEL.run_hostile_damage


class ControlledChaosModelTests(unittest.TestCase):
    def test_chaos_sequence_is_fixed_seed_repeatable_and_bounded(self) -> None:
        first = ControlledChaosModel(seed=7305)
        second = ControlledChaosModel(seed=7305)
        first_outcomes = [first.select_chaos() for _ in range(3)]
        second_outcomes = [second.select_chaos() for _ in range(3)]
        self.assertEqual(first_outcomes, second_outcomes)
        self.assertTrue(set(first_outcomes) <= set(first.CHAOS_OUTCOMES))
        self.assertIsNone(first.select_chaos())

    def test_player_progression_and_cooldowns_are_isolated(self) -> None:
        model = ControlledChaosModel(seed=1)
        self.assertTrue(model.award_elite("a"))
        self.assertFalse(model.player("b").elite_reward)
        self.assertTrue(model.use_weapon("a", tick=10))
        self.assertFalse(model.use_weapon("a", tick=11))
        self.assertTrue(model.use_weapon("b", tick=11))

    def test_elite_and_boss_rewards_cannot_duplicate(self) -> None:
        model = ControlledChaosModel(seed=1)
        self.assertTrue(model.award_elite("a"))
        self.assertFalse(model.award_elite("a"))
        self.assertTrue(model.advance_boss(BossPhase.TWO))
        self.assertTrue(model.advance_boss(BossPhase.THREE))
        self.assertEqual({"a": True, "b": True}, model.complete_boss(["a", "b", "a"]))
        self.assertEqual({"a": False, "b": False}, model.complete_boss(["a", "b"]))

    def test_boss_phases_must_be_ordered(self) -> None:
        model = ControlledChaosModel(seed=1)
        self.assertFalse(model.advance_boss(BossPhase.TWO))
        model.award_elite("a")
        self.assertFalse(model.advance_boss(BossPhase.THREE))
        self.assertTrue(model.advance_boss(BossPhase.TWO))
        self.assertTrue(model.advance_boss(BossPhase.THREE))

    def test_snapshot_round_trip_and_v1_migration(self) -> None:
        model = ControlledChaosModel(seed=1)
        model.award_elite("a")
        restored = ControlledChaosModel.restore(model.snapshot(), seed=1)
        self.assertEqual(model.snapshot(), restored.snapshot())
        migrated = ControlledChaosModel.restore(
            {"version": 1, "boss_phase": 2, "players": {"a": {"power": True}}},
            seed=1,
        )
        self.assertTrue(migrated.player("a").unlock)
        self.assertTrue(migrated.player("a").boss_reward)

    def test_corrupt_or_unknown_state_fails_safe_to_empty(self) -> None:
        for raw in (None, "bad", {"version": 99}, {"version": 2, "players": []},
                    {"version": 2, "boss_phase": "bad"}):
            with self.subTest(raw=raw):
                self.assertEqual({}, ControlledChaosModel.restore(raw, seed=1).state.players)

    def test_active_objects_are_bounded_and_cleanup_is_idempotent(self) -> None:
        model = ControlledChaosModel(seed=1, active_entity_limit=2)
        self.assertTrue(model.spawn_bounded("one"))
        self.assertTrue(model.spawn_bounded("two"))
        self.assertFalse(model.spawn_bounded("three"))
        self.assertFalse(model.spawn_bounded("one"))
        self.assertEqual(2, model.cleanup())
        self.assertEqual(0, model.cleanup())

    def test_hostile_damage_has_two_independent_exact_executions(self) -> None:
        receipts = [run_hostile_damage(execution) for execution in (1, 2)]
        self.assertEqual([1, 2], [receipt.execution for receipt in receipts])
        for receipt in receipts:
            self.assertTrue(receipt.passed)
            self.assertEqual(20, receipt.health_before)
            self.assertEqual(16, receipt.health_after)
            self.assertEqual(4, receipt.actual_damage)
            self.assertFalse(receipt.entity_death_observed)


if __name__ == "__main__":
    unittest.main()
