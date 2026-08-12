from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


MODULE_PATH = Path(__file__).with_name("verify_preview.py")
SPEC = importlib.util.spec_from_file_location("verify_preview", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class PreviewVerifierTest(unittest.TestCase):
    def test_png_rejects_bad_crc(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.validate_png(b"\x89PNG\r\n\x1a\n" + b"\0" * 12)

    def test_safe_member_rejects_traversal(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.safe_member("../outside")

    def test_manifest_state_remains_non_candidate(self) -> None:
        self.assertIn("NOT_FROZEN_NOT_QUALIFIED", MODULE.EXPECTED_STATE)
        self.assertIn("not_an_immutable_candidate", MODULE.PROOF_BOUNDARIES)


if __name__ == "__main__":
    unittest.main()
