from __future__ import annotations

import unittest

from validate_runtime_a import check


class WhisperwoodEquipmentRuntimeATest(unittest.TestCase):
    def test_exact_source_and_reference_closure(self) -> None:
        report = check()
        self.assertEqual(report["status"], "PASS_WITH_EXTERNAL_ICON_HANDOFF")
        self.assertEqual(len(report["assets"]), 8)


if __name__ == "__main__":
    unittest.main()
