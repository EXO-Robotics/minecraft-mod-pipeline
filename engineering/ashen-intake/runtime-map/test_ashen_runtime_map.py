from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MAP_PATH = HERE / "ASHEN_RUNTIME_IMPLEMENTATION_MAP.json"
GENERATOR_PATH = HERE / "build_ashen_runtime_map.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("ashen_runtime_map_builder", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AshenRuntimeMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        cls.builder = load_generator()

    def test_exact_base_and_inventory_counts(self):
        self.assertEqual(self.payload["base"]["commit"], "9acf1b0f62ade90b59ba65e0a9e0618852ff3159")
        self.assertEqual(self.payload["base"]["tree"], "9b7b425e535439658df29c92f82ad73e9aa54e3d")
        self.assertEqual(
            self.payload["counts"],
            {
                "blocks": 10,
                "creatures": 10,
                "equipment_links": 14,
                "packet_002_assets": 50,
                "plants": 10,
                "resources": 10,
                "structures": 10,
                "unratified_nonwarehouse_terms": 22,
            },
        )

    def test_all_dispositions_use_closed_vocabulary(self):
        allowed = {"KEEP", "REFINE", "REPLACE", "SUPERSEDE", "DEFER"}
        self.assertEqual(set(self.payload["classification_vocabulary"]), allowed)
        values = [row["classification"] for row in self.payload["system_reconciliation"]]
        for section in ("creatures", "plants", "blocks", "resources", "structures", "equipment"):
            values.extend(row["classification"] for row in self.payload[section])
        values.extend([self.payload["worldgen_budget"]["classification"], self.payload["boss_boundary"]["classification"], self.payload["codex_progression"]["classification"]])
        self.assertTrue(set(values) <= allowed)
        self.assertEqual(set(values), allowed)

    def test_approved_ids_are_exact_and_unique(self):
        expected = {
            "creatures": {row[0] for row in self.builder.CREATURES},
            "plants": {row[0] for row in self.builder.PLANTS},
            "blocks": set(self.builder.BLOCKS),
            "resources": {row[0] for row in self.builder.RESOURCES},
            "structures": {row[0] for row in self.builder.STRUCTURES},
            "equipment": {row[0] for row in self.builder.EQUIPMENT},
        }
        for section, ids in expected.items():
            actual = [row["id"] for row in self.payload[section]]
            self.assertEqual(set(actual), ids)
            self.assertEqual(len(actual), len(set(actual)))

    def test_source_target_ownership_never_conflicts(self):
        owners = defaultdict(set)

        def collect(value):
            if isinstance(value, dict):
                if set(value) >= {"path", "owner"}:
                    owners[value["path"]].add(value["owner"])
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(self.payload)
        conflicts = {path: sorted(value) for path, value in owners.items() if len(value) > 1}
        self.assertEqual(conflicts, {})

    def test_only_briar_ring_targets_exist_as_ashen_facing_equipment_at_base(self):
        present = {
            row["id"]: sorted(target["path"] for target in row["source_targets"] if target["present_at_base"])
            for row in self.payload["equipment"]
        }
        self.assertTrue(present["briar_ring"])
        self.assertTrue(all(not paths for asset_id, paths in present.items() if asset_id != "briar_ring"))
        self.assertEqual(next(row for row in self.payload["equipment"] if row["id"] == "briar_ring")["classification"], "KEEP")

    def test_kiln_sky_is_fail_closed(self):
        boss = self.payload["boss_boundary"]
        self.assertEqual(boss["classification"], "DEFER")
        self.assertEqual(next(row for row in self.payload["creatures"] if row["id"] == "ash_drake")["classification"], "SUPERSEDE")
        self.assertIn("phase thresholds", boss["nontransferable_from_thorn_court"])
        self.assertIn("repeat semantics", boss["nontransferable_from_thorn_court"])
        blocker_ids = {row["id"] for row in self.payload["blockers"] if row["blocking"]}
        self.assertEqual(
            blocker_ids,
            {"W1-CREATIVE-001-ASHEN", "W1-CREATIVE-003-KILN-SKY", "W1-CREATIVE-004-ASHEN", "PACKET-002-NATIVE-REPAIR"},
        )

    def test_worldgen_does_not_raise_console_target(self):
        budget = self.payload["worldgen_budget"]
        self.assertEqual(budget["global_natural_entities_target"], 40)
        self.assertEqual(budget["cap_change"], "NONE")
        drake = next(row for row in self.payload["creatures"] if row["id"] == "ash_drake")
        self.assertFalse(drake["spawn"]["natural"])
        self.assertEqual(sum(1 for row in self.payload["creatures"] if row["spawn"]["natural"]), 9)

    def test_repo_authority_hashes_match_exact_base(self):
        repo_authorities = [row for row in self.payload["authority"] if row["path"].startswith("engineering/")]
        for row in repo_authorities:
            content = subprocess.check_output(["git", "show", f'{self.payload["base"]["commit"]}:{row["path"]}'], cwd=ROOT)
            self.assertEqual(hashlib.sha256(content).hexdigest(), row["sha256"])

    def test_generator_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / "first.json"
            second = Path(folder) / "second.json"
            subprocess.run(["python3", str(GENERATOR_PATH), "--output", str(first)], cwd=ROOT, check=True, capture_output=True, text=True)
            subprocess.run(["python3", str(GENERATOR_PATH), "--output", str(second)], cwd=ROOT, check=True, capture_output=True, text=True)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first.read_bytes(), MAP_PATH.read_bytes())

    def test_proof_boundary_is_source_only(self):
        self.assertEqual(self.payload["proof_boundary"]["bp_rp_edits"], "NOT_PERFORMED")
        self.assertEqual(self.payload["proof_boundary"]["build"], "NOT_RUN")
        self.assertEqual(self.payload["proof_boundary"]["bds"], "NOT_RUN")
        self.assertEqual(self.payload["proof_boundary"]["runtime_behavior"], "NOT_PROVEN")


if __name__ == "__main__":
    unittest.main()
