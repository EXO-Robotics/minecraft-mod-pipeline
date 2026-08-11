#!/usr/bin/env python3
"""Build an evidence-derived receipt for nine ratified economy icons."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE / "source"
SHIPPING = ROOT / "resource_pack/textures/aionbound/whisperwood/items"
OUT = HERE / "WHISPERWOOD_ECONOMY_ICON_RECEIPT.json"

DECODER_PATH = ROOT / "assets/wave1/whisperwood/equipment-icons/build_receipt.py"
SPEC = importlib.util.spec_from_file_location("ww_equipment_icon_decoder", DECODER_PATH)
DECODER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(DECODER)

ASSETS = {
    "mosskip_crown_fragment": "one broken crown-like antler bud fragment, rounded moss-coated tine with a small amber growth ring",
    "thorn_barb": "one sharply hooked thorn barb, dark bark base with moss-green ridge and a tiny amber sap glint",
    "stalker_claw": "one long predatory claw, bark-dark keratin with a serrated thorn ridge and restrained amber tip",
    "hollow_venom_sac": "one compact spider venom sac, deep bark casing with translucent moss-green venom and a small amber vein",
    "moss_bind_glue": "one squat sealed glue jar containing thick moss-green resin, bark stopper and small amber binding band",
    "amber_core": "one faceted hollow amber core held in a minimal dark root cradle, warm amber center and moss flecks",
    "thorn_cord": "one tidy looped cord woven from dark widow silk and green briar fiber, with a single small thorn clasp",
    "cleaver_blank": "one unfinished cleaver blade blank made from curved briar antler and root-dark backing, no handle",
    "living_root_focus": "one compact living root focus, three moss-green roots clasping a glowing amber heart",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    source_ids = {path.name.removesuffix("-chroma.png") for path in SOURCE.glob("*-chroma.png")}
    if source_ids != set(ASSETS):
        raise ValueError(f"source set mismatch: {sorted(source_ids ^ set(ASSETS))}")
    icons = []
    for item_id, subject in ASSETS.items():
        source = SOURCE / f"{item_id}-chroma.png"
        shipping = SHIPPING / f"{item_id}.png"
        width, height, rgba = DECODER.decode_rgba(shipping)
        alphas = rgba[3::4]
        corners = [alphas[0], alphas[31], alphas[31 * 32], alphas[-1]]
        visible = sum(alpha > 0 for alpha in alphas)
        magenta = sum(
            rgba[index] > 200 and rgba[index + 1] < 80 and rgba[index + 2] > 200 and rgba[index + 3] > 0
            for index in range(0, len(rgba), 4)
        )
        if (width, height) != (32, 32) or corners != [0, 0, 0, 0] or not 24 <= visible <= 900 or magenta:
            raise ValueError(f"shipping validation failed: {item_id}: size={width}x{height} corners={corners} visible={visible} magenta={magenta}")
        icons.append({
            "id": item_id,
            "subject_prompt": subject,
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
        "schema": "aionbound.wave1.whisperwood.economy_icons.v1",
        "status": "PASS_STATIC_PRESENTATION",
        "generation_mode": "built_in_imagegen_exactly_one_call_per_distinct_asset",
        "call_count": 9,
        "creative_authority": "program/crazycraft-pack-production-v1/studio-prep/creative/10_icons/ITEM_ICON_DESIGN.md",
        "identity_authority": ["W1-001-WW_APPROVED_AS_WRITTEN", "WAVE_1_ENGINEERING_DECISION_LEDGER approved derived components"],
        "common_prompt": {
            "use_case": "stylized-concept",
            "asset_type": "Minecraft Bedrock 32x32 inventory icon source",
            "style": "handcrafted low-resolution game icon, crisp chunky pixel-art-inspired painted shapes, one clear object",
            "palette": {"moss": "#4a7a48", "amber": "#c48a2e", "bark_shadow": "#3d2e1f"},
            "chroma_background": "#ff00ff",
            "constraints": ["centered single object", "16x16 readable silhouette", "top-left soft light", "no text", "no watermark", "no shadow", "no magenta subject pixels"],
        },
        "postprocess": {
            "helper": "/Users/blakegrove/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py",
            "mode": "auto-key border, soft matte, threshold 12/220, despill",
            "resize": "ImageMagick Lanczos fit within 30x30, centered on transparent 32x32 RGBA canvas",
        },
        "icons": icons,
        "proof_boundary": "Generated inventory presentation plus exact PNG/alpha/chroma validation only; not registry, client render, BDS, balance, console, or release proof.",
    }


if __name__ == "__main__":
    document = build()
    OUT.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": document["status"], "icon_count": len(document["icons"]), "receipt": str(OUT)}, sort_keys=True))
