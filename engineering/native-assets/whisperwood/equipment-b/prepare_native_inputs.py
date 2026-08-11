#!/usr/bin/env python3
"""Stage exact Packet 006 equipment-B inputs with portable Aionbound identity.

The immutable packet is read-only. PNG bytes and canonical geometry authority
are copied byte-for-byte; only copied JSON source/brief identity and texture
paths are normalized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ASSETS = (
    "whisperwood_helmet", "whisperwood_chest", "whisperwood_legs", "whisperwood_boots",
    "moss_charm", "root_bracelet", "lantern_badge", "moon_sap_pendant", "briar_ring",
    "thorn_stalker_skull", "briar_elk_trophy", "mosskip_trophy", "ancient_acorn_display",
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet, output = args.packet.resolve(), args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"OUTPUT_NOT_EMPTY:{output}")
    records = []
    for asset in ASSETS:
        source_model = packet / "assets/editable" / f"{asset}.bbmodel"
        source_texture = packet / "assets/editable" / f"{asset}.png"
        source_brief = packet / "assets/briefs" / f"{asset}.json"
        source_geometry = packet / "assets/export/models" / f"{asset}.geo.json"
        source_animation = packet / "assets/export/animations" / f"{asset}.animation.json"
        paths = (source_model, source_texture, source_brief, source_geometry, source_animation)
        if any(not path.is_file() for path in paths):
            raise SystemExit(f"INPUT_MISSING:{asset}")
        asset_dir = output / asset
        texture_dir = asset_dir / "textures"
        texture_dir.mkdir(parents=True)
        model = json.loads(source_model.read_text())
        brief = json.loads(source_brief.read_text())
        expected_old = f"geometry.aionforge_eq.{asset}"
        if model.get("model_identifier") != expected_old or brief.get("model_identifier") != expected_old:
            raise SystemExit(f"SOURCE_IDENTITY_UNEXPECTED:{asset}")
        model["model_identifier"] = f"geometry.aionbound.{asset}"
        for animation in model.get("animations", []):
            name = animation.get("name")
            if isinstance(name, str):
                animation["name"] = name.replace(f"animation.aionforge_eq.{asset}.", f"animation.aionbound.{asset}.")
        changed_paths = 0
        for texture in model.get("textures", []):
            for key, value in (("name", f"{asset}.png"), ("path", f"textures/{asset}.png"), ("relative_path", f"textures/{asset}.png")):
                if texture.get(key) != value:
                    texture[key] = value
                    changed_paths += 1
        brief["model_identifier"] = f"geometry.aionbound.{asset}"
        model_path, brief_path = asset_dir / f"{asset}.bbmodel", asset_dir / f"{asset}.brief.json"
        model_path.write_bytes(canonical(model))
        native_model = dict(model)
        native_model["model_identifier"] = f"aionbound.{asset}"
        (asset_dir / f"{asset}.native.bbmodel").write_bytes(canonical(native_model))
        brief_path.write_bytes(canonical(brief))
        shutil.copyfile(source_texture, texture_dir / f"{asset}.png")
        shutil.copyfile(source_geometry, asset_dir / f"{asset}.canonical.geo.json")
        shutil.copyfile(source_animation, asset_dir / f"{asset}.canonical.animation.json")
        if digest(source_texture) != digest(texture_dir / f"{asset}.png"):
            raise SystemExit(f"TEXTURE_BYTES_CHANGED:{asset}")
        records.append({
            "asset": asset,
            "source_model_sha256": digest(source_model),
            "staged_model_sha256": digest(model_path),
            "texture_sha256": digest(source_texture),
            "texture_dimensions": [32, 32],
            "portable_texture_fields_normalized": changed_paths,
            "runtime_namespace": "aionbound",
        })
    receipt = {"schema_version": 1, "status": "PASS", "assets": records, "texture_policy": "EXACT_32X32_BYTES_PRESERVED_NO_UPSCALE"}
    (output / "STAGING_RECEIPT.json").write_bytes(canonical(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
