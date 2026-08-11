from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "engineering/test-evidence/derive_receipt.py"
SPEC = importlib.util.spec_from_file_location("derive_receipt", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def observation(actual: int = 14) -> dict:
    return {
        "schema": "aionbound.engineering-evidence-input.v1",
        "candidate": {
            "id": "AIONBOUND_WAVE_1_TEST",
            "commit": "1" * 40,
            "tree": "2" * 40,
            "mcaddon_sha256": "3" * 64,
        },
        "checks": [{
            "id": "runtime-semantics",
            "required": True,
            "command": ["node", "--test", "tests/runtime.test.mjs"],
            "exit_code": 0,
            "assertions": [{"name": "passing-tests", "expected": 14, "actual": actual}],
            "evidence_files": ["runtime.tap"],
        }],
    }


class EvidenceDerivedReceiptTest(unittest.TestCase):
    def test_status_and_file_hash_are_derived(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evidence = root / "runtime.tap"
            evidence.write_text("1..14\n# pass 14\n")
            receipt = MODULE.derive(observation(), root)
            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual(receipt["checks"][0]["status"], "PASS")
            self.assertEqual(receipt["checks"][0]["evidence_files"][0]["size"], evidence.stat().st_size)
            self.assertEqual(len(receipt["checks"][0]["evidence_files"][0]["sha256"]), 64)

            failed = MODULE.derive(observation(actual=13), root)
            self.assertEqual(failed["status"], "FAIL")
            self.assertFalse(failed["checks"][0]["assertions"][0]["matched"])

    def test_supplied_status_and_missing_evidence_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            supplied = observation()
            supplied["status"] = "PASS"
            with self.assertRaisesRegex(ValueError, "may not supply"):
                MODULE.derive(supplied, root)
            with self.assertRaisesRegex(ValueError, "missing evidence file"):
                MODULE.derive(observation(), root)

    def test_output_schema_is_parseable_and_rejects_extra_top_level_fields(self):
        schema = json.loads((ROOT / "engineering/test-evidence/evidence-receipt.schema.json").read_text())
        self.assertEqual(schema["properties"]["schema"]["const"], "aionbound.engineering-evidence-receipt.v1")
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
