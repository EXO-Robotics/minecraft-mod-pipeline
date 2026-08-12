#!/usr/bin/env python3
"""Verify a deterministic G8 engineering preview without qualifying it."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import struct
import subprocess
import zlib
import zipfile


EXPECTED_STATE = "DETERMINISTIC_WORKSPACE_BUILD_COMPLETE_NOT_FROZEN_NOT_QUALIFIED"
PROOF_BOUNDARIES = [
    "not_an_immutable_candidate",
    "not_bds_or_same_world_restart_proof",
    "not_client_controller_console_realms_marketplace_or_release_proof",
    "dormant_or_unratified_gameplay_is_not_claimed_complete",
]


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_member(name: str) -> PurePosixPath:
    member = PurePosixPath(name)
    if member.is_absolute() or not member.parts or ".." in member.parts:
        raise ValueError(f"unsafe archive member: {name!r}")
    return member


def validate_png(value: bytes) -> None:
    if value[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("invalid PNG signature")
    position = 8
    ihdr = iend = False
    while position < len(value):
        if position + 12 > len(value):
            raise ValueError("truncated PNG chunk")
        size = struct.unpack(">I", value[position : position + 4])[0]
        kind = value[position + 4 : position + 8]
        end = position + 12 + size
        if end > len(value):
            raise ValueError("truncated PNG payload")
        payload = value[position + 8 : position + 8 + size]
        recorded = struct.unpack(">I", value[position + 8 + size : end])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != recorded:
            raise ValueError("invalid PNG CRC")
        ihdr |= kind == b"IHDR"
        iend |= kind == b"IEND"
        position = end
    if position != len(value) or not ihdr or not iend:
        raise ValueError("incomplete PNG")


def git_value(root: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()


def verify(root: Path, addon: Path, manifest_path: Path, expected_commit: str) -> dict:
    root = root.resolve()
    addon = addon.resolve()
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("state") != EXPECTED_STATE:
        raise ValueError(f"unexpected build state: {manifest.get('state')!r}")

    commit = git_value(root, "rev-parse", expected_commit)
    tree = git_value(root, "rev-parse", f"{commit}^{{tree}}")
    addon_bytes = addon.read_bytes()
    addon_rows = [row for row in manifest["artifacts"] if row["path"] == addon.name]
    if len(addon_rows) != 1:
        raise ValueError("manifest must bind the addon exactly once")
    addon_row = addon_rows[0]
    if addon_row["sha256"] != sha256(addon_bytes) or addon_row["size"] != len(addon_bytes):
        raise ValueError("addon differs from artifact manifest")

    inner_files = json_count = png_count = 0
    nested_hashes: dict[str, str] = {}
    entrypoint = manifest["packaged_entrypoint"]
    shipped_entrypoint_hash = None
    with zipfile.ZipFile(io.BytesIO(addon_bytes)) as outer:
        if outer.testzip() is not None:
            raise ValueError("outer archive CRC failure")
        for outer_info in outer.infolist():
            safe_member(outer_info.filename)
            if outer_info.is_dir():
                continue
            payload = outer.read(outer_info)
            nested_hashes[outer_info.filename] = sha256(payload)
            with zipfile.ZipFile(io.BytesIO(payload)) as inner:
                if inner.testzip() is not None:
                    raise ValueError(f"nested archive CRC failure: {outer_info.filename}")
                for inner_info in inner.infolist():
                    safe_member(inner_info.filename)
                    if inner_info.is_dir():
                        continue
                    value = inner.read(inner_info)
                    inner_files += 1
                    if inner_info.filename.endswith(".json"):
                        json.loads(value)
                        json_count += 1
                    if inner_info.filename.endswith(".png"):
                        validate_png(value)
                        png_count += 1
                    if (
                        outer_info.filename == entrypoint["behavior_mcpack_member"]
                        and inner_info.filename == entrypoint["entrypoint_member"]
                    ):
                        shipped_entrypoint_hash = sha256(value)

    for row in manifest["artifacts"]:
        if row["path"].endswith(".mcpack") and nested_hashes.get(row["path"]) != row["sha256"]:
            raise ValueError(f"nested pack differs from manifest: {row['path']}")
    if shipped_entrypoint_hash != entrypoint["sha256"]:
        raise ValueError("shipped entrypoint differs from manifest")

    return {
        "schema_version": 1,
        "status": "ENGINEERING_PREVIEW_EXACT_ARCHIVE_PASS_NOT_CANDIDATE_NOT_QUALIFIED",
        "source": {"commit": commit, "tree": tree},
        "addon": {"path": str(addon), "sha256": addon_row["sha256"], "size": addon_row["size"]},
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path.read_bytes())},
        "packaged_entrypoint": entrypoint,
        "archive_checks": {
            "outer_and_nested_crc": "PASS",
            "inner_file_count": inner_files,
            "json_parse_count": json_count,
            "png_signature_and_crc_count": png_count,
        },
        "proof_boundaries": PROOF_BOUNDARIES,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--addon", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.root, args.addon, args.manifest, args.commit)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
