from __future__ import annotations

import io
import hashlib
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.factory.safe_extract_outer_archive import OuterArchiveError, safe_extract


class SafeOuterArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self) -> None:
        for path in sorted(self.root.rglob("*"), reverse=True):
            path.chmod(0o755 if path.is_dir() else 0o644)
        self.temporary.cleanup()

    def _archive(self, rows: list[tuple[str, bytes]]) -> Path:
        target = self.root / "fixture.zip"
        with zipfile.ZipFile(target, "w") as archive:
            for name, data in rows:
                archive.writestr(name, data)
        return target

    def _extract(self, source: Path):
        return safe_extract(
            source,
            self.root / "oracle",
            self.root / "inventory.json",
            expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            expected_bytes=source.stat().st_size,
        )

    def test_nested_archive_with_duplicate_member_remains_opaque(self) -> None:
        nested = io.BytesIO()
        with zipfile.ZipFile(nested, "w") as archive:
            archive.writestr("duplicate.txt", b"one")
            archive.writestr("duplicate.txt", b"two")
        source = self._archive([("mods/nested.jar", nested.getvalue())])
        result = self._extract(source)
        self.assertFalse(result["nested_archives_opened"])
        self.assertEqual(result["file_count"], 1)
        self.assertEqual(
            (self.root / "oracle/mods/nested.jar").read_bytes(),
            nested.getvalue(),
        )

    def test_rejects_outer_duplicate_member(self) -> None:
        source = self._archive([("same.txt", b"one"), ("same.txt", b"two")])
        with self.assertRaisesRegex(OuterArchiveError, "duplicate outer"):
            self._extract(source)

    def test_rejects_traversal_and_portable_collision(self) -> None:
        source = self._archive([("../escape.txt", b"bad")])
        with self.assertRaisesRegex(OuterArchiveError, "unsafe outer"):
            self._extract(source)

        source.unlink()
        source = self._archive([("Case.txt", b"one"), ("case.txt", b"two")])
        with self.assertRaisesRegex(OuterArchiveError, "portable outer"):
            self._extract(source)

    def test_rejects_outer_symlink(self) -> None:
        source = self.root / "fixture.zip"
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr(info, "target")
        with self.assertRaisesRegex(OuterArchiveError, "symlink"):
            self._extract(source)

    def test_rejects_authority_hash_or_size_mismatch(self) -> None:
        source = self._archive([("safe.txt", b"safe")])
        with self.assertRaisesRegex(OuterArchiveError, "SHA-256 mismatch"):
            safe_extract(
                source,
                self.root / "oracle",
                self.root / "inventory.json",
                expected_sha256="0" * 64,
                expected_bytes=source.stat().st_size,
            )
        with self.assertRaisesRegex(OuterArchiveError, "byte length mismatch"):
            safe_extract(
                source,
                self.root / "oracle",
                self.root / "inventory.json",
                expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                expected_bytes=source.stat().st_size + 1,
            )


if __name__ == "__main__":
    unittest.main()
