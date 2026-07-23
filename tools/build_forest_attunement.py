#!/usr/bin/env python3
"""Build the original Forest Attunement internal-test add-on deterministically."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/forest-attunement"
RP_TEXTURE = FEATURE / "resource_pack/textures/items/forest_attunement_sigil.png"
SOURCE_TEXTURE = ROOT / "prototypes/blockbench/forest_attunement/forest_attunement_sigil.png"
DIST = FEATURE / "dist"
REPORTS = FEATURE / "reports"
ZIP_TIME = (2020, 1, 1, 0, 0, 0)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def make_icon() -> bytes:
    """Return an original 32px leaf-ring sigil using a fixed indexed palette."""
    size = 32
    transparent = (0, 0, 0, 0)
    bark = (62, 43, 30, 255)
    gold = (218, 181, 82, 255)
    moss = (58, 121, 73, 255)
    light = (116, 181, 91, 255)
    pixels = [[transparent for _ in range(size)] for _ in range(size)]
    for y in range(size):
        for x in range(size):
            dx, dy = x - 15.5, y - 15.5
            d2 = dx * dx + dy * dy
            if 92 <= d2 <= 151:
                pixels[y][x] = bark
            if 103 <= d2 <= 132 and (x + 2 * y) % 5:
                pixels[y][x] = gold
    # A deliberately asymmetric sprout/needle glyph.
    for y in range(7, 25):
        x = 15 + (y - 15) // 7
        for ox in (-1, 0, 1):
            pixels[y][x + ox] = light if ox == 0 else moss
    for x, y in [(10, 11), (11, 12), (12, 13), (20, 10), (19, 11), (18, 12),
                 (9, 18), (10, 17), (11, 16), (21, 18), (20, 17), (19, 16)]:
        for ox in (0, 1):
            for oy in (0, 1):
                pixels[y + oy][x + ox] = moss if (ox + oy) else light
    raw = b"".join(b"\x00" + b"".join(bytes(px) for px in row) for row in pixels)
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return signature + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b"")


def write_if_changed(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def zip_tree(output: Path, roots: list[tuple[Path, str]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        entries = []
        for root, prefix in roots:
            entries.extend((path, f"{prefix}/{path.relative_to(root).as_posix()}" if prefix else path.relative_to(root).as_posix())
                           for path in root.rglob("*") if path.is_file())
        for path, name in sorted(entries, key=lambda pair: pair[1]):
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    icon = make_icon()
    write_if_changed(RP_TEXTURE, icon)
    write_if_changed(SOURCE_TEXTURE, icon)
    DIST.mkdir(parents=True, exist_ok=True)
    bp = DIST / "forest-attunement-behavior-INTERNAL-TEST.mcpack"
    rp = DIST / "forest-attunement-resource-INTERNAL-TEST.mcpack"
    addon = DIST / "forest-attunement-INTERNAL-TEST.mcaddon"
    zip_tree(bp, [(FEATURE / "behavior_pack", "")])
    zip_tree(rp, [(FEATURE / "resource_pack", "")])
    zip_tree(addon, [(FEATURE / "behavior_pack", "ForestAttunement_BP"),
                     (FEATURE / "resource_pack", "ForestAttunement_RP")])
    artifacts = {
        "schema_version": "1.0.0",
        "label": "INTERNAL-TEST",
        "artifacts": [
            {"path": str(path.relative_to(FEATURE)), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in (bp, rp, addon)
        ],
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "artifact-manifest.json").write_text(json.dumps(artifacts, indent=2) + "\n")
    print(json.dumps(artifacts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
