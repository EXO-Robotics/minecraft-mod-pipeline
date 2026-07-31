#!/usr/bin/env python3
"""Fail-closed extraction for one already frozen outer evidence ZIP.

Nested JAR/ZIP files remain opaque bytes. This is intentionally separate from
the factory planner, whose recursive metadata inspection may reject defects
inside a nested archive even when the containing outer ZIP is safe to extract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath


MAX_ENTRIES = 250_000
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024
ALLOWED_COMPRESSION_METHODS = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}


class OuterArchiveError(ValueError):
    pass


def _assert_no_symlink_components(path: Path, *, allow_missing_tail: bool) -> None:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    missing = False
    for part in absolute.parts[1:]:
        current /= part
        if missing:
            continue
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if allow_missing_tail:
                missing = True
                continue
            raise OuterArchiveError(f"path does not exist: {absolute}") from None
        if stat.S_ISLNK(mode):
            raise OuterArchiveError(f"symlink path component rejected: {current}")


def _safe_name(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name or name.startswith("/"):
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and all(
        part not in {"", ".", ".."} for part in path.parts
    )


def _portable(name: str) -> str:
    return unicodedata.normalize("NFC", name.rstrip("/")).casefold()


def _validate(archive: zipfile.ZipFile, locator: str) -> list[zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > MAX_ENTRIES:
        raise OuterArchiveError(f"archive entry limit exceeded: {locator}")
    seen: set[str] = set()
    portable_seen: set[str] = set()
    file_paths: set[PurePosixPath] = set()
    all_paths: set[PurePosixPath] = set()
    total = 0
    for info in infos:
        name = info.filename
        if not _safe_name(name):
            raise OuterArchiveError(f"unsafe outer archive member: {name!r}")
        mode = info.external_attr >> 16
        if mode and stat.S_ISLNK(mode):
            raise OuterArchiveError(f"outer archive symlink rejected: {name}")
        if info.flag_bits & 0x1:
            raise OuterArchiveError(f"encrypted outer archive member rejected: {name}")
        if info.compress_type not in ALLOWED_COMPRESSION_METHODS:
            raise OuterArchiveError(
                f"unsupported outer archive compression method: {name}"
            )
        if name in seen:
            raise OuterArchiveError(f"duplicate outer archive member: {name}")
        seen.add(name)
        portable = _portable(name)
        if portable in portable_seen:
            raise OuterArchiveError(f"portable outer archive collision: {name}")
        portable_seen.add(portable)
        path = PurePosixPath(name.rstrip("/"))
        all_paths.add(path)
        if any(parent in file_paths for parent in path.parents):
            raise OuterArchiveError(f"file/directory prefix collision: {name}")
        if not info.is_dir():
            file_paths.add(path)
            if info.file_size > MAX_FILE_BYTES:
                raise OuterArchiveError(f"outer archive member too large: {name}")
            total += info.file_size
            if total > MAX_TOTAL_BYTES:
                raise OuterArchiveError("outer archive expansion limit exceeded")
    for file_path in file_paths:
        if any(
            other != file_path and file_path in other.parents
            for other in all_paths
        ):
            raise OuterArchiveError(
                f"file/directory prefix collision: {file_path.as_posix()}"
            )
    return infos


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(
    source: Path,
    output: Path,
    manifest: Path,
    *,
    expected_sha256: str,
    expected_bytes: int,
) -> dict[str, object]:
    source_input = source.expanduser()
    output_input = output.expanduser()
    _assert_no_symlink_components(source_input, allow_missing_tail=False)
    _assert_no_symlink_components(output_input, allow_missing_tail=True)
    source = source_input.resolve()
    output = output_input.resolve()
    manifest = manifest.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".zip":
        raise OuterArchiveError("source must be one regular ZIP file")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise OuterArchiveError("output must be absent or an empty directory")
    if source.stat().st_size != expected_bytes:
        raise OuterArchiveError("frozen source byte length mismatch")
    observed_sha256 = _sha256(source)
    if observed_sha256 != expected_sha256:
        raise OuterArchiveError("frozen source SHA-256 mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    rows: list[dict[str, object]] = []
    try:
        with zipfile.ZipFile(source, "r") as archive:
            infos = _validate(archive, str(source))
            for info in infos:
                relative = PurePosixPath(info.filename.rstrip("/"))
                target = temporary.joinpath(*relative.parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                with archive.open(info, "r") as input_stream, target.open("xb") as output_stream:
                    while True:
                        chunk = input_stream.read(1024 * 1024)
                        if not chunk:
                            break
                        output_stream.write(chunk)
                        digest.update(chunk)
                rows.append(
                    {
                        "path": relative.as_posix(),
                        "byte_length": info.file_size,
                        "compressed_byte_length": info.compress_size,
                        "crc32": f"{info.CRC:08x}",
                        "sha256": digest.hexdigest(),
                    }
                )
        for path in sorted(temporary.rglob("*"), reverse=True):
            path.chmod(0o555 if path.is_dir() else 0o444)
        temporary.chmod(0o555)
        if output.exists():
            output.rmdir()
        os.replace(temporary, output)
        document: dict[str, object] = {
            "schema_version": "safe-outer-archive-extraction-v1",
            "source_path": str(source),
            "source_sha256": observed_sha256,
            "source_byte_length": expected_bytes,
            "output_path": str(output),
            "nested_archives_opened": False,
            "archive_entry_count": len(infos),
            "file_count": len(rows),
            "total_uncompressed_bytes": sum(
                int(row["byte_length"]) for row in rows
            ),
            "checks": {
                "zip_integrity": "PASS",
                "unsafe_paths": 0,
                "symlinks": 0,
                "duplicate_names": 0,
                "portable_name_collisions": 0,
                "file_directory_prefix_collisions": 0,
                "encrypted_members": 0,
                "unsupported_compression_methods": 0,
            },
            "files": rows,
        }
        temporary_manifest = manifest.with_name(f".{manifest.name}.tmp")
        temporary_manifest.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary_manifest, manifest)
        return document
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-bytes", type=int, required=True)
    args = parser.parse_args()
    try:
        result = safe_extract(
            args.source,
            args.output,
            args.manifest,
            expected_sha256=args.expected_sha256,
            expected_bytes=args.expected_bytes,
        )
    except (OSError, OuterArchiveError, zipfile.BadZipFile) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "ok": True,
                "source_sha256": result["source_sha256"],
                "archive_entry_count": result["archive_entry_count"],
                "file_count": result["file_count"],
                "total_uncompressed_bytes": result["total_uncompressed_bytes"],
                "manifest": str(args.manifest.expanduser().resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
