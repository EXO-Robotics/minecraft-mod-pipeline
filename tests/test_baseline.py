from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mccompiler.bedrock import compile_bedrock
from mccompiler.planner import plan_conversion
from mccompiler.scan import scan_path
from mccompiler.validate import validate_output


FIXTURE = Path(__file__).parent / "fixtures" / "example-mod"


class BaselineTests(unittest.TestCase):
    def test_scan_fabric_source_tree(self):
        ir = scan_path(FIXTURE)
        self.assertEqual(ir["mods"][0]["id"], "example_mod")
        self.assertEqual(ir["mods"][0]["loader"], "fabric")
        self.assertEqual(ir["aggregate"]["source_signals"]["item_interactions"], 1)
        self.assertIn("item_interactions", ir["aggregate"]["source_signals"])


    def test_compile_and_validate(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            ir = scan_path(FIXTURE)
            plan = plan_conversion(ir)
            archive = compile_bedrock(ir, plan, output)
            result = validate_output(archive.parent)
            self.assertTrue(result["valid"])
            self.assertTrue(archive.exists())
            self.assertTrue(json.loads((archive.parent / "behavior_pack" / "manifest.json").read_text())["modules"])
