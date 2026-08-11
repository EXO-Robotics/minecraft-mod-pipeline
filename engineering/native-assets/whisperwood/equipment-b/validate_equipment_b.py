#!/usr/bin/env python3
"""Fail-closed validation and deterministic aggregate receipt for equipment-B."""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
import zlib
from pathlib import Path


ASSETS = (
    "whisperwood_helmet", "whisperwood_chest", "whisperwood_legs", "whisperwood_boots",
    "moss_charm", "root_bracelet", "lantern_badge", "moon_sap_pendant", "briar_ring",
    "thorn_stalker_skull", "briar_elk_trophy", "mosskip_trophy", "ancient_acorn_display",
)
CLIPS = {"moss_charm": ["idle_sway"], "moon_sap_pendant": ["pulse"]}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def decode_png(path: Path, expected: tuple[int, int, int, int] | None = None) -> tuple[int, int, int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"PNG_SIGNATURE:{path}")
    offset, idat, width, height, depth, color, ended = 8, bytearray(), None, None, None, None, False
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        if binascii.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise AssertionError(f"PNG_CRC:{path}:{kind!r}")
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", payload[:10])
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            ended = True
            offset += 12 + length
            break
        offset += 12 + length
    if not ended or offset != len(data):
        raise AssertionError(f"PNG_STREAM:{path}")
    raw = zlib.decompress(bytes(idat))
    channels = {2: 3, 6: 4}.get(color)
    if channels is None or depth != 8 or len(raw) != height * (1 + width * channels):
        raise AssertionError(f"PNG_FORMAT:{path}:{width}x{height}:{depth}:{color}:{len(raw)}")
    if expected is not None and (width, height, depth, color) != expected:
        raise AssertionError(f"PNG_EXPECTED_FORMAT:{path}:{width}x{height}:{depth}:{color}")
    return width, height, depth, color


def locator(geometry: dict, name: str) -> dict:
    found = []
    for entry in geometry.get("minecraft:geometry", []):
        for bone in entry.get("bones", []):
            if name in bone.get("locators", {}):
                found.append({"parent": bone["name"], "value": bone["locators"][name]})
    if len(found) != 1:
        raise AssertionError(f"LOCATOR_CARDINALITY:{name}:{len(found)}")
    return found[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    staging = json.loads((root / "inputs/STAGING_RECEIPT.json").read_text())
    if [row["asset"] for row in staging["assets"]] != list(ASSETS):
        raise AssertionError("STAGING_ASSET_SET")
    results = []
    for asset in ASSETS:
        input_dir, evidence = root / "inputs" / asset, root / "evidence" / asset
        texture = input_dir / "textures" / f"{asset}.png"
        decode_png(texture, (32, 32, 8, 6))
        row = next(record for record in staging["assets"] if record["asset"] == asset)
        if digest(texture) != row["texture_sha256"]:
            raise AssertionError(f"TEXTURE_HASH:{asset}")
        model = json.loads((input_dir / f"{asset}.bbmodel").read_text())
        native_model = json.loads((input_dir / f"{asset}.native.bbmodel").read_text())
        brief = json.loads((input_dir / f"{asset}.brief.json").read_text())
        expected_geometry = f"geometry.aionbound.{asset}"
        if model.get("model_identifier") != expected_geometry or brief.get("model_identifier") != expected_geometry:
            raise AssertionError(f"NAMESPACE:{asset}")
        if native_model.get("model_identifier") != f"aionbound.{asset}":
            raise AssertionError(f"NATIVE_PROJECT_NAMESPACE:{asset}")
        for texture_record in model.get("textures", []):
            expected_path = f"textures/{asset}.png"
            if texture_record.get("path") != expected_path or texture_record.get("relative_path") != expected_path:
                raise AssertionError(f"TEXTURE_PATH:{asset}")
        animated = asset in CLIPS
        receipt_path = evidence / ("entity-animation-native-receipt.json" if animated else "whisperwood-native-blockbench-receipt.json")
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("status") != "PASS" or receipt.get("native_result", {}).get("warning_count") != 0 or receipt.get("native_result", {}).get("error_count", 0) != 0:
            raise AssertionError(f"NATIVE_STATUS:{asset}")
        exports = receipt.get("exports", {})
        if not all(exports.get(kind, {}).get("canonical_equivalent") is True for kind in ("geometry", "animations")):
            raise AssertionError(f"TWO_PASS_EQUIVALENCE:{asset}")
        final_geo = json.loads((evidence / "native-exports/pass-2.geo.json").read_text())
        identifiers = [entry.get("description", {}).get("identifier") for entry in final_geo.get("minecraft:geometry", [])]
        if identifiers != [expected_geometry]:
            raise AssertionError(f"NATIVE_NAMESPACE:{asset}:{identifiers}")
        canonical_geo = json.loads((input_dir / f"{asset}.canonical.geo.json").read_text())
        if locator(final_geo, "effect") != locator(canonical_geo, "effect"):
            raise AssertionError(f"LOCATOR_AUTHORITY:{asset}")
        screenshots = receipt.get("screenshots", [])
        if animated:
            expected_clips = CLIPS[asset]
            if receipt.get("brief_approved_clips") != expected_clips or len(screenshots) != len(expected_clips):
                raise AssertionError(f"CLIP_SET:{asset}")
            for screenshot in screenshots:
                path = evidence / screenshot["path"]
                decode_png(path)
                if digest(path) != screenshot["sha256"]:
                    raise AssertionError(f"SCREENSHOT_HASH:{asset}")
        elif screenshots:
            raise AssertionError(f"UNREQUESTED_SCREENSHOTS:{asset}")
        results.append({
            "asset": asset,
            "status": "PASS",
            "geometry_identifier": expected_geometry,
            "effect_locator": locator(final_geo, "effect"),
            "declared_clips": CLIPS.get(asset, []),
            "texture_sha256": digest(texture),
            "texture_dimensions": [32, 32],
            "native_receipt": str(receipt_path.relative_to(root)),
            "native_receipt_sha256": digest(receipt_path),
            "two_pass_geometry_equivalent": True,
            "two_pass_animation_equivalent": True,
            "zero_warning_native_session": True,
            "screenshots": screenshots,
        })
    report = {
        "schema_version": 1,
        "status": "PASS",
        "audited_integration_head": "668993d1b5fc7a676181063eef1b9dd721d5b2a4",
        "scope": "BLOCKBENCH_NATIVE_EQUIPMENT_B_ONLY",
        "asset_count": len(results),
        "assets": results,
        "texture_policy": "EXACT_32X32_PACKET_BYTES_PRESERVED_NO_UPSCALE",
        "proof_boundary": ["NOT_BP_RP_INTEGRATION", "NOT_BEDROCK_CLIENT", "NOT_STABLE_BDS", "NOT_PHYSICAL_PS4", "NOT_MARKETPLACE"],
    }
    report_path = args.report.resolve() if args.report else root / "EQUIPMENT_B_NATIVE_REPORT.json"
    report_path.write_bytes(canonical(report))
    print(json.dumps({"status": "PASS", "assets": len(results), "report": str(report_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
