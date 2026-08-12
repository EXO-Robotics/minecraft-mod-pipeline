from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class CrystalSourceExitTests(unittest.TestCase):
    def test_existing_runtime_classes_are_reused_without_ashen_activation(self):
        runtime = (ROOT / "behavior_pack/scripts/runtime.js").read_text()
        self.assertEqual(8, len(re.findall(r"(?:afterEvents|beforeEvents)\.[A-Za-z]+\.subscribe\(", runtime)))
        self.assertEqual(1, runtime.count("runInterval(tick, 1)"))
        for fragment in ("pearlDepths.reconcile()", "pearlDepths.tick()", "pearlDepths.bossDeath(event)", "crystalEquipment.tickPlayer(player)"):
            self.assertIn(fragment, runtime)
        self.assertNotIn("createKilnSkyService", runtime)
        self.assertNotIn("createAshenEquipmentRoleService", runtime)

    def test_schema_v4_and_natural_budget_are_preserved(self):
        state = (ROOT / "behavior_pack/scripts/state.js").read_text()
        budgets = (ROOT / "behavior_pack/scripts/budgets.js").read_text()
        catalog = (ROOT / "behavior_pack/scripts/catalog.js").read_text()
        self.assertIn("export const STATE_VERSION = 4", state)
        self.assertRegex(budgets, r"naturalEntitiesTarget:\s*40")
        for value in ("bloom_crab", "bog_watcher", "crystal_dragonfly", "crystal_newt", "glass_heron", "mire_turtle", "prism_frog", "reed_serpent", "silt_crocodile"):
            self.assertIn(f'"aionbound:{value}"', catalog)
        natural = catalog[catalog.index("export const NATURAL_ENTITY_IDS"):catalog.index("]);", catalog.index("export const NATURAL_ENTITY_IDS"))]
        self.assertNotIn("aionbound:marsh_wight", natural)

    def test_protected_reward_and_optional_trophy_guards(self):
        ecology = (ROOT / "behavior_pack/loot_tables/entities/crystal/marsh_wight.json").read_text()
        for forbidden in ("marsh_wight_mask", "pearl_depths"):
            self.assertNotIn(forbidden, ecology.lower())
        contract = (ROOT / "behavior_pack/scripts/crystal_reward_data.js").read_text()
        self.assertIn('chapterSeal: "aionbound:marsh_wight_mask"', contract)
        self.assertIn("progressionSubstitutes: Object.freeze([])", contract)
        pearl = (ROOT / "behavior_pack/scripts/pearl_depths.js").read_text()
        for fragment in ("claimMask", "recoverMask", "completeWorld", "worldCompletionKey"):
            self.assertIn(fragment, pearl)
        rewards = (ROOT / "behavior_pack/scripts/crystal_rewards.js").read_text()
        self.assertIn("guardArenaCacheInteraction", rewards)

    def test_source_exit_manifest_declares_narrow_boundary(self):
        path = ROOT / "engineering/validation/wave1/WAVE_1_CRYSTAL_IMPLEMENTED_CLOSURE.json"
        manifest = json.loads(path.read_text())
        self.assertEqual("CRYSTAL_MARSH_VERTICAL_SOURCE_COMPLETE_TARGETED_LOCAL_PASS", manifest["status"])
        self.assertEqual(4, manifest["invariants"]["persistence_schema"])
        self.assertEqual(40, manifest["invariants"]["natural_entity_target"])
        self.assertEqual(9, len(manifest["invariants"]["natural_crystal_ids"]))
        self.assertIn("NO BUILD, PACKAGE, BDS, CLIENT", manifest["proof_boundary"])


if __name__ == "__main__":
    unittest.main()
