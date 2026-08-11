import json
import subprocess
import unittest
from pathlib import Path

from author_ashen_audio import ROOT, ROWS, SOUNDS


class AshenAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(Path(__file__).with_name("author_ashen_audio.py"))], cwd=ROOT, check=True)

    def test_exact_ten_entities_have_three_reviewed_events(self):
        entities = json.loads(SOUNDS.read_text())["entity_sounds"]["entities"]
        for asset in ROWS:
            row = entities[f"aionbound:{asset}"]
            self.assertEqual(set(row["events"]), {"ambient", "hurt", "death"})
            self.assertTrue(all(value.startswith("mob.") for value in row["events"].values()))

    def test_ambient_intervals_are_bounded_and_distinct(self):
        signatures = set()
        for asset in ROWS:
            entity = json.loads((ROOT / f"behavior_pack/entities/aionbound/ashen/{asset}.entity.json").read_text())["minecraft:entity"]
            interval = entity["components"]["minecraft:ambient_sound_interval"]
            self.assertEqual(interval["event_name"], "ambient")
            self.assertTrue(6 <= interval["value"] <= 18)
            self.assertTrue(8 <= interval["range"] <= 16)
            signatures.add((interval["value"], interval["range"]))
        self.assertGreaterEqual(len(signatures), 8)

    def test_no_custom_audio_bytes_or_signature_cue_claim(self):
        audio = [p for p in (ROOT / "resource_pack").rglob("*") if p.suffix.lower() in {".ogg", ".wav", ".fsb"}]
        self.assertEqual(audio, [])


if __name__ == "__main__":
    unittest.main()
