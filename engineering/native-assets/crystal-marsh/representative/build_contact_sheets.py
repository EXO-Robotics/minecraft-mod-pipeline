#!/usr/bin/env python3
"""Build labeled visual contact sheets from exact native Blockbench captures."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
ASSETS = ("marsh_wight", "crystal_dragonfly", "silt_crocodile", "bubble_pod", "flood_reed", "sunken_shrine", "ancient_boat")
RECEIPT = "crystal-marsh-representative-native-receipt.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    records = []
    for asset in ASSETS:
        root = EVIDENCE / asset
        receipt = json.loads((root / RECEIPT).read_text())
        images = [root / item["path"] for item in receipt["screenshots"]]
        output = root / f"{asset}-native-contact-sheet.png"
        command = [
            "magick", "montage", *map(str, images),
            "-thumbnail", "420x260",
            "-background", "#151922",
            "-fill", "white",
            "-pointsize", "16",
            "-set", "label", "%t",
            "-geometry", "420x295+10+10",
            "-tile", "4x",
            str(output),
        ]
        subprocess.run(command, check=True)
        if output.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError(f"CONTACT_SHEET_NOT_PNG:{asset}")
        records.append({"asset": asset, "path": str(output.relative_to(HERE)), "sha256": sha256(output), "source_screenshot_count": len(images)})
    manifest = {"schema": "aionforge.wave1.crystal_marsh.native_contact_sheets.v1", "assets": records}
    (HERE / "CRYSTAL_MARSH_REPRESENTATIVE_CONTACT_SHEETS.json").write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
    return manifest


if __name__ == "__main__":
    build()
