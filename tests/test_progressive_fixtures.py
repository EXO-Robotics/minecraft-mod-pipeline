from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mccompiler.bedrock import compile_bedrock
from mccompiler.planner import plan_conversion
from mccompiler.scan import scan_path


ROOT = Path(__file__).parent / "fixtures" / "progressive"


class ProgressiveFixtureTests(unittest.TestCase):
    maxDiff = None

    def cases(self):
        paths = sorted(path for path in ROOT.iterdir() if path.is_dir())
        self.assertEqual([f"{number:02d}" for number in range(1, 19)], [path.name[:2] for path in paths])
        for path in paths:
            with (path / "expected.json").open(encoding="utf-8") as handle:
                yield path, json.load(handle)

    def test_progressive_source_analysis_and_planning(self):
        for path, expected in self.cases():
            with self.subTest(fixture=path.name):
                ir = scan_path(path)
                plan = plan_conversion(ir)
                content = {(row["kind"], row["identifier"]) for row in ir["content"]}
                self.assertTrue({tuple(row) for row in expected["content"]} <= content)
                behaviors = ir["behaviors"]
                self.assertEqual(set(expected.get("triggers", [])), {row["trigger"]["type"] for row in behaviors})
                self.assertEqual(set(expected.get("actions", [])), {action["type"] for row in behaviors for action in row["actions"]})
                self.assertEqual(set(expected.get("conditions", [])), {condition["type"] for row in behaviors for condition in row["conditions"]})
                self.assertEqual(expected.get("behavior_count", len(behaviors)), len(behaviors))
                self.assertTrue(all(row["evidence"] for row in ir["content"] + behaviors))
                self.assertEqual({tuple(row) for row in expected.get("state", [])}, {(row["id"], row["scope"], row["persistence"]) for row in ir["state"]})
                self.assertEqual(set(expected.get("ui", [])), {row["id"] for row in ir["ui_intent"]})
                self.assertEqual(set(expected.get("networking", [])), {row["id"] for row in ir["networking_intent"]})
                self.assertEqual({tuple(row) for row in expected["diagnostics"]}, {(row["code"], row.get("feature")) for row in ir["diagnostics"]})
                self.assertEqual(set(expected["patterns"]), {row["id"] for row in plan["patterns"]})
                by_id = {}
                for feature in plan["features"]:
                    by_id.setdefault(feature["id"], set()).add(feature["classification"])
                for identifier, classification in expected["classifications"].items():
                    self.assertIn(classification, by_id.get(identifier, set()), identifier)
                unsupported = sum(1 for row in plan["features"] if row["classification"] in {"UNSUPPORTED", "MANUAL_REDESIGN"})
                approximations = sum(1 for row in plan["features"] if "APPROXIMATION" in row["classification"])
                self.assertEqual(expected["report"], {"unsupported": unsupported, "approximations": approximations})

    def test_expected_bedrock_generation(self):
        for path, expected in self.cases():
            with self.subTest(fixture=path.name), tempfile.TemporaryDirectory() as temp:
                ir = scan_path(path)
                plan = plan_conversion(ir)
                output = Path(temp) / "output"
                archive = compile_bedrock(ir, plan, output)
                self.assertTrue(archive.is_file())
                manifest = json.loads((output / "conversion-manifest.json").read_text(encoding="utf-8"))
                generated = {row["kind"] for row in manifest["generated"]}
                omitted = {row["kind"] for row in manifest["omitted"]}
                self.assertTrue(set(expected["bedrock"].get("generated_kinds", [])) <= generated)
                self.assertTrue(set(expected["bedrock"].get("omitted_kinds", [])) <= omitted)
                self.assertTrue((output / "reports" / "conversion-report.md").is_file())
                self.assertTrue((output / "reports" / "unsupported-and-approximations.json").is_file())

    def test_semantic_equivalence_and_material_difference(self):
        equivalent_path = ROOT / "13_semantic_equivalence"
        different_path = ROOT / "14_material_difference"
        equivalent_expected = json.loads((equivalent_path / "expected.json").read_text(encoding="utf-8"))
        different_expected = json.loads((different_path / "expected.json").read_text(encoding="utf-8"))
        self.assertEqual("equal", equivalent_expected["fingerprint_relation"])
        self.assertEqual("different", different_expected["fingerprint_relation"])
        equivalent = scan_path(equivalent_path)["behaviors"]
        different = scan_path(different_path)["behaviors"]
        self.assertEqual(2, len(equivalent))
        self.assertEqual(equivalent[0]["fingerprint"]["sha256"], equivalent[1]["fingerprint"]["sha256"])
        self.assertEqual(2, len(different))
        self.assertNotEqual(different[0]["fingerprint"]["sha256"], different[1]["fingerprint"]["sha256"])


if __name__ == "__main__":
    unittest.main()
