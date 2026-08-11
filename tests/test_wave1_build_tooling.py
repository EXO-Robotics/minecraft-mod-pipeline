"""Bounded tests for successor-safe deterministic workspace packaging."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("wave1_build", ROOT / "tools/build.py")
assert SPEC and SPEC.loader
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


def write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def fixture(root: Path) -> None:
    manifest = {
        "format_version": 2,
        "modules": [
            {"type": "data", "uuid": "00000000-0000-0000-0000-000000000001", "version": [1, 0, 0]},
            {
                "type": "script",
                "language": "javascript",
                "entry": "scripts/main.js",
                "uuid": "00000000-0000-0000-0000-000000000002",
                "version": [1, 0, 0],
            },
        ],
    }
    write(root / "behavior_pack/manifest.json", (json.dumps(manifest) + "\n").encode())
    write(root / "behavior_pack/scripts/main.js", b'console.warn("runtime-ready-g8");\n')
    write(root / "behavior_pack/items/test.json", b'{"format_version":"1.21.80"}\n')
    write(root / "resource_pack/manifest.json", b'{"format_version":2}\n')
    write(root / "resource_pack/textures/test.bin", b"wave1-texture")


class Wave1BuildToolingTests(unittest.TestCase):
    def test_successor_names_cannot_overwrite_g7(self):
        names = BUILD.output_names()
        self.assertTrue(all("g8" in value for value in names.values()))
        self.assertTrue(all("g7" not in value.lower() for value in names.values()))
        self.assertEqual(BUILD.GENERATION, 8)

    def test_build_twice_is_byte_identical_and_ledgers_every_source_byte(self):
        with tempfile.TemporaryDirectory(prefix="wave1-builder-test-") as temporary:
            temporary = Path(temporary)
            source = temporary / "source"
            first = temporary / "first"
            second = temporary / "second"
            fixture(source)

            result = BUILD.build_twice_and_compare(source, first, second)
            self.assertTrue(result["build_1_equals_build_2"])
            self.assertEqual(result["state"], "DETERMINISTIC_BUILD_COMPARISON_PASS")

            names = BUILD.output_names()
            for key in ("behavior", "resources", "addon", "ledger", "manifest"):
                self.assertEqual((first / names[key]).read_bytes(), (second / names[key]).read_bytes())

            ledger = json.loads((first / names["ledger"]).read_text())
            expected = sorted(
                path.relative_to(source).as_posix()
                for pack in (source / "behavior_pack", source / "resource_pack")
                for path in pack.rglob("*") if path.is_file()
            )
            self.assertEqual([row["path"] for row in ledger["entries"]], expected)
            self.assertEqual(ledger["member_count"], len(expected))

    def test_manifest_addresses_exact_nested_shipped_entrypoint(self):
        with tempfile.TemporaryDirectory(prefix="wave1-entrypoint-test-") as temporary:
            temporary = Path(temporary)
            source = temporary / "source"
            output = temporary / "output"
            fixture(source)
            manifest = BUILD.build_once(source, output)
            names = BUILD.output_names()
            address = manifest["packaged_entrypoint"]
            self.assertEqual(
                address["address"],
                f'{names["addon"]}!/{names["behavior"]}!/scripts/main.js',
            )

            with zipfile.ZipFile(output / names["addon"]) as addon:
                behavior_bytes = addon.read(address["behavior_mcpack_member"])
            import io
            with zipfile.ZipFile(io.BytesIO(behavior_bytes)) as behavior:
                shipped = behavior.read(address["entrypoint_member"])
            self.assertEqual(BUILD.sha256_bytes(shipped), address["sha256"])

    def test_missing_or_ambiguous_script_entrypoint_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="wave1-entrypoint-fail-") as temporary:
            source = Path(temporary) / "source"
            fixture(source)
            manifest_path = source / "behavior_pack/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["modules"].append({"type": "script", "entry": "scripts/other.js"})
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "exactly one"):
                BUILD.build_once(source, Path(temporary) / "output")


if __name__ == "__main__":
    unittest.main()
