from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from mccompiler.overrides import apply_overrides
from mccompiler.planner import plan_conversion
from mccompiler.scan import scan_path
from mccompiler.schema import validate_ir
from mccompiler.semantics import fingerprint
from mccompiler.bedrock import compile_bedrock


ROOT = Path(__file__).parent / "fixtures" / "representative_mod"


class SemanticCompilerTests(unittest.TestCase):
    def test_representative_fixture_has_grounded_semantics(self):
        ir = scan_path(ROOT)
        self.assertEqual([], validate_ir(ir))
        self.assertGreaterEqual(len(ir["content"]), 10)
        self.assertGreaterEqual(len(ir["behaviors"]), 15)
        self.assertTrue(all(b["evidence"] for b in ir["behaviors"]))
        self.assertIn("object_tick", {b["trigger"]["type"] for b in ir["behaviors"]})
        self.assertIn("state_transition", {b["trigger"]["type"] for b in ir["behaviors"]})
        self.assertEqual({"player", "item", "block", "entity"}, {s["scope"] for s in ir["state"]})
        self.assertIn("blade_charge", {s["id"] for s in ir["state"]})
        self.assertEqual(1, len(ir["unsupported_hooks"]))

    def test_fingerprint_equivalence_and_difference(self):
        behavior = scan_path(ROOT)["behaviors"][0]
        equivalent = deepcopy(behavior)
        equivalent["evidence"] = [{"source_file": "elsewhere", "start_line": 999}]
        equivalent["confidence"] = .2
        self.assertEqual(fingerprint(behavior)["sha256"], fingerprint(equivalent)["sha256"])
        different = deepcopy(behavior)
        different["actions"] = [{"type": "create_explosion"}]
        self.assertNotEqual(fingerprint(behavior)["sha256"], fingerprint(different)["sha256"])

    def test_override_is_persistent_and_explicit(self):
        ir = scan_path(ROOT)
        target = ir["behaviors"][0]["id"]
        apply_overrides(ir, {"schema_version": "1.0.0", "overrides": [{"target": target, "strategy": "MANUAL_REDESIGN", "provenance": {"author": "test", "reason": "review"}}]})
        feature = next(x for x in plan_conversion(ir)["features"] if x["id"] == target)
        self.assertEqual("MANUAL_REDESIGN", feature["classification"])
        self.assertIsNotNone(feature["override"])

    def test_override_identifier_state_omission_and_custom_module(self):
        ir = scan_path(ROOT)
        source = "export const reviewed = true;\n"
        document = {"schema_version": "1.0.0", "overrides": [
            {"target": "representative:bonus_crystal", "map_identifier": "representative:reviewed_crystal", "provenance": {"author": "test", "reason": "mapping"}},
            {"target": "energy", "state_storage": "world_dynamic_property_by_block_location", "provenance": {"author": "test", "reason": "storage"}},
            {"target": "representative:storm_orb/onImpact", "omit": True, "provenance": {"author": "test", "reason": "reviewed omission"}, "licensing_note": "fixture only",
             "custom_script_modules": [{"destination": "scripts/custom/reviewed.js", "source": source, "sha256": hashlib.sha256(source.encode()).hexdigest()}]},
        ]}
        apply_overrides(ir, document)
        self.assertIn("representative:reviewed_crystal", {x["identifier"] for x in ir["content"]})
        self.assertEqual("world_dynamic_property_by_block_location", next(x for x in ir["state"] if x["id"] == "energy")["storage_strategy"])
        plan = plan_conversion(ir)
        self.assertEqual("UNSUPPORTED", next(x for x in plan["features"] if x["id"] == "representative:storm_orb/onImpact")["classification"])
        with tempfile.TemporaryDirectory() as directory:
            compile_bedrock(ir, plan, directory)
            self.assertEqual(source, (Path(directory) / "behavior_pack/scripts/custom/reviewed.js").read_text())
            self.assertIn("import './custom/reviewed.js';", (Path(directory) / "behavior_pack/scripts/main.js").read_text())


if __name__ == "__main__":
    unittest.main()
