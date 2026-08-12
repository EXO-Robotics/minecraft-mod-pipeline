#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import author_skyreach_structures as author  # noqa: E402


class SkyreachStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((HERE / "SKYREACH_STRUCTURE_ASSEMBLIES.json").read_text())

    def test_exact_distinct_roster(self) -> None:
        ids = [row["id"] for row in self.manifest["assemblies"]]
        self.assertEqual(ids, [a.identifier for a in author.ASSEMBLIES])
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        self.assertEqual(len({row["structure_sha256"] for row in self.manifest["assemblies"]}), 10)

    def test_templates_are_inert_and_no_deferred_identity_leaks(self) -> None:
        forbidden = {"minecraft:barrel", "minecraft:chest", "minecraft:trapped_chest", "minecraft:lectern", "minecraft:lodestone"}
        for row in self.manifest["assemblies"]:
            self.assertEqual(row["block_position_data"], "EMPTY_NO_BLOCK_ENTITY_NBT")
            self.assertTrue(forbidden.isdisjoint(row["palette"]), row["id"])
            raw = (ROOT / row["structure_path"]).read_bytes()
            for term in (b"loot", b"reward", b"seal", b"storm_pinion", b"wind_roc"):
                self.assertNotIn(term, raw.lower(), (row["id"], term))

    def test_palette_references_defined_blocks(self) -> None:
        defined = set()
        for path in (ROOT / "behavior_pack/blocks").glob("*.json"):
            doc = json.loads(path.read_text())
            defined.add(doc["minecraft:block"]["description"]["identifier"])
        for row in self.manifest["assemblies"]:
            for block in row["palette"]:
                if block.startswith("aionbound:"):
                    self.assertIn(block, defined, (row["id"], block))

    def test_feature_and_rule_closure(self) -> None:
        for row in self.manifest["assemblies"]:
            feature = json.loads((ROOT / row["feature_path"]).read_text())["minecraft:structure_template_feature"]
            rule = json.loads((ROOT / row["feature_rule_path"]).read_text())["minecraft:feature_rules"]
            self.assertEqual(feature["structure_name"], f"aionbound:skyreach/{row['id']}")
            self.assertEqual(rule["description"]["places_feature"], feature["description"]["identifier"])
            filters = json.dumps(rule["conditions"])
            self.assertIn("mountain", filters)
            self.assertIn("hills", filters)
            self.assertNotIn("swamp", filters)

    def test_density_is_bounded_and_not_registry_scaled(self) -> None:
        attempts = self.manifest["aggregate_expected_attempts_per_256_chunks_before_filters"]
        self.assertGreater(attempts, 0)
        self.assertLess(attempts, 1.0)
        denominators = [row["scatter"]["denominator"] for row in self.manifest["assemblies"]]
        self.assertEqual(len(set(denominators)), 10)
        self.assertGreaterEqual(min(denominators), 1024)

    def test_generator_is_deterministic(self) -> None:
        result = subprocess.run([sys.executable, str(HERE / "author_skyreach_structures.py"), "--check"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
