from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.factory.analyze_legacy_curseforge_intake import (
    IntakeAnalysisError,
    analyze_intake,
    main,
)


def digest_tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class LegacyCurseForgeIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.server = self.root / "oracle" / "server"
        self.client = self.root / "oracle" / "client"
        self.server.mkdir(parents=True)
        self.client.mkdir(parents=True)
        self.lock = self.root / "authority" / "release-lock.json"
        self.lock.parent.mkdir()
        self.lock.write_text(
            json.dumps(
                {
                    "schema_version": "fixture-release-lock-v1",
                    "project_id": 296062,
                    "release": "4.2.4",
                    "rights_status": "ALL_RIGHTS_RESERVED",
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_mod_jar(
        self,
        filename: str = "ExampleMod-1.2.3.jar",
        *,
        duplicate_mcmod: bool = False,
        distribution: dict[str, bool] | None = None,
    ) -> Path:
        mods = self.server / "mods"
        mods.mkdir(exist_ok=True)
        target = mods / filename
        metadata = {
            "modid": "example",
            "name": "Example Mod",
            "version": "1.2.3",
            "dependencies": ["required-after:foundation@[1.0,);after:optional_api"],
            "license": "Fixture-License",
            **(distribution or {}),
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(target, "w") as archive:
                archive.writestr("mcmod.info", json.dumps([metadata]))
                if duplicate_mcmod:
                    archive.writestr("MCMOD.INFO", json.dumps([metadata]))
                archive.writestr(
                    "META-INF/MANIFEST.MF",
                    "Manifest-Version: 1.0\nImplementation-Version: 1.2.3\n",
                )
                archive.writestr("assets/example/textures/blocks/ore.png", b"not-an-image")
                archive.writestr("assets/example/Textures/Blocks/ORE.PNG", b"case-collision")
                archive.writestr("data/example/recipes/ore.json", b"{}")
                archive.writestr("embedded/dependency.jar", b"opaque nested archive")
        return target

    def _write_client_manifest(self) -> None:
        (self.client / "overrides" / "config").mkdir(parents=True)
        (self.client / "overrides" / "config" / "prestige.cfg").write_text(
            "enabled=true\n", encoding="utf-8"
        )
        (self.client / "manifest.json").write_text(
            json.dumps(
                {
                    "minecraft": {"version": "1.12.2"},
                    "manifestType": "minecraftModpack",
                    "name": "Fixture Pack",
                    "version": "4.2.4",
                    "files": [
                        {"projectID": 111, "fileID": 222, "required": True, "futureField": {"kept": "exactly"}},
                        {"projectID": 333, "fileID": 444, "required": False},
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def test_inventory_is_deterministic_read_only_and_preserves_manifest_rows(self) -> None:
        self._write_mod_jar()
        self._write_client_manifest()
        cache = self.root / "authority" / "official-file-metadata.json"
        cache.write_text(
            json.dumps(
                {
                    "files": [
                        {"projectId": 111, "id": 222, "fileName": "ExampleMod-1.2.3.jar"},
                        {"projectId": 333, "id": 444, "fileName": "ClientOnlyCandidate.jar"},
                    ]
                }
            )
            + "\n",
            encoding="utf-8",
        )
        before = {"server": digest_tree(self.server), "client": digest_tree(self.client)}
        output = self.root / "analysis"

        first = analyze_intake(self.lock, self.server, self.client, output, cache)
        json_outputs = {
            path.name: path.read_bytes() for path in output.glob("*.json")
        }
        second = analyze_intake(self.lock, self.server, self.client, output, cache)

        self.assertEqual(first, second)
        self.assertEqual(
            before,
            {"server": digest_tree(self.server), "client": digest_tree(self.client)},
        )
        self.assertEqual(
            json_outputs,
            {path.name: path.read_bytes() for path in output.glob("*.json")},
        )
        inventory = json.loads((output / "MOD_INVENTORY.json").read_text())
        self.assertEqual(
            inventory["client_manifest"]["rows"][0]["manifest_row"]["futureField"],
            {"kept": "exactly"},
        )
        self.assertEqual(inventory["mods"][0]["distribution"], "SHARED")
        self.assertFalse(first["source_content_executed"])
        self.assertFalse(first["nested_archives_opened"])

    def test_unique_metadata_dependencies_assets_and_archive_anomalies_are_evidence_grounded(self) -> None:
        self._write_mod_jar()
        self._write_client_manifest()
        output = self.root / "analysis"
        analyze_intake(self.lock, self.server, self.client, output)

        mods = json.loads((output / "MOD_INVENTORY.json").read_text())["mods"]
        self.assertEqual(mods[0]["mod_id"], "example")
        self.assertEqual(mods[0]["metadata_status"], "PARSED")
        self.assertEqual(mods[0]["distribution"], "SERVER_PRESENT_CLIENT_UNRESOLVED")
        self.assertEqual(mods[0]["nested_archive_members_not_opened"], ["embedded/dependency.jar"])
        graph = json.loads((output / "MOD_DEPENDENCY_GRAPH.json").read_text())
        self.assertEqual(
            {(edge["to"], edge["required"]) for edge in graph["edges"]},
            {("foundation", True), ("optional_api", False)},
        )
        file_inventory = json.loads((output / "FULL_FILE_INVENTORY.json").read_text())
        self.assertIn(
            "NESTED_PORTABLE_MEMBER_COLLISION",
            {row["kind"] for row in file_inventory["anomalies"]},
        )
        assets = json.loads((output / "ASSET_FAMILY_INVENTORY.json").read_text())
        block_family = next(row for row in assets["families"] if row["family"] == "BLOCK_TEXTURES")
        self.assertEqual(block_family["member_count"], 2)
        self.assertFalse(block_family["production_copying_allowed"])

    def test_multiple_case_variant_mcmod_entries_are_ambiguous_not_parsed(self) -> None:
        self._write_mod_jar(duplicate_mcmod=True)
        self._write_client_manifest()
        output = self.root / "analysis"
        summary = analyze_intake(self.lock, self.server, self.client, output)
        row = json.loads((output / "MOD_INVENTORY.json").read_text())["mods"][0]
        self.assertEqual(row["metadata_status"], "AMBIGUOUS_MULTIPLE_MCMOD_INFO")
        self.assertIsNone(row["mod_id"])
        self.assertEqual(row["distribution"], "UNKNOWN")
        self.assertEqual(summary["analysis_status"], "COMPLETE_WITH_UNKNOWNS")

    def test_explicit_distribution_is_honored_but_missing_metadata_stays_unknown(self) -> None:
        self._write_mod_jar(distribution={"clientSideOnly": True})
        broken = self.server / "mods" / "broken.jar"
        broken.write_bytes(b"not a zip")
        self._write_client_manifest()
        output = self.root / "analysis"
        analyze_intake(self.lock, self.server, self.client, output)
        rows = json.loads((output / "MOD_INVENTORY.json").read_text())["mods"]
        by_name = {row["filename"]: row for row in rows}
        self.assertEqual(by_name["ExampleMod-1.2.3.jar"]["distribution"], "CLIENT_ONLY")
        self.assertEqual(by_name["broken.jar"]["archive_status"], "INVALID_OR_UNREADABLE_ZIP")
        self.assertEqual(by_name["broken.jar"]["distribution"], "UNKNOWN")

    def test_sqlite_mirrors_core_inventory(self) -> None:
        self._write_mod_jar()
        self._write_client_manifest()
        output = self.root / "analysis"
        analyze_intake(self.lock, self.server, self.client, output)
        connection = sqlite3.connect(output / "FULL_FILE_INVENTORY.sqlite3")
        try:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM files").fetchone()[0],
                json.loads((output / "FULL_FILE_INVENTORY.json").read_text())["file_count"],
            )
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM client_manifest_rows").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT mod_id FROM mods").fetchone()[0], "example")
        finally:
            connection.close()

    def test_output_inside_oracle_is_rejected_and_cli_fails_closed(self) -> None:
        self._write_mod_jar()
        self._write_client_manifest()
        with self.assertRaises(IntakeAnalysisError):
            analyze_intake(self.lock, self.server, self.client, self.server / "analysis")
        self.assertEqual(
            main(
                [
                    "--release-lock", str(self.lock),
                    "--server-oracle-root", str(self.server),
                    "--client-oracle-root", str(self.client),
                    "--analysis-root", str(self.server / "analysis"),
                ]
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
