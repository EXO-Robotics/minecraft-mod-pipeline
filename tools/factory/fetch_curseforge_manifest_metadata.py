#!/usr/bin/env python3
"""Build a deterministic metadata cache for a CurseForge client manifest.

This tool deliberately fetches metadata only.  It never follows redirects and
never reads a download URL returned by the API response.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


OFFICIAL_BASE_URL = "https://www.curseforge.com/api/v1"
CACHE_SCHEMA_VERSION = "curseforge.manifest-metadata-cache.v1"
RECEIPT_SCHEMA_VERSION = "curseforge.manifest-metadata-fetch-receipt.v1"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_WORKERS_LIMIT = 32
MAX_RETRIES_LIMIT = 5


class ManifestValidationError(ValueError):
    """The input client manifest is not a safe, complete fetch authority."""


class MetadataFetchError(RuntimeError):
    """One or more official metadata requests could not be completed."""


class MetadataValidationError(ValueError):
    """An API response did not describe the requested project and file."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(  # type: ignore[override]
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ManifestValidationError(f"{field} must be a positive integer")
    return value


def load_manifest_entries(manifest_path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and strictly validate required project/file identities."""

    path = Path(manifest_path)
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(f"cannot read client manifest {path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ManifestValidationError("client manifest root must be an object")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ManifestValidationError("client manifest files must be a non-empty array")

    project_ids: set[int] = set()
    file_ids: set[int] = set()
    entries: list[dict[str, Any]] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise ManifestValidationError(f"files[{index}] must be an object")
        project_id = _positive_int(item.get("projectID"), f"files[{index}].projectID")
        file_id = _positive_int(item.get("fileID"), f"files[{index}].fileID")
        if item.get("required") is not True:
            raise ManifestValidationError(f"files[{index}].required must be true")
        if project_id in project_ids:
            raise ManifestValidationError(f"duplicate projectID: {project_id}")
        if file_id in file_ids:
            raise ManifestValidationError(f"duplicate fileID: {file_id}")
        project_ids.add(project_id)
        file_ids.add(file_id)
        entries.append(
            {"project_id": project_id, "file_id": file_id, "required": True}
        )

    entries.sort(key=lambda entry: (entry["project_id"], entry["file_id"]))
    source = {
        "manifest_sha256": _sha256_bytes(raw),
        "manifest_type": manifest.get("manifestType"),
        "manifest_version": manifest.get("manifestVersion"),
        "pack_name": manifest.get("name"),
        "pack_version": manifest.get("version"),
        "minecraft_version": (
            manifest.get("minecraft", {}).get("version")
            if isinstance(manifest.get("minecraft"), dict)
            else None
        ),
    }
    return source, entries


def _normalize_base_url(base_url: str) -> str:
    if not isinstance(base_url, str) or not base_url:
        raise ValueError("base_url must be a non-empty URL")
    normalized = base_url.rstrip("/")
    parsed = urllib.parse.urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be an absolute HTTP(S) URL")
    if parsed.query or parsed.fragment:
        raise ValueError("base_url must not include a query or fragment")
    return normalized


def _as_int_or_none(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise MetadataValidationError(f"{field} must be null or a positive integer")
    return value


def _as_bool_or_none(value: Any, field: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise MetadataValidationError(f"{field} must be null or boolean")
    return value


def _minimal_metadata(
    payload: Any, *, project_id: int, file_id: int
) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise MetadataValidationError("response must contain a data object")
    data = payload["data"]
    returned_project = data.get("projectId", data.get("modId"))
    if (
        data.get("projectId") is not None
        and data.get("modId") is not None
        and data.get("projectId") != data.get("modId")
    ):
        raise MetadataValidationError("conflicting projectId and modId identities")
    returned_file = data.get("id")
    if returned_project != project_id or isinstance(returned_project, bool):
        raise MetadataValidationError(
            f"project identity mismatch: requested {project_id}, returned {returned_project!r}"
        )
    if returned_file != file_id or isinstance(returned_file, bool):
        raise MetadataValidationError(
            f"file identity mismatch: requested {file_id}, returned {returned_file!r}"
        )

    filename = data.get("fileName")
    display_name = data.get("displayName")
    byte_length = data.get("fileLength")
    release_type = data.get("releaseType")
    game_versions = data.get("gameVersions")
    if not isinstance(filename, str) or not filename.strip():
        raise MetadataValidationError("fileName must be a non-empty string")
    if not isinstance(display_name, str) or not display_name.strip():
        raise MetadataValidationError("displayName must be a non-empty string")
    if isinstance(byte_length, bool) or not isinstance(byte_length, int) or byte_length < 0:
        raise MetadataValidationError("fileLength must be a non-negative integer")
    if isinstance(release_type, bool) or not isinstance(release_type, (int, str)):
        raise MetadataValidationError("releaseType must be an integer or string")
    if not isinstance(game_versions, list) or not all(
        isinstance(version, str) and version for version in game_versions
    ):
        raise MetadataValidationError("gameVersions must be an array of non-empty strings")

    compatibility = {
        "is_available": _as_bool_or_none(data.get("isAvailable"), "isAvailable"),
        "is_server_pack": _as_bool_or_none(data.get("isServerPack"), "isServerPack"),
        "server_pack_file_id": _as_int_or_none(
            data.get("serverPackFileId"), "serverPackFileId"
        ),
        "parent_project_file_id": _as_int_or_none(
            data.get("parentProjectFileId"), "parentProjectFileId"
        ),
        "alternate_file_id": _as_int_or_none(data.get("alternateFileId"), "alternateFileId"),
        "expose_as_alternative": _as_bool_or_none(
            data.get("exposeAsAlternative"), "exposeAsAlternative"
        ),
        "is_early_access_content": _as_bool_or_none(
            data.get("isEarlyAccessContent"), "isEarlyAccessContent"
        ),
        "is_compatible_with_client": _as_bool_or_none(
            data.get("isCompatibleWithClient"), "isCompatibleWithClient"
        ),
    }
    return {
        "project_id": project_id,
        "file_id": file_id,
        "filename": filename,
        "display_name": display_name,
        "byte_length": byte_length,
        "release_type": release_type,
        "game_versions": sorted(set(game_versions)),
        "compatibility": compatibility,
    }


def _response_bytes(response: Any, expected_url: str) -> bytes:
    final_url = response.geturl() if hasattr(response, "geturl") else expected_url
    if final_url != expected_url:
        raise MetadataFetchError(
            f"redirected metadata request is forbidden: {expected_url} -> {final_url}"
        )
    status = getattr(response, "status", None)
    if status is None and hasattr(response, "getcode"):
        status = response.getcode()
    if status not in (None, 200):
        raise MetadataFetchError(f"metadata endpoint returned HTTP {status}")
    headers = getattr(response, "headers", None)
    if headers is not None:
        raw_length = headers.get("Content-Length")
        if raw_length is not None:
            try:
                if int(raw_length) > MAX_RESPONSE_BYTES:
                    raise MetadataFetchError("metadata response exceeds size limit")
            except ValueError as exc:
                raise MetadataFetchError("invalid metadata Content-Length") from exc
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise MetadataFetchError("metadata response exceeds size limit")
    return body


def _fetch_one(
    entry: Mapping[str, Any],
    *,
    base_url: str,
    opener: Callable[..., Any],
    retries: int,
    timeout: float,
    sleep: Callable[[float], None],
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_id = int(entry["project_id"])
    file_id = int(entry["file_id"])
    url = f"{base_url}/mods/{project_id}/files/{file_id}"
    last_error: Exception | None = None
    for attempt in range(1, retries + 2):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "mccompiler-curseforge-metadata/1",
            },
        )
        try:
            response = opener(request, timeout=timeout)
            try:
                body = _response_bytes(response, url)
            finally:
                if hasattr(response, "close"):
                    response.close()
            try:
                payload = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MetadataValidationError("metadata response is not valid JSON") from exc
            metadata = _minimal_metadata(
                payload, project_id=project_id, file_id=file_id
            )
            fetch = {
                "project_id": project_id,
                "file_id": file_id,
                "url": url,
                "attempts": attempt,
                "response_sha256": _sha256_bytes(body),
            }
            return metadata, fetch
        except (OSError, urllib.error.URLError, MetadataFetchError, MetadataValidationError) as exc:
            last_error = exc
            if attempt <= retries:
                sleep(min(0.25 * (2 ** (attempt - 1)), 2.0))
    assert last_error is not None
    raise MetadataFetchError(
        f"metadata fetch failed for projectID={project_id} fileID={file_id} "
        f"after {retries + 1} attempt(s): {last_error}"
    ) from last_error


def _atomic_json(path: Path, value: Mapping[str, Any]) -> bytes:
    payload = _canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return payload


def build_metadata_cache(
    manifest_path: str | Path,
    cache_path: str | Path,
    receipt_path: str | Path,
    *,
    opener: Callable[..., Any] | None = None,
    base_url: str = OFFICIAL_BASE_URL,
    max_workers: int = 8,
    retries: int = 2,
    timeout: float = 15.0,
    now: Callable[[], str] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch exact manifest metadata and atomically publish cache and receipt."""

    if isinstance(max_workers, bool) or not 1 <= max_workers <= MAX_WORKERS_LIMIT:
        raise ValueError(f"max_workers must be between 1 and {MAX_WORKERS_LIMIT}")
    if isinstance(retries, bool) or not 0 <= retries <= MAX_RETRIES_LIMIT:
        raise ValueError(f"retries must be between 0 and {MAX_RETRIES_LIMIT}")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    normalized_base = _normalize_base_url(base_url)
    source, entries = load_manifest_entries(manifest_path)
    if opener is None:
        opener = urllib.request.build_opener(_NoRedirectHandler()).open

    metadata_by_identity: dict[tuple[int, int], dict[str, Any]] = {}
    fetch_by_identity: dict[tuple[int, int], dict[str, Any]] = {}
    failures: list[str] = []
    worker_count = min(max_workers, len(entries))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(
                _fetch_one,
                entry,
                base_url=normalized_base,
                opener=opener,
                retries=retries,
                timeout=timeout,
                sleep=sleep,
            ): (entry["project_id"], entry["file_id"])
            for entry in entries
        }
        for future in as_completed(futures):
            identity = futures[future]
            try:
                metadata, fetch = future.result()
            except Exception as exc:
                failures.append(f"{identity[0]}/{identity[1]}: {exc}")
            else:
                metadata_by_identity[identity] = metadata
                fetch_by_identity[identity] = fetch
    if failures:
        raise MetadataFetchError("; ".join(sorted(failures)))

    ordered_identities = sorted(metadata_by_identity)
    authority_payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "source": source,
        "endpoint_template": f"{normalized_base}/mods/{{projectID}}/files/{{fileID}}",
        "files": [metadata_by_identity[identity] for identity in ordered_identities],
    }
    authority_sha256 = _sha256_bytes(_canonical_bytes(authority_payload))
    cache = {
        **authority_payload,
        "authority_payload_sha256": authority_sha256,
    }

    cache_bytes = _canonical_bytes(cache)
    completed_at = (
        now()
        if now is not None
        else time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "fetch_completed_at": completed_at,
        "source_manifest_path": str(Path(manifest_path).resolve()),
        "source_manifest_sha256": source["manifest_sha256"],
        "cache_path": str(Path(cache_path).resolve()),
        "cache_sha256": _sha256_bytes(cache_bytes),
        "authority_payload_sha256": authority_sha256,
        "official_base_url_used": normalized_base == OFFICIAL_BASE_URL,
        "fetches": [fetch_by_identity[identity] for identity in ordered_identities],
    }

    _atomic_json(Path(cache_path), cache)
    _atomic_json(Path(receipt_path), receipt)
    return cache, receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="extracted client manifest.json")
    parser.add_argument("cache", type=Path, help="deterministic metadata cache output")
    parser.add_argument("receipt", type=Path, help="metadata fetch receipt output")
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        build_metadata_cache(
            args.manifest,
            args.cache,
            args.receipt,
            max_workers=args.max_workers,
            retries=args.retries,
            timeout=args.timeout,
        )
    except (ManifestValidationError, MetadataFetchError, MetadataValidationError, ValueError) as exc:
        raise SystemExit(f"metadata cache build failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
