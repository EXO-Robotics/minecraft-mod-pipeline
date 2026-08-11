import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILDER = HERE / "build_ashen_codex_runtime.py"
TARGET = ROOT / "behavior_pack/scripts/wave1_codex_ashen_data.js"


def load_builder():
    spec = importlib.util.spec_from_file_location("ashen_codex_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AshenCodexRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()
        cls.rows = cls.builder.build()

    def test_exact_append_only_coverage(self):
        self.assertEqual(len(self.rows), 66)
        self.assertEqual(len([r for r in self.rows if r["kind"] == "equipment"]), 13)
        self.assertNotIn("briar_ring", {r["id"] for r in self.rows})

    def test_region_local_indices_and_caps(self):
        caps = {"resource": 20, "plant": 10, "creature": 10, "structure": 10, "equipment": 21, "boss": 1, "progression": 2}
        for category, cap in caps.items():
            rows = [r for r in self.rows if r["category"] == category]
            self.assertEqual([r["categoryIndex"] for r in rows], list(range(len(rows))))
            self.assertLessEqual(len(rows), cap)

    def test_horn_is_critical_and_core_is_optional_text(self):
        boss = next(r for r in self.rows if r["id"] == "kiln_sky")
        self.assertEqual(boss["authorityText"]["chapter_seal"], "aionbound:ash_drake_horn")
        self.assertEqual(boss["authorityText"]["optional_mastery_reward"], "aionbound:ember_forge_core")

    def test_all_event_ids_unique(self):
        ids = [e["id"] for r in self.rows for e in r["events"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_generation_is_byte_deterministic(self):
        before = TARGET.read_bytes()
        subprocess.run(["python3", str(BUILDER)], cwd=ROOT, check=True)
        self.assertEqual(TARGET.read_bytes(), before)
        self.assertEqual(len(hashlib.sha256(before).hexdigest()), 64)


if __name__ == "__main__":
    unittest.main()
