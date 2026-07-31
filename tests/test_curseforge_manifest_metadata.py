from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.factory.fetch_curseforge_manifest_metadata import (
    OFFICIAL_BASE_URL,
    ManifestValidationError,
    MetadataFetchError,
    build_metadata_cache,
)


class FakeResponse(io.BytesIO):
    status = 200
    headers: dict[str, str] = {}

    def __init__(self, payload: dict[str, Any], url: str) -> None:
        super().__init__(json.dumps(payload).encode("utf-8"))
        self._url = url

    def geturl(self) -> str:
        return self._url


def response(project_id: int, file_id: int, **overrides: Any) -> dict[str, Any]:
    data = {
        "projectId": project_id,
        "id": file_id,
        "fileName": f"mod-{project_id}.jar",
        "displayName": f"Mod {project_id}",
        "fileLength": project_id * 100,
        "releaseType": 1,
        "gameVersions": ["Forge", "1.12.2", "1.12.2"],
        "isAvailable": True,
        "isServerPack": False,
        "serverPackFileId": None,
        "parentProjectFileId": None,
        "alternateFileId": None,
        "exposeAsAlternative": False,
        "isEarlyAccessContent": False,
        "isCompatibleWithClient": True,
        "downloadUrl": "https://artifacts.invalid/must-not-be-opened.jar",
        "extraOfficialData": "not retained",
    }
    data.update(overrides)
    return {"data": data}


class CurseForgeManifestMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.manifest = self.root / "manifest.json"
        self.cache = self.root / "cache.json"
        self.receipt = self.root / "receipt.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_manifest(self, files: list[dict[str, Any]]) -> None:
        self.manifest.write_text(
            json.dumps(
                {
                    "manifestType": "minecraftModpack",
                    "manifestVersion": 1,
                    "name": "Fixture Pack",
                    "version": "1.0",
                    "minecraft": {"version": "1.12.2"},
                    "files": files,
                }
            ),
            encoding="utf-8",
        )

    def opener_for(self, payloads: dict[tuple[int, int], dict[str, Any]]):
        opened: list[str] = []

        def open_request(request: Any, *, timeout: float) -> FakeResponse:
            del timeout
            url = request.full_url
            opened.append(url)
            parts = url.rstrip("/").split("/")
            identity = (int(parts[-3]), int(parts[-1]))
            return FakeResponse(payloads[identity], url)

        return open_request, opened

    def test_builds_deterministic_minimal_cache_without_downloading_artifacts(self) -> None:
        self.write_manifest(
            [
                {"projectID": 20, "fileID": 200, "required": True},
                {"projectID": 10, "fileID": 100, "required": True},
            ]
        )
        payloads = {(10, 100): response(10, 100), (20, 200): response(20, 200)}
        opener, opened = self.opener_for(payloads)
        cache_one, receipt_one = build_metadata_cache(
            self.manifest,
            self.cache,
            self.receipt,
            opener=opener,
            base_url="http://offline.test/api/v1",
            now=lambda: "2026-01-01T00:00:00Z",
            sleep=lambda _: None,
        )
        first_cache_bytes = self.cache.read_bytes()
        first_authority_hash = cache_one["authority_payload_sha256"]

        opener_two, opened_two = self.opener_for(payloads)
        cache_two, receipt_two = build_metadata_cache(
            self.manifest,
            self.cache,
            self.receipt,
            opener=opener_two,
            base_url="http://offline.test/api/v1",
            now=lambda: "2027-02-02T00:00:00Z",
            sleep=lambda _: None,
        )

        self.assertEqual(first_cache_bytes, self.cache.read_bytes())
        self.assertEqual(first_authority_hash, cache_two["authority_payload_sha256"])
        self.assertNotIn("fetch_completed_at", cache_two)
        self.assertNotEqual(receipt_one["fetch_completed_at"], receipt_two["fetch_completed_at"])
        self.assertEqual([row["project_id"] for row in cache_two["files"]], [10, 20])
        self.assertEqual(cache_two["files"][0]["game_versions"], ["1.12.2", "Forge"])
        self.assertNotIn("downloadUrl", json.dumps(cache_two))
        self.assertNotIn("artifacts.invalid", opened + opened_two)
        self.assertTrue(all("/mods/" in url and "/files/" in url for url in opened))

    def test_rejects_duplicate_or_non_required_manifest_identities_before_fetch(self) -> None:
        invalid_sets = [
            [
                {"projectID": 10, "fileID": 100, "required": True},
                {"projectID": 10, "fileID": 101, "required": True},
            ],
            [
                {"projectID": 10, "fileID": 100, "required": True},
                {"projectID": 11, "fileID": 100, "required": True},
            ],
            [{"projectID": 0, "fileID": 100, "required": True}],
            [{"projectID": 10, "fileID": 100, "required": False}],
            [{"projectID": 10, "fileID": 100}],
        ]
        for index, files in enumerate(invalid_sets):
            with self.subTest(index=index):
                self.write_manifest(files)
                with self.assertRaises(ManifestValidationError):
                    build_metadata_cache(
                        self.manifest,
                        self.cache,
                        self.receipt,
                        opener=lambda *_args, **_kwargs: self.fail("fetch must not occur"),
                        base_url="http://offline.test/api/v1",
                    )

    def test_rejects_returned_project_or_file_identity_mismatch(self) -> None:
        self.write_manifest([{"projectID": 10, "fileID": 100, "required": True}])
        for bad_payload in (response(11, 100), response(10, 101)):
            with self.subTest(payload=bad_payload):
                opener, _ = self.opener_for({(10, 100): bad_payload})
                with self.assertRaises(MetadataFetchError) as raised:
                    build_metadata_cache(
                        self.manifest,
                        self.cache,
                        self.receipt,
                        opener=opener,
                        base_url="http://offline.test/api/v1",
                        retries=0,
                    )
                self.assertIn("identity mismatch", str(raised.exception))
                self.assertFalse(self.cache.exists())
                self.assertFalse(self.receipt.exists())

    def test_failed_fetch_is_retried_boundedly_and_publishes_nothing(self) -> None:
        self.write_manifest([{"projectID": 10, "fileID": 100, "required": True}])
        calls = 0

        def failing_opener(_request: Any, *, timeout: float) -> Any:
            nonlocal calls
            del timeout
            calls += 1
            raise urllib.error.URLError("offline")

        with self.assertRaises(MetadataFetchError):
            build_metadata_cache(
                self.manifest,
                self.cache,
                self.receipt,
                opener=failing_opener,
                base_url="http://offline.test/api/v1",
                retries=2,
                sleep=lambda _: None,
            )
        self.assertEqual(calls, 3)
        self.assertFalse(self.cache.exists())
        self.assertFalse(self.receipt.exists())

    def test_default_endpoint_is_official_and_custom_base_is_explicit(self) -> None:
        self.assertEqual(OFFICIAL_BASE_URL, "https://www.curseforge.com/api/v1")
        self.write_manifest([{"projectID": 10, "fileID": 100, "required": True}])
        seen: list[str] = []

        def opener(request: Any, *, timeout: float) -> FakeResponse:
            del timeout
            seen.append(request.full_url)
            return FakeResponse(response(10, 100), request.full_url)

        _cache, receipt = build_metadata_cache(
            self.manifest,
            self.cache,
            self.receipt,
            opener=opener,
            retries=0,
        )
        self.assertEqual(
            seen,
            ["https://www.curseforge.com/api/v1/mods/10/files/100"],
        )
        self.assertTrue(receipt["official_base_url_used"])


if __name__ == "__main__":
    unittest.main()
