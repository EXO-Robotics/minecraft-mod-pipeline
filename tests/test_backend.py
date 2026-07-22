from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from mccompiler.bedrock import compile_bedrock
from mccompiler.planner import plan_conversion
from mccompiler.validate import validate_output


def ev() -> list[dict[str, object]]:
    return [{"source_file": "Fixture.java", "start_line": 1, "end_line": 1, "extraction_rule": "test", "confidence": 1.0}]


class BackendTests(unittest.TestCase):
    def fixture(self) -> tuple[dict, dict]:
        ir = {"schema_version": "1.0.0", "metadata": {"id": "demo"}, "mods": [{"id": "demo"}], "dependencies": [], "content": [{"kind": "item", "identifier": "demo:wand", "properties": {}, "evidence": ev()}, {"kind": "block", "identifier": "demo:machine", "properties": {}, "evidence": ev()}, {"kind": "recipe", "identifier": "demo:wand_recipe", "properties": {"result": "demo:wand"}, "evidence": ev()}, {"kind": "entity", "identifier": "demo:golem", "properties": {}, "evidence": ev()}, {"kind": "structure", "identifier": "demo:arena", "properties": {}, "evidence": ev()}], "assets": [], "behaviors": [{"id": "demo:wand/use", "owner": {"kind": "item", "identifier": "demo:wand"}, "trigger": {"type": "item_use"}, "conditions": [], "actions": [{"type": "send_player_feedback"}], "evidence": ev(), "confidence": 1.0, "diagnostics": []}, {"id": "demo:ghost", "owner": {}, "trigger": {"type": "item_use"}, "conditions": [], "actions": [{"type": "damage"}], "evidence": [], "confidence": 1.0, "diagnostics": []}], "state": [{"id": "charge", "scope": "player", "value_type": "number", "default": 0, "persistence": "persistent", "evidence": ev()}], "presentation_requirements": [], "ui_intent": [{"id": "machine", "title": "Machine", "purpose": "Process", "controls": ["Start"], "evidence": ev()}], "networking_intent": [], "unsupported_hooks": [{"feature": "mixin", "evidence": ev()}], "tests": [], "target": {"script_api_version": "2.0.0", "version_markers": ["1.21.90"]}}
        return ir, plan_conversion(ir)

    def test_deterministic_modular_output_and_validation(self):
        ir, plan = self.fixture()
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first, second = compile_bedrock(ir, plan, a), compile_bedrock(ir, plan, b)
            self.assertEqual(hashlib.sha256(first.read_bytes()).digest(), hashlib.sha256(second.read_bytes()).digest())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.namelist(), sorted(archive.namelist()))
                self.assertIn("behavior_pack/scripts/runtime/state.js", archive.namelist())
                self.assertIn("scripts/runtime/state.js", archive.namelist())
                self.assertIn("reports/provenance.json", archive.namelist())
            self.assertIn("c.block?.location||c.location", (Path(a) / "behavior_pack/scripts/runtime/actions.js").read_text())
            self.assertIn("location:p", (Path(a) / "behavior_pack/scripts/tests/contracts.js").read_text())
            result = validate_output(a, plan)
            self.assertTrue(result["valid"], result)
            self.assertEqual(result["layers"]["runtime"]["status"], "not-run")

    def test_evidence_gate_and_explicit_reporting(self):
        ir, plan = self.fixture()
        with tempfile.TemporaryDirectory() as output:
            compile_bedrock(ir, plan, output)
            behavior_plan = json.loads((Path(output) / "tests/behavior-plan.json").read_text())
            self.assertIn("demo:wand/use", behavior_plan["approved"])
            self.assertEqual(behavior_plan["omitted"][0]["id"], "demo:ghost")
            report = json.loads((Path(output) / "reports/unsupported-and-approximations.json").read_text())
            self.assertTrue(report["unsupported"])

    def test_shaped_recipe_preserves_pattern_key_and_result(self):
        ir, _ = self.fixture()
        ir["content"].append({
            "kind": "recipe", "identifier": "demo:golden_wand_recipe",
            "properties": {
                "recipe_type": "shaped", "pattern": ["TGG", "  G"],
                "key": {"T": "minecraft:tripwire_hook", "G": "minecraft:gold_nugget"},
                "result": "demo:wand",
            },
            "evidence": ev(),
        })
        plan = plan_conversion(ir)
        with tempfile.TemporaryDirectory() as output:
            compile_bedrock(ir, plan, output)
            recipe = json.loads((Path(output) / "behavior_pack/recipes/demo_golden_wand_recipe.json").read_text())
        body = recipe["minecraft:recipe_shaped"]
        self.assertEqual("1.26.0", recipe["format_version"])
        self.assertEqual(["TGG", "  G"], body["pattern"])
        self.assertEqual({"item": "minecraft:gold_nugget"}, body["key"]["G"])
        self.assertEqual("demo:wand", body["result"]["item"])
        self.assertEqual(
            [{"item": "minecraft:gold_nugget"}, {"item": "minecraft:tripwire_hook"}],
            body["unlock"],
        )

    def test_validator_detects_archive_tampering(self):
        ir, plan = self.fixture()
        with tempfile.TemporaryDirectory() as output:
            archive = compile_bedrock(ir, plan, output)
            with zipfile.ZipFile(archive, "a") as bundle:
                bundle.writestr("zzz.txt", "tampered")
            result = validate_output(output, plan)
            self.assertFalse(result["valid"])
            self.assertTrue(any("Archive" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
