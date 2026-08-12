#!/usr/bin/env python3
import hashlib
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORT = json.loads((HERE / "FINAL_AUTHORITY_CLOSURE_MAP.json").read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FinalAuthorityClosureMapTest(unittest.TestCase):
    def test_exact_audited_source_and_evidence_hashes(self):
        self.assertEqual(REPORT["audited_source"], {
            "commit": "edbdf01143e994cae8e77414951d07ae3c95ed63",
            "tree": "9685cd17539999419d3f8e32272261e585cde0c6",
            "worktree_clean_for_audited_paths": True,
        })
        for row in REPORT["evidence"]:
            self.assertEqual(sha256(ROOT / row["path"]), row["sha256"], row["path"])

    def test_skyreach_current_state_supersedes_partial_snapshots(self):
        current = json.loads((ROOT / "engineering/skyreach-intake/deferred-source-exit/SKYREACH_DEFERRED_SOURCE_EXIT.json").read_text())
        self.assertEqual(current["technical_deferred"], {})
        self.assertIn("all 10 Packet 004 creatures", current["implemented"]["creatures"])
        self.assertIn("all 10 Packet 004 native-backed custom blocks", current["implemented"]["plants"])
        self.assertIn("all 30 custom Packet 004", current["implemented"]["native_assets"])
        row = next(item for item in REPORT["resolved_or_superseded"] if item["id"] == "SKYREACH_NATIVE_AND_PRODUCT_BINDING_GAPS")
        self.assertEqual(row["classification"], "RESOLVED")
        self.assertIn("superseded", row["history_boundary"])

    def test_skyreach_proposal_readiness_matches_authority_map(self):
        authority = json.loads((ROOT / "engineering/skyreach-intake/authority/SKYREACH_VERTICAL_INTAKE_MAP.json").read_text())
        rows = authority["minimum_authority_tranches"]
        self.assertEqual(rows["W1-001-SR"]["status"], "PROPOSED_NOT_RATIFIED")
        self.assertEqual(len(rows["W1-001-SR"]["aliases"]), 18)
        self.assertEqual(rows["W1-001-SR"]["new_required_items"], [{
            "craft_home": "glider_panel",
            "id": "aionbound:wing_bone_stay",
            "term": "Wing Bone Stay",
        }])
        self.assertEqual(len(rows["W1-003-STORM-NEST"]["deferred_decisions"]), 6)
        self.assertEqual(len(rows["W1-004-SR"]["deferred_decisions"]), 5)
        states = {row["id"]: row["state"] for row in REPORT["approval_readiness"]}
        self.assertEqual(states["W1-001-SR"], "APPROVAL_READY_AS_STRUCTURED_INTAKE_ROW")
        self.assertEqual(states["W1-003-STORM-NEST"], "EXISTS_NOT_APPROVAL_READY_FOR_EXECUTION")
        self.assertEqual(states["W1-004-SR"], "EXISTS_NOT_APPROVAL_READY_FOR_EXECUTION")

    def test_sidegrade_defer_is_bounded_and_shipping_ids_are_absent(self):
        proposal = json.loads((ROOT / "engineering/authority/support-proposals/W1-CREATIVE-005/sidegrade_identity_proposal.json").read_text())
        self.assertEqual(proposal["authority_effect"], "NONE_UNTIL_RATIFIED")
        self.assertFalse(proposal["proposal"]["implementation_priority"]["blocks_base_packet_006_items"])
        deferred = next(row for row in REPORT["safe_to_ship_deferred"] if row["id"] == "W1-CREATIVE-005")
        self.assertEqual(deferred["classification"], "SAFE_TO_SHIP_DEFERRED")
        ids = [row["id"] for row in proposal["proposal"]["sibling_sidegrades"] + proposal["proposal"]["sibling_unique_finishes"]]
        pack_text = "\n".join(
            path.read_text(errors="ignore")
            for pack in (ROOT / "behavior_pack", ROOT / "resource_pack")
            for path in pack.rglob("*") if path.is_file() and path.suffix in {".json", ".js", ".lang"}
        )
        for identifier in ids:
            self.assertNotIn(identifier, pack_text)

    def test_final_blockers_and_minimum_user_decisions_are_explicit(self):
        blockers = {row["id"] for row in REPORT["final_blocking"]}
        self.assertEqual(blockers, {
            "ASHEN_SHARED_RUNTIME_ACTIVATION",
            "SKYREACH_EXECUTABLE_VERTICAL",
            "TWINBOND_FINALE",
            "W1-ASSET-AUDIO-001",
            "FINAL_PACKAGE_AND_QUALIFICATION_EVIDENCE",
        })
        decisions = REPORT["smallest_user_decision_set"]
        self.assertEqual(len(decisions["required_now_for_full_candidate"]), 5)
        self.assertEqual(decisions["not_required_if_deferred_conditions_hold"], ["W1-CREATIVE-005"])
        self.assertEqual(
            set(decisions["no_further_human_design_decision_required"]),
            {"ASHEN_SHARED_RUNTIME_ACTIVATION", "FINAL_PACKAGE_AND_QUALIFICATION_EVIDENCE"},
        )


if __name__ == "__main__":
    unittest.main()
