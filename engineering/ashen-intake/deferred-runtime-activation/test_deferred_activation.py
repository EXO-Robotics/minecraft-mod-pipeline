#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
JSON_PATH = HERE / "ASHEN_RUNTIME_ACTIVATION_DEFERRED.json"
MD_PATH = HERE / "ASHEN_RUNTIME_ACTIVATION_DEFERRED.md"


class DeferredActivationReceiptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(JSON_PATH.read_text())

    def test_exact_disposition_and_base(self) -> None:
        self.assertEqual("ASHEN_VERTICAL_SOURCE_COMPLETE_RUNTIME_ACTIVATION_DEFERRED", self.data["status"])
        self.assertEqual("MANAGED_REVIEWER_ACTIVATION_BLOCKED", self.data["blocker"])
        self.assertEqual("bcd65076900a3688dd797d54719263d88afd501c", self.data["source_authority"]["commit"])
        self.assertEqual("4d876b233e6b510687d238f1d7f6611c7c0c4ab9", self.data["source_authority"]["tree"])
        self.assertFalse(self.data["vertical_disposition"]["runtime_complete"])

    def test_only_two_compositions_deferred_and_no_runtime_claim(self) -> None:
        self.assertEqual(2, len(self.data["vertical_disposition"]["deferred_only"]))
        self.assertTrue(all(row["observed"] == "ABSENT" for row in self.data["dormant_connections"]))
        self.assertFalse(self.data["proof_boundary"]["bds"])
        self.assertFalse(self.data["proof_boundary"]["shared_runtime_activation"])
        self.assertFalse(self.data["proof_boundary"]["runtime_complete"])

    def test_evidence_hashes_close(self) -> None:
        for row in self.data["evidence"]:
            path = ROOT / row["path"]
            self.assertEqual(row["bytes"], path.stat().st_size, row["path"])
            self.assertEqual(row["sha256"], hashlib.sha256(path.read_bytes()).hexdigest(), row["path"])

    def test_runtime_and_catalog_remain_dormant(self) -> None:
        runtime = (ROOT / "behavior_pack/scripts/runtime.js").read_text()
        catalog = (ROOT / "behavior_pack/scripts/catalog.js").read_text()
        self.assertNotIn("createAshenEquipmentService", runtime)
        self.assertNotIn("createKilnSkyService", runtime)
        self.assertNotIn("ashenEquipment.", runtime)
        self.assertNotIn("kilnSky.", runtime)
        self.assertNotIn('"aionbound:ash_repeater": "ashen_ranged"', catalog)

    def test_rebuild_is_deterministic(self) -> None:
        before = (hashlib.sha256(JSON_PATH.read_bytes()).hexdigest(), hashlib.sha256(MD_PATH.read_bytes()).hexdigest())
        subprocess.run(["python3", str(HERE / "build_deferred_activation.py")], cwd=ROOT, check=True)
        after = (hashlib.sha256(JSON_PATH.read_bytes()).hexdigest(), hashlib.sha256(MD_PATH.read_bytes()).hexdigest())
        self.assertEqual(before, after)

    def test_final_candidate_reconciliation_is_mandatory(self) -> None:
        ticket = self.data["deferred_integration_ticket"]
        self.assertFalse(ticket["design_decisions_required"])
        self.assertIn("MUST_RECONCILE_BEFORE_IMMUTABLE_WAVE_1_CANDIDATE", ticket["final_candidate_rule"])
        self.assertTrue(any("full inventory" in item for item in ticket["acceptance_criteria"]))
        self.assertEqual([30, 2, 6], [row["passed"] for row in self.data["passed_evidence"]["focused_validation_observed_2026_08_11"]])
        self.assertTrue(all(row["failed"] == 0 for row in self.data["passed_evidence"]["focused_validation_observed_2026_08_11"]))
        debt = self.data["reconciliation_debt"]
        self.assertEqual("W1-G8-KILN-SKY-CHECKED-IN-EVIDENCE-STALE", debt["id"])
        self.assertEqual({"tests": 2, "passed": 1, "failed": 1}, debt["observed_2026_08_11"])
        self.assertFalse(debt["product_defect_demonstrated"])


if __name__ == "__main__":
    unittest.main()
