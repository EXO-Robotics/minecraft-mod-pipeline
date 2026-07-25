from __future__ import annotations

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from mccompiler.scan import scan_path


class ScanHashTests(unittest.TestCase):
    def test_archive_scan_distinguishes_artifact_and_semantic_content_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stored = root / "stored.jar"
            deflated = root / "deflated.jar"
            entries = {
                "META-INF/MANIFEST.MF": b"Manifest-Version: 1.0\n",
                "assets/example/lang/en_us.json": b'{"item.example.test":"Test"}\n',
            }

            for archive, compression in (
                (stored, zipfile.ZIP_STORED),
                (deflated, zipfile.ZIP_DEFLATED),
            ):
                with zipfile.ZipFile(archive, "w", compression=compression) as bundle:
                    for name, payload in entries.items():
                        bundle.writestr(name, payload)

            stored_input = scan_path(stored)["input"]
            deflated_input = scan_path(deflated)["input"]

            self.assertNotEqual(stored.read_bytes(), deflated.read_bytes())
            self.assertEqual(
                hashlib.sha256(stored.read_bytes()).hexdigest(),
                stored_input["artifact_sha256"],
            )
            self.assertEqual(
                hashlib.sha256(deflated.read_bytes()).hexdigest(),
                deflated_input["artifact_sha256"],
            )
            self.assertNotEqual(
                stored_input["artifact_sha256"],
                deflated_input["artifact_sha256"],
            )
            self.assertEqual(
                stored_input["content_sha256"],
                deflated_input["content_sha256"],
            )
            self.assertEqual(stored_input["content_sha256"], stored_input["sha256"])
            self.assertEqual("content_sha256", stored_input["sha256_alias_of"])

            source = scan_path(stored)["mods"][0]["source"]
            self.assertEqual(stored_input["artifact_sha256"], source["artifact_sha256"])
            self.assertEqual(stored_input["content_sha256"], source["content_sha256"])
            self.assertEqual(source["content_sha256"], source["sha256"])
            self.assertEqual("content_sha256", source["sha256_alias_of"])

    def test_directory_scan_labels_semantic_hash_without_artifact_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "example.txt").write_text("example\n", encoding="utf-8")

            input_identity = scan_path(root)["input"]

            self.assertEqual("directory", input_identity["kind"])
            self.assertNotIn("artifact_sha256", input_identity)
            self.assertEqual(input_identity["content_sha256"], input_identity["sha256"])
            self.assertEqual("content_sha256", input_identity["sha256_alias_of"])


if __name__ == "__main__":
    unittest.main()
