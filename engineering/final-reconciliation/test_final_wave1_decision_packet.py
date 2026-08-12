#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPEC = importlib.util.spec_from_file_location("decision_builder", HERE / "build_final_wave1_decision_packet.py")
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)
REPORT = json.loads((HERE / "FINAL_WAVE1_DECISION_PACKET.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FinalWave1DecisionPacketTests(unittest.TestCase):
    def test_exact_integration_and_source_hashes(self) -> None:
        self.assertEqual(REPORT["audited_integration"], {"commit": BUILDER.AUDITED_COMMIT, "tree": BUILDER.AUDITED_TREE, "head_advanced_during_audit": False})
        for path, expected in BUILDER.SOURCE_HASHES.items():
            self.assertTrue((ROOT / path).is_file(), path)
            self.assertRegex(expected, r"^[0-9a-f]{64}$")
        self.assertEqual(sha256(BUILDER.PACKET006_MANIFEST), BUILDER.PACKET006_MANIFEST_SHA256)

    def test_all_six_proposals_are_exact_and_unratified(self) -> None:
        rows = [row for decision in REPORT["decision_set"][:2] for row in decision["proposals"]]
        self.assertEqual({row["ticket_id"] for row in rows}, {"W1-001-SR", "W1-003-STORM-NEST", "W1-004-SR", "W1-002-TWINBOND", "W1-003-TWINBOND", "W1-004-TWINBOND"})
        for row in rows:
            self.assertEqual(row["status"], "PROPOSED_NOT_RATIFIED")
            self.assertEqual(row["authority_effect"], "NONE_UNTIL_RATIFIED_IN_REPLACEMENT_DECISION_LEDGER")
            self.assertEqual(sha256(ROOT / row["path"]), row["sha256"])

    def test_verbatim_minimal_approval_text(self) -> None:
        self.assertEqual(REPORT["decision_set"][0]["approval_text_verbatim"], BUILDER.SKYREACH_APPROVAL)
        self.assertEqual(REPORT["decision_set"][1]["approval_text_verbatim"], BUILDER.FINALE_APPROVAL)
        audio = REPORT["decision_set"][2]
        self.assertEqual(audio["kind"], "CHOOSE_EXACTLY_ONE")
        self.assertEqual([row["approval_text_verbatim"] for row in audio["choices"]], [BUILDER.AUDIO_ORIGINAL, BUILDER.AUDIO_SCOPE_REDUCTION])

    def test_packet006_all_50_source_presentation_closure(self) -> None:
        p = REPORT["no_decision_required"]["packet006_base_presentation"]
        self.assertEqual(p["manifest_count"], 50)
        self.assertEqual(p["source_presentation_complete"], 50)
        self.assertEqual(p["item_representations"] + p["block_representations"], 50)
        self.assertEqual(p["geometry_bindings"], 50)
        self.assertEqual(p["localized"], 50)
        self.assertEqual(p["item_atlas_entries"] + p["terrain_atlas_entries"], 50)
        self.assertEqual(set(p["intentional_non_attachable_placeable_trophies"]), {"aionbound:mosskip_trophy", "aionbound:briar_elk_trophy", "aionbound:thorn_stalker_skull", "aionbound:ancient_acorn_display"})

    def test_sidegrades_remain_absent_and_ashen_is_not_misclassified(self) -> None:
        proposal = json.loads((ROOT / "engineering/authority/support-proposals/W1-CREATIVE-005/sidegrade_identity_proposal.json").read_text())
        ids = [row["id"] for key in ("sibling_sidegrades", "sibling_unique_finishes") for row in proposal["proposal"][key]]
        pack_text = "\n".join(path.read_text(errors="ignore") for pack in (ROOT / "behavior_pack", ROOT / "resource_pack") for path in pack.rglob("*") if path.is_file() and path.suffix in {".json", ".js", ".lang"})
        for identifier in ids:
            self.assertNotIn(identifier, pack_text)
        ashen = REPORT["separately_blocked_not_approved_by_this_packet"]["ashen_activation"]
        self.assertEqual(ashen["disposition"], "NO_RETRY_NO_WORKAROUND_IN_THIS_WORKLOAD")
        self.assertFalse(ashen["product_defect_demonstrated"])

    def test_publication_is_separate_and_unobservable(self) -> None:
        pub = REPORT["separately_blocked_not_approved_by_this_packet"]["github_publication"]
        self.assertEqual(pub["classification"], "EXTERNALLY_OBSERVED_NOT_PRODUCT_EVIDENCE_PUBLICATION_BLOCKER_ONLY")
        self.assertEqual(pub["decision_source"], "NOT_OBSERVABLE")
        self.assertIn("None", str(pub["product_or_candidate_consequence"]))
        self.assertIsNone(pub["committed_evidence_path"])

    def test_generated_outputs_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            BUILDER.write_outputs(out)
            for name in ("FINAL_WAVE1_DECISION_PACKET.json", "FINAL_WAVE1_DECISION_PACKET.md"):
                self.assertEqual((out / name).read_bytes(), (HERE / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
