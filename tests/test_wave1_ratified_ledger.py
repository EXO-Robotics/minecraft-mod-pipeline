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

    def test_exact_whisperwood_tranches_are_ratified_and_preserved(self):
        rows = self.ledger["ratifications"]["approved"]
        self.assertEqual(
            [row["tranche"] for row in rows],
            ["W1-001-WW", "W1-003-THORN-COURT", "W1-004-WW-CH1", "W1-006-WW-SAPLING"],
        )
        self.assertTrue(self.ledger["ratifications"]["preserve_proposals_as_written"])
        for row in rows:
            proposal = ROOT / row["proposal"]
            self.assertTrue(proposal.is_file())
            self.assertEqual(hashlib.sha256(proposal.read_bytes()).hexdigest(), row["proposal_sha256"])

    def test_deferred_scope_is_not_silently_promoted(self):
        self.assertEqual(
            self.ledger["ratifications"]["deferred"],
            ["W1-CREATIVE-005", "W1-001-LATER-REGIONS", "W1-004-LATER-REGIONS"],
        )
        policy = self.ledger["construction_policy"]
        self.assertTrue(policy["whisperwood_vertical_implementation_authorized"])
        self.assertTrue(policy["ashen_start_authorized_only_after_checkpoint_1_pass"])

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


if __name__ == "__main__":
    unittest.main()
