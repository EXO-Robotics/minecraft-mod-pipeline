import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "engineering/whisperwood-intake/readiness/WHISPERWOOD_READINESS_AUDIT.json"


class WhisperwoodReadinessAuditTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(AUDIT.read_text())

    def test_audit_is_bound_to_exact_prefix_and_fail_closed(self):
        self.assertEqual(self.data["audited_head"], "a9d64b2a999462a2c8e2f1f1779e06c8cf6ca702")
        self.assertEqual(self.data["overall_classification"], "PRE_LOOT_INTEGRATION_PREFIX_NOT_VERTICAL_COMPLETE")
        self.assertIs(self.data["checkpoint_1_authorized"], False)

    def test_criterion_inventory_is_exact_and_unique(self):
        expected = {
            "first_living_biome_fully_playable_offline",
            "all_001_ids_in_world", "ww_craft_loop", "hunter_camp_waystone_cave",
            "thorn_apex_runnable", "drops_feed_ww_crafts", "non_statue_ambient",
            "spawn_to_ww_explore_without_commands", "craft_spear_or_armor_piece",
            "find_structure", "defeat_stalker_or_shrine_path", "activate_waystone",
            "obtain_ah_rumor", "normalized_assets_load", "natural_entities_initialize",
            "structures_resources_register", "runtime_starts_cleanly", "same_world_reopens",
            "no_candidate_scoped_content_runtime_errors"
        }
        ids = [row["id"] for row in self.data["criteria"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), expected)

    def test_classifications_use_only_closed_vocabulary(self):
        allowed = set(self.data["classification_vocabulary"])
        self.assertEqual(allowed, {"PASS_SOURCE", "WITHHELD_TICKET", "UNPROVEN_CLIENT_OR_BDS", "MISSING_IMPLEMENTATION"})
        self.assertTrue(all(row["classification"] in allowed for row in self.data["criteria"]))

    def test_only_non_statue_bar_is_source_pass(self):
        passed = [row["id"] for row in self.data["criteria"] if row["classification"] == "PASS_SOURCE"]
        self.assertEqual(passed, ["non_statue_ambient"])

    def test_checkpoint_has_no_source_pass(self):
        checkpoint = [row for row in self.data["criteria"] if row["group"] == "checkpoint_1"]
        self.assertEqual(len(checkpoint), 6)
        self.assertTrue(all(row["classification"] == "UNPROVEN_CLIENT_OR_BDS" for row in checkpoint))


if __name__ == "__main__":
    unittest.main()
