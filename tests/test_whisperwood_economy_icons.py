import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "assets/wave1/whisperwood/economy-icons/build_receipt.py"
SPEC = importlib.util.spec_from_file_location("economy_icons", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class WhisperwoodEconomyIconTests(unittest.TestCase):
    def test_receipt_is_derived_from_exact_decodable_bytes(self):
        expected = MODULE.build()
        committed = json.loads(MODULE.OUT.read_text())
        self.assertEqual(expected, committed)
        self.assertEqual(9, expected["call_count"])
        self.assertEqual(9, len(expected["icons"]))

    def test_all_shipping_icons_are_clean_distinct_rgba(self):
        receipt = MODULE.build()
        shipping_hashes = set()
        for icon in receipt["icons"]:
            self.assertEqual([32, 32], icon["shipping_size"])
            self.assertEqual([0, 0, 0, 0], icon["transparent_corner_alpha"])
            self.assertEqual(0, icon["visible_magenta_pixel_count"])
            shipping_hashes.add(icon["shipping_sha256"])
        self.assertEqual(9, len(shipping_hashes))


if __name__ == "__main__":
    unittest.main()
