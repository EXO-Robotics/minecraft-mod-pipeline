import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json"


class Wave1RatifiedLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_exact_whisperwood_ashen_and_crystal_tranches_are_ratified_and_preserved(self):
        rows = self.ledger["ratifications"]["approved"]
        self.assertEqual(
            [row["tranche"] for row in rows],
            [
                "W1-001-WW",
                "W1-003-THORN-COURT",
                "W1-004-WW-CH1",
                "W1-006-WW-SAPLING",
                "W1-001-AH",
                "W1-003-KILN-SKY",
                "W1-004-AH",
                "W1-001-CM",
                "W1-003-PEARL-DEPTHS",
                "W1-004-CM",
            ],
        )
        self.assertTrue(self.ledger["ratifications"]["preserve_proposals_as_written"])
        for row in rows:
            proposal = ROOT / row["proposal"]
            self.assertTrue(proposal.is_file())
            self.assertEqual(hashlib.sha256(proposal.read_bytes()).hexdigest(), row["proposal_sha256"])

    def test_deferred_scope_is_not_silently_promoted(self):
        self.assertEqual(
            self.ledger["ratifications"]["deferred"],
            [
                "W1-CREATIVE-005",
                "W1-001-SKYREACH_AND_FINALE",
                "W1-003-SKYREACH_AND_FINALE",
                "W1-004-SKYREACH_AND_FINALE",
            ],
        )
        policy = self.ledger["construction_policy"]
        self.assertTrue(policy["whisperwood_vertical_implementation_authorized"])
        self.assertTrue(policy["ashen_vertical_implementation_authorized"])
        self.assertTrue(policy["crystal_marsh_vertical_implementation_authorized"])
        self.assertEqual(policy["ashen_vertical_status"], "ASHEN_VERTICAL_SOURCE_COMPLETE_RUNTIME_ACTIVATION_DEFERRED")
        self.assertFalse(policy["new_bds_checkpoint_authorized"])

    def test_ashen_approval_preserves_sidegrade_deferral_and_exact_seal(self):
        rows = {row["tranche"]: row for row in self.ledger["ratifications"]["approved"]}
        identity = json.loads((ROOT / rows["W1-001-AH"]["proposal"]).read_text(encoding="utf-8"))["proposal"]
        boss_doc = json.loads((ROOT / rows["W1-003-KILN-SKY"]["proposal"]).read_text(encoding="utf-8"))
        boss = boss_doc["proposal"]
        loot = json.loads((ROOT / rows["W1-004-AH"]["proposal"]).read_text(encoding="utf-8"))["proposal"]
        self.assertEqual(identity["drake_scale_selection_semantics"]["upgrade_or_sidegrade_authority"], "NONE_WHILE_W1-CREATIVE-005_IS_DEFERRED")
        self.assertEqual(boss_doc["authority_effect"], "NONE_UNTIL_RATIFIED_IN_REPLACEMENT_DECISION_LEDGER")
        self.assertEqual(boss["terminal_semantics"]["progression_credit"], "per_player_durable_once")
        self.assertEqual(loot["ashen_resolution"]["chapter_critical_seal"], "aionbound:ash_drake_horn")
        self.assertFalse(loot["ashen_resolution"]["ecology_or_natural_ash_drake_can_drop_chapter_seal"])

    def test_whisperwood_progression_guards_remain_exact(self):
        proposal_path = ROOT / self.ledger["ratifications"]["approved"][2]["proposal"]
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))["proposal"]
        guard = proposal["arena_reward_guard"]
        seals = proposal["alternate_seal_resolution"]
        self.assertFalse(guard["regular_entity_or_command_kill_can_grant_trophy"])
        self.assertEqual(guard["critical_progression_representation"], "durable_virtual_seal_credit_not_physical_item_presence")
        self.assertFalse(seals["briar_elk_trophy_replaces_thorn_stalker_skull"])
        self.assertFalse(seals["mosskip_trophy_replaces_thorn_stalker_skull"])
        self.assertEqual(seals["chapter_1_critical_seal"], "aionbound:thorn_stalker_skull")

    def test_crystal_approval_preserves_sidegrade_deferral_and_exact_seal(self):
        rows = {row["tranche"]: row for row in self.ledger["ratifications"]["approved"]}
        identity = json.loads((ROOT / rows["W1-001-CM"]["proposal"]).read_text(encoding="utf-8"))["proposal"]
        boss = json.loads((ROOT / rows["W1-003-PEARL-DEPTHS"]["proposal"]).read_text(encoding="utf-8"))["proposal"]
        loot = json.loads((ROOT / rows["W1-004-CM"]["proposal"]).read_text(encoding="utf-8"))["proposal"]
        self.assertEqual(identity["w1_creative_005_effect"], "NONE_DEFERRED_NO_SIDEGRADE_OR_UPGRADE_BEHAVIOR_GRANTED")
        self.assertEqual(identity["new_inventory_identities_selected"], [
            "aionbound:prism_wing", "aionbound:watcher_lens", "aionbound:wight_shroud"
        ])
        self.assertEqual(boss["terminal_semantics"]["progression_credit"], "per_player_durable_once")
        self.assertEqual(loot["crystal_marsh_resolution"]["chapter_critical_seal"], "aionbound:marsh_wight_mask")
        self.assertFalse(loot["crystal_marsh_resolution"]["ecology_or_natural_marsh_wight_can_drop_chapter_seal"])
        self.assertFalse(loot["crystal_marsh_resolution"]["mastery_only_trophies"]["aionbound:crystal_obelisk_fragment"]["progression_substitute"])


if __name__ == "__main__":
    unittest.main()
