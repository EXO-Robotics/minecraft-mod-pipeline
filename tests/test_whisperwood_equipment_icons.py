import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "assets/wave1/whisperwood/equipment-icons/build_receipt.py"
SPEC = importlib.util.spec_from_file_location("equipment_icons", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WhisperwoodEquipmentIconTests(unittest.TestCase):
    def test_receipt_is_derived_from_exact_decodable_bytes(self):
        expected = MODULE.build()
        committed = json.loads(MODULE.OUT.read_text())
        self.assertEqual(expected, committed)
        self.assertEqual(expected["status"], "PASS_STATIC_PRESENTATION")
        self.assertEqual(expected["icon_count"], 21)

    def test_exact_packet006_whisperwood_category_counts(self):
        receipt = MODULE.build()
        counts = {}
        for icon in receipt["icons"]:
            counts[icon["category"]] = counts.get(icon["category"], 0) + 1
            self.assertEqual(icon["visible_magenta_pixel_count"], 0)
            self.assertEqual(icon["transparent_corner_alpha"], [0, 0, 0, 0])
        self.assertEqual(counts, {"weapons": 5, "armor": 4, "tools": 3, "accessories": 5, "trophies": 4})


if __name__ == "__main__":
    unittest.main()
