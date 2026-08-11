#!/usr/bin/env python3
"""Build an evidence-derived receipt for the 21 Whisperwood equipment icons."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
import zlib


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE / "source"
SHIPPING = ROOT / "resource_pack/textures/aionbound/whisperwood/equipment"
OUT = HERE / "WHISPERWOOD_EQUIPMENT_ICON_RECEIPT.json"

ASSETS = {
    "weapons": ["mossfang_spear", "widow_fang_dagger", "thorn_whip", "briar_cleaver", "moon_sap_staff"],
    "armor": ["whisperwood_helmet", "whisperwood_chest", "whisperwood_legs", "whisperwood_boots"],
    "tools": ["root_knife", "whisperwood_hatchet", "lantern_hook"],
    "accessories": ["moss_charm", "root_bracelet", "lantern_badge", "moon_sap_pendant", "briar_ring"],
    "trophies": ["thorn_stalker_skull", "briar_elk_trophy", "mosskip_trophy", "ancient_acorn_display"],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_rgba(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"bad PNG signature: {path}")
    offset, width, height, compressed = 8, None, None, bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            raise ValueError(f"bad PNG CRC: {path}")
        offset += 12 + length
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (depth, color, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError(f"expected non-interlaced 8-bit RGBA: {path}")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    raw = zlib.decompress(bytes(compressed))
    stride, prior, rows = width * 4, bytearray(width * 4), []
    if len(raw) != height * (stride + 1):
        raise ValueError(f"decoded row length mismatch: {path}")
    cursor = 0
    for _ in range(height):
        filter_type, cursor = raw[cursor], cursor + 1
        scan = bytearray(raw[cursor:cursor + stride])
        cursor += stride
        for index in range(stride):
            left = scan[index - 4] if index >= 4 else 0
            up = prior[index]
            upper_left = prior[index - 4] if index >= 4 else 0
            if filter_type == 1:
                scan[index] = (scan[index] + left) & 255
            elif filter_type == 2:
                scan[index] = (scan[index] + up) & 255
            elif filter_type == 3:
                scan[index] = (scan[index] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                estimate = left + up - upper_left
                distances = abs(estimate - left), abs(estimate - up), abs(estimate - upper_left)
                predictor = left if distances[0] <= distances[1] and distances[0] <= distances[2] else up if distances[1] <= distances[2] else upper_left
                scan[index] = (scan[index] + predictor) & 255
            elif filter_type != 0:
                raise ValueError(f"unknown PNG filter: {path}")
        rows.append(bytes(scan))
        prior = scan
    return width, height, b"".join(rows)


def build() -> dict:
    expected_ids = [asset for category in ASSETS.values() for asset in category]
    source_ids = {path.name.removesuffix("-chroma.png") for path in SOURCE.glob("*-chroma.png")}
    shipping_ids = {path.stem for path in SHIPPING.glob("*.png")}
    if source_ids != set(expected_ids) or shipping_ids != set(expected_ids):
        raise ValueError("icon file set does not match exact 21-ID authority")
    icons = []
    for category, ids in ASSETS.items():
        for asset in ids:
            source = SOURCE / f"{asset}-chroma.png"
            shipping = SHIPPING / f"{asset}.png"
            width, height, rgba = decode_rgba(shipping)
            if (width, height) != (32, 32):
                raise ValueError(f"wrong shipping size: {asset}")
            alphas = rgba[3::4]
            corners = [alphas[0], alphas[31], alphas[31 * 32], alphas[-1]]
            visible = sum(alpha > 0 for alpha in alphas)
            magenta = sum(
                rgba[index] > 200 and rgba[index + 1] < 80 and rgba[index + 2] > 200 and rgba[index + 3] > 0
                for index in range(0, len(rgba), 4)
            )
            if corners != [0, 0, 0, 0] or not 24 <= visible <= 900 or magenta:
                raise ValueError(
                    f"alpha/coverage/chroma validation failed: {asset}: "
                    f"corners={corners} visible={visible} magenta={magenta}"
                )
            icons.append({
                "id": asset,
                "category": category,
                "source_path": source.relative_to(ROOT).as_posix(),
                "source_sha256": sha256(source),
                "shipping_path": shipping.relative_to(ROOT).as_posix(),
                "shipping_sha256": sha256(shipping),
                "shipping_size": [width, height],
                "visible_pixel_count": visible,
                "visible_magenta_pixel_count": magenta,
                "transparent_corner_alpha": corners,
            })
    return {
        "schema": "aionbound.wave1.whisperwood.equipment_icons.v1",
        "status": "PASS_STATIC_PRESENTATION",
        "generation_mode": "built_in_imagegen_one_call_per_distinct_asset",
        "creative_authority": "program/crazycraft-pack-production-v1/studio-prep/creative/10_icons/ITEM_ICON_DESIGN.md",
        "prompt_contract": {
            "use_case": "stylized-concept",
            "canvas_intent": "32x32 shipping icon with 16x16 readability proof",
            "palette": {"moss": "#4a7a48", "amber": "#c48a2e", "bark_shadow": "#3d2e1f"},
            "chroma_background": "#ff00ff",
            "constraints": ["one idea per icon", "mesh graphic cousin", "top-left soft light", "no text", "no watermark", "no cast shadow"],
        },
        "postprocess": {
            "helper": "/Users/blakegrove/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py",
            "mode": "auto-key border, soft matte, despill",
            "resize": "ImageMagick Lanczos fit within 32x32 transparent canvas",
        },
        "icon_count": len(icons),
        "icons": icons,
        "proof_boundary": "Generated inventory presentation and static PNG/alpha/readability inspection only; not item registry, attachable, client render, BDS, console, or release proof.",
    }


if __name__ == "__main__":
    document = build()
    OUT.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": document["status"], "icon_count": document["icon_count"], "receipt": str(OUT)}, sort_keys=True))
