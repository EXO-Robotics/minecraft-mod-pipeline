#!/usr/bin/env python3
"""Build only: package committed BP/RP bytes without generating source content."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pack_tree(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for member in sorted(path for path in source.rglob("*") if path.is_file()):
            relative = member.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, member.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def pack_addon(packs: list[Path], target: Path) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
        for member in packs:
            info = zipfile.ZipInfo(member.name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, member.read_bytes())


def main() -> None:
    behavior = DIST / "aionbound-core-content-beta-g7-behavior.mcpack"
    resources = DIST / "aionbound-core-content-beta-g7-resources.mcpack"
    addon = DIST / "aionbound-core-content-beta-g7.mcaddon"
    pack_tree(ROOT / "behavior_pack", behavior)
    pack_tree(ROOT / "resource_pack", resources)
    pack_addon([behavior, resources], addon)
    result = {
        "artifacts": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path), "size": path.stat().st_size}
            for path in (behavior, resources, addon)
        ],
        "build_mode": "sorted members, fixed timestamps, fixed permissions, deflate level 9",
        "generation": 7,
        "source_generation_performed": False,
        "state": "DETERMINISTIC_BUILD_COMPLETE",
    }
    (DIST / "g7-artifact-manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
