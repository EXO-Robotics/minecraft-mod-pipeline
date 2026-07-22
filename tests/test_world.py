from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from mccompiler.world import compute_pack_hash, generate_test_world


def make_pack(root: Path, name: str, uuid: str, module_type: str) -> Path:
    root.mkdir(parents=True)
    manifest = {
        "format_version": 2,
        "header": {"name": name, "description": "test", "uuid": uuid, "version": [1, 2, 3], "min_engine_version": [1, 21, 0]},
        "modules": [{"type": module_type, "uuid": uuid[::-1], "version": [1, 2, 3]}],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "nested").mkdir()
    (root / "nested" / "content.json").write_text('{"ok":true}\n', encoding="utf-8")
    return root


class TestWorldTests(unittest.TestCase):
    def test_mcworld_is_deterministic_embeds_and_binds_both_packs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bp = make_pack(root / "bp", "Demo BP", "11111111-1111-1111-1111-111111111111", "data")
            rp = make_pack(root / "rp", "Demo RP", "22222222-2222-2222-2222-222222222222", "resources")
            first = generate_test_world(bp, rp, root / "first.mcworld")
            second = generate_test_world(bp, rp, root / "second.mcworld")
            self.assertEqual((root / "first.mcworld").read_bytes(), (root / "second.mcworld").read_bytes())
            self.assertEqual(first["pack_hash"], second["pack_hash"])
            self.assertEqual(first["world_hash"], hashlib.sha256((root / "first.mcworld").read_bytes()).hexdigest())
            with zipfile.ZipFile(root / "first.mcworld") as archive:
                names = archive.namelist()
                self.assertIn("level.dat", names)
                self.assertIn("levelname.txt", names)
                self.assertTrue(any(name.startswith("behavior_packs/Demo_BP-") and name.endswith("/manifest.json") for name in names))
                self.assertTrue(any(name.startswith("resource_packs/Demo_RP-") and name.endswith("/manifest.json") for name in names))
                behavior_binding = json.loads(archive.read("world_behavior_packs.json"))
                resource_binding = json.loads(archive.read("world_resource_packs.json"))
                self.assertEqual("11111111-1111-1111-1111-111111111111", behavior_binding[0]["pack_id"])
                self.assertEqual([1, 2, 3], resource_binding[0]["version"])
                version, payload_size = __import__("struct").unpack("<II", archive.read("level.dat")[:8])
                self.assertEqual(8, version)
                self.assertEqual(len(archive.read("level.dat")) - 8, payload_size)

    def test_pack_hash_changes_with_pack_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bp = make_pack(root / "bp", "BP", "11111111-1111-1111-1111-111111111111", "data")
            rp = make_pack(root / "rp", "RP", "22222222-2222-2222-2222-222222222222", "resources")
            before = compute_pack_hash(bp, rp)
            (bp / "nested" / "content.json").write_text('{"ok":false}\n', encoding="utf-8")
            self.assertNotEqual(before, compute_pack_hash(bp, rp))

    def test_invalid_pack_and_output_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bp = make_pack(root / "bp", "BP", "11111111-1111-1111-1111-111111111111", "data")
            rp = root / "rp"; rp.mkdir(); (rp / "manifest.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "Invalid resource pack manifest"):
                generate_test_world(bp, rp, root / "test.mcworld")
            valid_rp = make_pack(root / "valid-rp", "RP", "22222222-2222-2222-2222-222222222222", "resources")
            with self.assertRaisesRegex(ValueError, r"\.mcworld"):
                generate_test_world(bp, valid_rp, root / "test.zip")


if __name__ == "__main__":
    unittest.main()
