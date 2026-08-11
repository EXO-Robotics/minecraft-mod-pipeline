import importlib.util
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "engineering/whisperwood-intake/plant-runtime/validate_whisperwood_plants.py"
sys.path.insert(0, str(VALIDATOR.parent))
SPEC = importlib.util.spec_from_file_location("validate_whisperwood_plants", VALIDATOR)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WhisperwoodPlantRuntimeTest(unittest.TestCase):
    def test_all_ten_plants_close_statically(self):
        report = MODULE.validate(REPO)
        self.assertEqual(report["status"], "PASS_STATIC_REFERENCE_CLOSURE")
        self.assertEqual(report["asset_count"], 10)
        self.assertEqual(len({entry["runtime_id"] for entry in report["assets"]}), 10)

    def test_animations_are_explicitly_withheld(self):
        report = MODULE.validate(REPO)
        self.assertEqual(report["animation_policy"]["runtime_playback"], "WITHHELD")
        animated = [entry for entry in report["assets"] if entry["source_animation"]]
        self.assertEqual(len(animated), 4)
        self.assertTrue(all(entry["runtime_animation"].startswith("WITHHELD_") for entry in animated))


if __name__ == "__main__":
    unittest.main()
