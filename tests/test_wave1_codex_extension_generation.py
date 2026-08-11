import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "engineering/whisperwood-intake/codex-extension/generate_codex_extension_data.py"
MAP = GENERATOR.with_name("WHISPERWOOD_CODEX_EXTENSION_MAP.json")
TARGET = ROOT / "behavior_pack/scripts/wave1_codex_extension_data.js"


class WhisperwoodCodexExtensionGenerationTests(unittest.TestCase):
    def test_generated_runtime_data_is_current(self):
        spec = importlib.util.spec_from_file_location("wave1_codex_extension_generator", GENERATOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(TARGET.read_text(), module.render(json.loads(MAP.read_text())))


if __name__ == "__main__":
    unittest.main()
