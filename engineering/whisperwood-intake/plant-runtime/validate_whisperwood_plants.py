#!/usr/bin/env python3
"""Static/reference-closure validator for Packet 001 plant blocks."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import struct
import zlib
from pathlib import Path

from build_whisperwood_plants import PLANTS


ANIMATED_SOURCE_ASSETS = {
    "lantern_bloom": "animation.aionforge_ww.lantern_bloom.glow_idle",
    "pale_reed": "animation.aionforge_ww.pale_reed.sway",
    "star_grass": "animation.aionforge_ww.star_grass.wind_sway",
    "whisper_fern": "animation.aionforge_ww.whisper_fern.gentle_sway",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def decode_png(path: Path) -> dict:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path}: invalid PNG signature")
    offset = 8
    idat = bytearray()
    ihdr = None
    saw_iend = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise AssertionError(f"{path}: truncated PNG chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : offset + 12 + length])[0]
        actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise AssertionError(f"{path}: bad {kind!r} CRC")
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            saw_iend = True
            if offset + 12 + length != len(data):
                raise AssertionError(f"{path}: trailing bytes after IEND")
        offset += 12 + length
    if not saw_iend or ihdr is None:
        raise AssertionError(f"{path}: incomplete PNG")
    width, height, bit_depth, color_type, compression, filtering, interlace = ihdr
    if (width, height, bit_depth, color_type, compression, filtering, interlace) != (32, 32, 8, 6, 0, 0, 0):
        raise AssertionError(f"{path}: expected non-interlaced 32x32 RGBA8, got {ihdr}")
    raw = zlib.decompress(bytes(idat))
    expected_size = height * (1 + width * 4)
    if len(raw) != expected_size:
        raise AssertionError(f"{path}: decoded scanline size {len(raw)} != {expected_size}")
    if any(raw[row * (1 + width * 4)] > 4 for row in range(height)):
        raise AssertionError(f"{path}: illegal PNG filter byte")
    return {"width": width, "height": height, "mode": "RGBA8", "decoded_bytes": len(raw)}


def geometry_payload(value: dict) -> dict:
    normalized = copy.deepcopy(value)
    normalized["minecraft:geometry"][0]["description"]["identifier"] = "<normalized>"
    return normalized


def evidence_texture_hash(receipt: dict) -> str:
    if "inputs" in receipt:
        return receipt["inputs"]["texture"]["sha256"]
    return receipt["evidence_inputs"]["texture"]["sha256"]


def validate(repo: Path) -> dict:
    blocks_registry = parse_json(repo / "resource_pack/blocks.json")
    terrain = parse_json(repo / "resource_pack/textures/terrain_texture.json")["texture_data"]
    lang = (repo / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8").splitlines()
    evidence_root = repo / "engineering/native-assets/whisperwood/evidence"
    assets = []

    for asset, spec in PLANTS.items():
        block_path = repo / f"behavior_pack/blocks/{asset}.block.json"
        geometry_path = repo / f"resource_pack/models/aionbound/whisperwood/{asset}.geo.json"
        texture_path = repo / f"resource_pack/textures/aionbound/whisperwood/plants/{asset}.png"
        receipt_name = "plant-animation-native-receipt.json" if asset in ANIMATED_SOURCE_ASSETS else "whisperwood-native-blockbench-receipt.json"
        receipt_path = evidence_root / asset / receipt_name
        evidence_geo_path = evidence_root / asset / "native-exports/pass-2.geo.json"

        block = parse_json(block_path)
        geometry = parse_json(geometry_path)
        evidence_geometry = parse_json(evidence_geo_path)
        receipt = parse_json(receipt_path)
        assert receipt["status"] == "PASS", f"{asset}: native evidence is not PASS"

        description = block["minecraft:block"]["description"]
        components = block["minecraft:block"]["components"]
        expected_id = f"aionbound:{asset}"
        expected_geometry = f"geometry.aionbound.{asset}"
        assert block["format_version"] == "1.21.80"
        assert description["identifier"] == expected_id
        assert description["menu_category"] == {"category": "nature"}
        assert components["minecraft:display_name"] == spec["display"]
        assert components["minecraft:collision_box"] is False
        assert components["minecraft:selection_box"] == spec["selection"]
        assert components["minecraft:destructible_by_mining"]["seconds_to_destroy"] > 0
        loot_path = f"loot_tables/blocks/{asset}.json"
        assert components["minecraft:loot"] == loot_path, f"{asset}: ratified harvest table is not bound"
        assert (repo / "behavior_pack" / loot_path).is_file(), f"{asset}: missing ratified harvest table"
        assert components["minecraft:geometry"] == expected_geometry
        material = components["minecraft:material_instances"]
        assert set(material) == {"*"}
        assert material["*"]["texture"] == asset
        assert material["*"]["render_method"] == "alpha_test"
        assert material["*"]["ambient_occlusion"] is False
        assert material["*"]["face_dimming"] is False
        placement = components["minecraft:placement_filter"]["conditions"]
        assert placement == [{"allowed_faces": spec["faces"], "block_filter": spec["supports"]}]

        shipping_description = geometry["minecraft:geometry"][0]["description"]
        assert shipping_description["identifier"] == expected_geometry
        assert "aionforge_ww" not in json.dumps(geometry)
        assert geometry_payload(geometry) == geometry_payload(evidence_geometry), f"{asset}: geometry shape drift"
        assert blocks_registry[expected_id] == {"sound": "grass", "textures": asset}
        assert terrain[asset] == {"textures": f"textures/aionbound/whisperwood/plants/{asset}"}
        assert lang.count(f"tile.{expected_id}.name={spec['display']}") == 1

        png = decode_png(texture_path)
        runtime_texture_hash = sha256(texture_path)
        assert runtime_texture_hash == evidence_texture_hash(receipt), f"{asset}: texture differs from native-evidence input"

        assets.append(
            {
                "asset": asset,
                "runtime_id": expected_id,
                "geometry_identifier": expected_geometry,
                "geometry_sha256": sha256(geometry_path),
                "texture_sha256": runtime_texture_hash,
                "png": png,
                "placement_faces": spec["faces"],
                "support_blocks": spec["supports"],
                "collision": "NONE",
                "selection_box": spec["selection"],
                "harvest_semantics": "RATIFIED_LOOT_TABLE_BOUND_NOT_RUNTIME_PROVEN",
                "native_evidence_status": receipt["status"],
                "source_animation": ANIMATED_SOURCE_ASSETS.get(asset),
                "runtime_animation": "WITHHELD_UNSUPPORTED_CUSTOM_BLOCK_SKELETAL_PLAYBACK" if asset in ANIMATED_SOURCE_ASSETS else "NOT_REQUIRED",
            }
        )

    runtime_animation_text = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in (repo / "resource_pack").rglob("*.json")
        if "models/aionbound/whisperwood" not in p.as_posix()
    )
    for animation_id in ANIMATED_SOURCE_ASSETS.values():
        assert animation_id not in runtime_animation_text, f"runtime unexpectedly binds {animation_id}"

    return {
        "schema_version": 1,
        "status": "PASS_STATIC_REFERENCE_CLOSURE",
        "asset_count": len(assets),
        "runtime_form": "STATIC_CUSTOM_BLOCK_GEOMETRY",
        "render_method": "alpha_test",
        "animation_policy": {
            "native_source_clips_preserved": sorted(ANIMATED_SOURCE_ASSETS.values()),
            "runtime_playback": "WITHHELD",
            "reason": "Stable custom-block geometry has no clean entity-style skeletal animation-controller binding; no Script API or entity surrogate was authorized.",
        },
        "checks": [
            "BP block JSON and stable format",
            "aionbound identifier and geometry namespace closure",
            "native-evidence geometry equivalence excluding intended identifier normalization",
            "exact native-evidence texture-byte equality",
            "complete PNG CRC, IDAT, scanline, dimension, and RGBA8 decode",
            "blocks.json, terrain_texture.json, and en_US.lang closure",
            "uniform alpha_test material pipeline",
            "role-grounded selection and placement filters",
            "ratified harvest-table closure and no runtime animation binding",
        ],
        "assets": assets,
        "proof_boundary": {
            "proven": ["STATIC_JSON", "STATIC_REFERENCE_CLOSURE", "PNG_DECODE", "NATIVE_EVIDENCE_REUSE"],
            "not_proven": ["CREATOR_TOOLS", "STABLE_BDS", "BEDROCK_CLIENT_RENDER", "PLACEMENT_RUNTIME", "HARVEST_RUNTIME", "ANIMATION_PLAYBACK", "WORLD_GENERATION", "PHYSICAL_PS4", "MARKETPLACE"],
        },
    }


def write_reports(repo: Path, report: dict) -> None:
    output = repo / "engineering/whisperwood-intake/plant-runtime"
    json_path = output / "WHISPERWOOD_PLANT_RUNTIME_REPORT.json"
    md_path = output / "WHISPERWOOD_PLANT_RUNTIME_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    rows = "\n".join(
        f"| `{item['asset']}` | `{item['runtime_id']}` | `{item['placement_faces'][0]}` | `{item['runtime_animation']}` |"
        for item in report["assets"]
    )
    md_path.write_text(
        "# Whisperwood Plant Runtime Static Report\n\n"
        f"Status: `{report['status']}`\n\n"
        "Ten Packet 001 plants are bound as non-colliding, selectable, placeable, breakable custom blocks using the exact native-evidence geometry and texture bytes. Shipping geometry identifiers are normalized to `geometry.aionbound.*`; shape payloads are unchanged.\n\n"
        "| Plant | Runtime ID | Placement face | Skeletal playback |\n"
        "| --- | --- | --- | --- |\n"
        f"{rows}\n\n"
        "## Animation decision\n\n"
        "The four approved Blockbench-authored clips remain in immutable native evidence. They are not copied into the RP because Stable custom-block geometry has no clean entity-style skeletal animation-controller binding. No entity surrogate or Script API behavior was introduced.\n\n"
        "## Proof boundary\n\n"
        "Proven here: JSON parsing, namespace/identifier/reference closure, native-evidence geometry equivalence, exact source texture-byte equality, full PNG decode, role-grounded static placement/selection definitions, and absence of invented loot or animation bindings.\n\n"
        "Not proven here: Creator Tools, Stable BDS, Bedrock client rendering, live placement/harvest behavior, animation playback, world generation, physical console behavior, or Marketplace acceptance.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = validate(args.repo.resolve())
    if args.write_report:
        write_reports(args.repo.resolve(), report)
    print(json.dumps({"status": report["status"], "asset_count": report["asset_count"]}))


if __name__ == "__main__":
    main()
