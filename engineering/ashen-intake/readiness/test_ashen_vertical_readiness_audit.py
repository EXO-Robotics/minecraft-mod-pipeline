#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPORT = HERE / "ASHEN_VERTICAL_READINESS_AUDIT.json"
BUILDER = HERE / "build_ashen_vertical_readiness_audit.py"

SPEC = importlib.util.spec_from_file_location("ashen_readiness_builder", BUILDER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AshenVerticalReadinessAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.rebuilt = MODULE.build()

    def test_report_is_exact_deterministic_rebuild(self) -> None:
        self.assertEqual(self.report, self.rebuilt)

    def test_exact_rosters(self) -> None:
        self.assertEqual(len(self.report["packet002"]), 50)
        self.assertEqual(len(self.report["packet006_ashen"]), 14)
        self.assertEqual(len({entry["id"] for entry in self.report["packet002"]}), 50)
        self.assertEqual(len({entry["id"] for entry in self.report["packet006_ashen"]}), 14)

    def test_only_safe_packet002_items_and_blocks_are_implemented(self) -> None:
        summary = self.report["summary"]
        expected = set(MODULE.RESOURCE_IDS + MODULE.BLOCK_IDS)
        self.assertEqual(set(summary["implemented_static_packet002_ids"]), expected)
        self.assertEqual(set(summary["exact_packet002_runtime_reference_ids"]), expected)
        self.assertEqual(summary["packet002_runtime_ids_beyond_safe_resources_and_blocks"], [])

    def test_unimplemented_vertical_surfaces_are_not_overclaimed(self) -> None:
        by_category = {}
        for entry in self.report["packet002"]:
            by_category.setdefault(entry["category"], []).append(entry)
        for category in ("creatures", "plants", "structures"):
            self.assertTrue(all(entry["surface_state"]["overall"] == "SAFE_BUT_UNIMPLEMENTED" for entry in by_category[category]))
        self.assertEqual(self.report["system_readiness"]["entities_ai_spawn"], "0_OF_10_IMPLEMENTED")
        self.assertEqual(self.report["system_readiness"]["plants_worldgen"], "0_OF_10_IMPLEMENTED")
        self.assertEqual(self.report["system_readiness"]["structures_worldgen"], "0_OF_10_IMPLEMENTED")

    def test_native_evidence_partition(self) -> None:
        counts = self.report["summary"]["packet002_native_counts"]
        self.assertEqual(counts["PASS_REPRESENTATIVE_NATIVE_REPAIR_GATE"], 7)
        self.assertEqual(counts["NATIVE_REPAIR_REQUIRED"], 23)
        self.assertEqual(counts["NOT_APPLICABLE_NATIVE_FULL_CUBE_OR_FLAT_ITEM"], 20)

    def test_packet006_collision_and_authority_partition(self) -> None:
        by_id = {entry["id"]: entry for entry in self.report["packet006_ashen"]}
        self.assertEqual(by_id["briar_ring"]["surface_state"]["overall"], "EXISTING_WHISPERWOOD_BASE_KEEP_NOT_ASHEN_IMPLEMENTATION")
        self.assertEqual(by_id["briar_ring"]["authority_blockers"], ["W1-CREATIVE-005"])
        absent = set(by_id) - {"briar_ring"}
        self.assertTrue(all(by_id[asset]["surface_state"]["runtime_binding"] == "NOT_IMPLEMENTED" for asset in absent))
        self.assertEqual(set(by_id["ash_drake_horn"]["authority_blockers"]), {"W1-003-KILN-SKY", "W1-004-AH"})

    def test_client_bds_and_kiln_sky_remain_unproven(self) -> None:
        self.assertEqual(self.report["system_readiness"]["client_bds_console"], "UNPROVEN_NO_NEW_BDS_RUN_AUTHORIZED_OR_PERFORMED")
        self.assertEqual(self.report["system_readiness"]["kiln_sky"], "IDENTITY_ONLY_INTAKE_W1_003_AND_W1_004_BLOCKED_NO_RUNTIME")


if __name__ == "__main__":
    unittest.main()
