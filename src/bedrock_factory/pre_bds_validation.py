"""Deterministic package checks owned only by PRE_BDS_MILESTONE."""

from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


PRE_BDS_SCHEMA = "bedrock-factory.pre-bds-milestone.v1.0.0"


def inspect_mcaddon(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    findings: list[dict[str, str]] = []
    manifests: dict[str, dict[str, Any]] = {}
    names: set[str] = set()
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            name = info.filename
            parts = PurePosixPath(name).parts
            if name in names:
                findings.append({"code": "DUPLICATE_ARCHIVE_NAME", "path": name})
            names.add(name)
            if not parts or name.startswith("/") or ".." in parts:
                findings.append({"code": "UNSAFE_ARCHIVE_PATH", "path": name})
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode) or (mode and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode))):
                findings.append({"code": "FORBIDDEN_SPECIAL_FILE", "path": name})
            if name.endswith("manifest.json"):
                try:
                    manifest = json.loads(archive.read(info))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    findings.append({"code": "MALFORMED_MANIFEST", "path": name})
                    continue
                manifests[name] = manifest
        for manifest_name, manifest in manifests.items():
            root = str(PurePosixPath(manifest_name).parent)
            root = "" if root == "." else root + "/"
            if root + "pack_icon.png" not in names:
                findings.append({"code": "PACK_ICON_MISSING", "path": root + "pack_icon.png"})
            header = manifest.get("header") if isinstance(manifest, dict) else None
            modules = manifest.get("modules") if isinstance(manifest, dict) else None
            if not isinstance(header, dict) or not isinstance(header.get("uuid"), str):
                findings.append({"code": "MANIFEST_HEADER_INVALID", "path": manifest_name})
            if not isinstance(modules, list) or not modules:
                findings.append({"code": "MANIFEST_MODULES_MISSING", "path": manifest_name})
                continue
            for module in modules:
                if isinstance(module, dict) and module.get("type") == "script":
                    entry = module.get("entry")
                    if not isinstance(entry, str) or root + entry not in names:
                        findings.append({"code": "SCRIPT_ENTRYPOINT_MISSING", "path": str(entry)})
    return {
        "schema_version": PRE_BDS_SCHEMA,
        "milestone": "PRE_BDS_MILESTONE",
        "candidate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "manifest_count": len(manifests),
        "status": "PASS" if not findings else "FAIL",
        "findings": sorted(findings, key=lambda row: (row["code"], row["path"])),
    }
