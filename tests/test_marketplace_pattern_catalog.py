from __future__ import annotations

import unittest

from mccompiler.pattern_catalog import marketplace_patterns, pattern_families


class MarketplacePatternCatalogTests(unittest.TestCase):
    def test_required_families_and_initial_patterns_exist(self) -> None:
        self.assertTrue({
            "items", "weapons", "tools", "armor", "projectiles", "effects", "cooldowns",
            "abilities", "machines", "entities", "bosses", "structures", "spawning",
            "transformations", "vehicles", "inventory", "forms", "progression", "world",
        } <= pattern_families())
        identifiers = {row["id"] for row in marketplace_patterns()}
        self.assertTrue({
            "weapons/projectile", "weapons/explosive-staff", "weapons/lightning",
            "tools/area-mining", "abilities/teleport-item", "abilities/summoning-item",
            "armor/passive-set", "armor/active-ability", "abilities/cooldown",
            "inventory/random-reward-block", "machines/processing", "machines/energy-like",
            "world/crop-growth", "entities/companion", "vehicles/mount", "bosses/multiphase",
            "transformations/selector", "forms/key-binding-replacement",
            "forms/java-gui-replacement", "world/dimension-approximation",
            "world/portal-structure-transition",
        } <= identifiers)

    def test_every_pattern_has_operational_contract(self) -> None:
        required = {
            "required_ir_shape", "marketplace_safe_strategies", "controller_interaction_design",
            "performance_implications", "fidelity_expectations", "known_limitations", "tests", "example_output",
        }
        for pattern in marketplace_patterns():
            with self.subTest(pattern=pattern["id"]):
                self.assertTrue(required <= pattern.keys())
                self.assertTrue(pattern["marketplace_safe_strategies"])
                self.assertTrue(pattern["tests"])


if __name__ == "__main__":
    unittest.main()
