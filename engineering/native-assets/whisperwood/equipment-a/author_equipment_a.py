#!/usr/bin/env python3
"""Native Blockbench repair lane A for eight Packet 006 Whisperwood items.

The frozen packet inputs are never edited. Each asset is normalized in a
disposable staging directory, then passed through the existing fail-closed
Blockbench 5.1.6 native authoring transaction. Evidence is augmented with the
exact canonical packet inputs and the explicit source-to-shipping namespace
binding. This lane does not edit BP/RP runtime files or define gameplay.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
WHISPERWOOD_NATIVE = HERE.parent
SHARED_TOOL = WHISPERWOOD_NATIVE / "entity-animation-repair-a" / "author_entity_animations.py"
DEFAULT_PACKET_ROOT = Path(
    "/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/"
    "studio-prep/sprints/asset-sprint-006-equipment-progression"
)


def load_shared_lane():
    spec = importlib.util.spec_from_file_location("whisperwood_equipment_native_shared", SHARED_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"CANNOT_LOAD_SHARED_NATIVE_LANE:{SHARED_TOOL}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lane = load_shared_lane()
native = lane.native
ZERO = [0.0, 0.0, 0.0]


def frames(channel: str, *entries: tuple[float, list[float]]):
    return lane.frames(channel, *entries)


def clip(duration: float, loop: bool, proof_time: float, bones: dict[str, list[dict[str, Any]]]):
    return lane.clip(duration, loop, proof_time, bones)


def idle_hold(duration: float = 3.0, proof_time: float = 0.75):
    return clip(duration, True, proof_time, {
        "grip": [frames(
            "rotation",
            (0.0, ZERO),
            (duration * 0.25, [0.7, 0.0, 1.2]),
            (duration * 0.5, ZERO),
            (duration * 0.75, [-0.5, 0.0, -1.0]),
            (duration, ZERO),
        )],
    })


EQUIPMENT_SPECS: dict[str, dict[str, Any]] = {
    "mossfang_spear": {
        "role": "Whisperwood reach spear; moss fang tip",
        "clips": {
            "idle_hold": idle_hold(),
            "thrust_pose": clip(0.6, False, 0.42, {
                "grip": [frames("rotation", (0.0, ZERO), (0.18, [-7.0, 0.0, 0.0]), (0.42, [11.0, 0.0, 0.0]), (0.6, [6.0, 0.0, 0.0]))],
                "head": [frames("position", (0.0, ZERO), (0.18, [0.0, 0.0, 0.25]), (0.42, [0.0, 0.0, -1.8]), (0.6, [0.0, 0.0, -0.8]))],
            }),
            "sweep_pose": clip(0.8, False, 0.45, {
                "grip": [frames("rotation", (0.0, [0.0, -18.0, -5.0]), (0.45, [0.0, 20.0, 7.0]), (0.8, [0.0, 5.0, 1.0]))],
            }),
        },
    },
    "widow_fang_dagger": {
        "role": "Curved widow-fang dagger",
        "clips": {
            "idle_hold": idle_hold(2.6, 0.65),
            "stab_pose": clip(0.45, False, 0.3, {
                "grip": [frames("rotation", (0.0, ZERO), (0.14, [-9.0, 0.0, 3.0]), (0.3, [13.0, 0.0, -2.0]), (0.45, [5.0, 0.0, 0.0]))],
                "head": [frames("position", (0.0, ZERO), (0.14, [0.0, 0.0, 0.2]), (0.3, [0.0, 0.0, -1.2]), (0.45, [0.0, 0.0, -0.45]))],
            }),
        },
    },
    "thorn_whip": {
        "role": "Living briar lash whip",
        "clips": {
            "idle_coil": clip(3.2, True, 0.8, {
                "head": [frames("rotation", (0.0, ZERO), (0.8, [0.0, 3.0, 1.8]), (1.6, ZERO), (2.4, [0.0, -2.5, -1.5]), (3.2, ZERO))],
            }),
            "crack_pose": clip(0.65, False, 0.38, {
                "grip": [frames("rotation", (0.0, [0.0, -12.0, -4.0]), (0.22, [0.0, 18.0, 8.0]), (0.38, [0.0, 28.0, -10.0]), (0.65, [0.0, 8.0, -2.0]))],
                "head": [frames("rotation", (0.0, ZERO), (0.22, [0.0, -8.0, 4.0]), (0.38, [0.0, 16.0, -7.0]), (0.65, [0.0, 4.0, -2.0]))],
            }),
            "extend_pose": clip(0.8, False, 0.55, {
                "head": [frames("position", (0.0, ZERO), (0.25, [0.0, 0.0, -0.7]), (0.55, [0.0, 0.0, -2.4]), (0.8, [0.0, 0.0, -1.1]))],
            }),
        },
    },
    "briar_cleaver": {
        "role": "Heavy briar short cleaver",
        "clips": {
            "idle_hold": idle_hold(3.4, 0.85),
            "chop_pose": clip(0.8, False, 0.5, {
                "grip": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.22, [-34.0, 0.0, 0.0]), (0.5, [32.0, 0.0, 0.0]), (0.8, [10.0, 0.0, 0.0]))],
            }),
        },
    },
    "moon_sap_staff": {
        "role": "Whisperwood cast staff with moon-sap orb",
        "clips": {
            "idle_hold": idle_hold(3.6, 0.9),
            "cast_raise": clip(1.0, False, 0.7, {
                "grip": [frames("rotation", (0.0, ZERO), (0.35, [-8.0, 0.0, -4.0]), (0.7, [-18.0, 0.0, -8.0]), (1.0, [-12.0, 0.0, -5.0]))],
                "head": [frames("position", (0.0, ZERO), (0.35, [0.0, 0.35, 0.0]), (0.7, [0.0, 1.0, 0.0]), (1.0, [0.0, 0.7, 0.0]))],
            }),
            "pulse": clip(2.0, True, 1.0, {
                "chassis": [frames("scale", (0.0, [1.0, 1.0, 1.0]), (0.5, [1.02, 1.02, 1.02]), (1.0, [1.055, 1.055, 1.055]), (1.5, [1.02, 1.02, 1.02]), (2.0, [1.0, 1.0, 1.0]))],
            }),
        },
    },
    "root_knife": {
        "role": "Forest utility knife",
        "clips": {
            "hold": idle_hold(2.4, 0.6),
        },
    },
    "whisperwood_hatchet": {
        "role": "Forest chop hatchet",
        "clips": {
            "hold": idle_hold(2.8, 0.7),
            "chop": clip(0.7, False, 0.44, {
                "grip": [frames("rotation", (0.0, [-16.0, 0.0, 0.0]), (0.2, [-30.0, 0.0, 0.0]), (0.44, [28.0, 0.0, 0.0]), (0.7, [8.0, 0.0, 0.0]))],
            }),
        },
    },
    "lantern_hook": {
        "role": "Hook pole with lantern cage",
        "clips": {
            "hold": idle_hold(3.0, 0.75),
            "hang": clip(3.2, True, 0.8, {
                "head": [frames("rotation", (0.0, ZERO), (0.8, [0.0, 0.0, 3.0]), (1.6, ZERO), (2.4, [0.0, 0.0, -2.5]), (3.2, ZERO))],
            }),
        },
    },
}


lane.ENTITY_SPECS = EQUIPMENT_SPECS
lane.TOOL_VERSION = "whisperwood-equipment-a-1.0.0"
lane.RECEIPT_NAME = "equipment-a-native-receipt.json"
lane.PROOF_SCOPE = "BLOCKBENCH_5_1_6_NATIVE_WHISPERWOOD_EQUIPMENT_A_SOURCE_AND_CODEC_EXPORT_ONLY"
lane.NON_CLAIMS = [
    "BP_RP_RUNTIME_BINDING",
    "GAMEPLAY_ITEM_BEHAVIOR",
    "LOOT_OR_RECIPE_ACQUISITION",
    "BEDROCK_CLIENT",
    "STABLE_BDS",
    "PHYSICAL_PS4",
    "MARKETPLACE",
]


def canonical_paths(packet_root: Path, asset: str) -> dict[str, Path]:
    return {
        "bbmodel": packet_root / "assets/editable" / f"{asset}.bbmodel",
        "texture": packet_root / "assets/editable" / f"{asset}.png",
        "geometry": packet_root / "assets/export/models" / f"{asset}.geo.json",
        "animation": packet_root / "assets/export/animations" / f"{asset}.animation.json",
        "brief": packet_root / "assets/briefs" / f"{asset}.json",
    }


def normalized_json(value: Any, source_prefix: str, shipping_prefix: str) -> Any:
    if isinstance(value, str):
        return value.replace(source_prefix, shipping_prefix)
    if isinstance(value, list):
        return [normalized_json(item, source_prefix, shipping_prefix) for item in value]
    if isinstance(value, dict):
        return {key: normalized_json(item, source_prefix, shipping_prefix) for key, item in value.items()}
    return value


def stage_normalized_inputs(packet_root: Path, asset: str, staging: Path) -> tuple[dict[str, Path], dict[str, str]]:
    staging.mkdir(parents=True, exist_ok=True)
    source = canonical_paths(packet_root, asset)
    for label, path in source.items():
        if not path.is_file():
            raise lane.EntityAnimationError(f"CANONICAL_INPUT_MISSING:{label}:{path}")

    source_prefix = f"aionforge_eq.{asset}"
    shipping_prefix = f"aionbound.{asset}"
    bbmodel = json.loads(source["bbmodel"].read_text())
    geometry = json.loads(source["geometry"].read_text())
    brief = json.loads(source["brief"].read_text())
    bbmodel = normalized_json(bbmodel, source_prefix, shipping_prefix)
    geometry = normalized_json(geometry, source_prefix, shipping_prefix)
    brief = normalized_json(brief, source_prefix, shipping_prefix)

    texture_name = f"{asset}.png"
    native.normalize_texture_records(bbmodel, texture_name)
    normalized = {
        "bbmodel": staging / f"{asset}.normalized.bbmodel",
        "texture": staging / texture_name,
        "geometry": staging / f"{asset}.normalized.geo.json",
        "brief": staging / f"{asset}.normalized.brief.json",
    }
    normalized["bbmodel"].write_bytes(native.canonical_json_bytes(bbmodel))
    normalized["geometry"].write_bytes(native.canonical_json_bytes(geometry))
    normalized["brief"].write_bytes(native.canonical_json_bytes(brief))
    shutil.copyfile(source["texture"], normalized["texture"])
    return normalized, {label: native.sha256_file(path) for label, path in source.items()}


def copy_canonical_inputs(packet_root: Path, asset: str, output: Path) -> dict[str, dict[str, str]]:
    directory = output / "canonical-inputs"
    directory.mkdir()
    source = canonical_paths(packet_root, asset)
    suffixes = {
        "bbmodel": ".source.bbmodel",
        "texture": ".source.png",
        "geometry": ".source.geo.json",
        "animation": ".source.animation.json",
        "brief": ".brief.json",
    }
    records: dict[str, dict[str, str]] = {}
    for label, path in source.items():
        target = directory / f"{asset}{suffixes[label]}"
        shutil.copyfile(path, target)
        records[label] = lane.file_record(target, output)
    return records


def validate_texture_preservation(asset: str, canonical_texture: Path, receipt: dict[str, Any], output: Path) -> dict[str, Any]:
    canonical_hash = native.sha256_file(canonical_texture)
    staged_hash = receipt["staged_texture"]["sha256"]
    evidence_hash = receipt["evidence_inputs"]["texture"]["sha256"]
    if canonical_hash != staged_hash or canonical_hash != evidence_hash:
        raise lane.EntityAnimationError(f"TEXTURE_BYTES_CHANGED:{asset}")
    png = canonical_texture.read_bytes()
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise lane.EntityAnimationError(f"TEXTURE_NOT_PNG:{asset}")
    width = int.from_bytes(png[16:20], "big")
    height = int.from_bytes(png[20:24], "big")
    if [width, height] != [32, 32]:
        raise lane.EntityAnimationError(f"TEXTURE_DIMENSION_DRIFT:{asset}:{width}x{height}")
    return {
        "policy": "PRESERVE_APPROVED_PACKET_PIXELS_NO_UPSCALE",
        "dimensions": [width, height],
        "canonical_sha256": canonical_hash,
        "normalized_input_sha256": evidence_hash,
        "native_project_texture_sha256": staged_hash,
        "byte_identical": True,
    }


def execute_asset(asset: str, packet_root: Path, output_root: Path, endpoint: str, capture: bool) -> dict[str, Any]:
    if asset not in EQUIPMENT_SPECS:
        raise lane.EntityAnimationError(f"UNSUPPORTED_ASSET:{asset}")
    output = output_root / asset
    with tempfile.TemporaryDirectory(prefix=f"aionbound-{asset}-", dir="/private/tmp") as temporary:
        normalized, canonical_hashes = stage_normalized_inputs(packet_root, asset, Path(temporary))
        code, receipt = lane.execute(lane.Inputs(
            asset,
            normalized["bbmodel"],
            normalized["texture"],
            normalized["geometry"],
            normalized["brief"],
            output,
            endpoint,
            capture,
        ))
        if code != 0 or receipt.get("status") != "PASS":
            raise lane.EntityAnimationError(f"NATIVE_LANE_FAILED:{asset}:{receipt.get('diagnostics')}")

    canonical = copy_canonical_inputs(packet_root, asset, output)
    source_identifier = f"geometry.aionforge_eq.{asset}"
    shipping_identifier = f"geometry.aionbound.{asset}"
    receipt["warehouse_canonical_inputs"] = canonical
    receipt["warehouse_canonical_hashes_before_staging"] = canonical_hashes
    receipt["namespace_normalization"] = {
        "warehouse_geometry_identifier": source_identifier,
        "shipping_geometry_identifier": shipping_identifier,
        "warehouse_animation_prefix": f"animation.aionforge_eq.{asset}",
        "shipping_animation_prefix": f"animation.aionbound.{asset}",
        "warehouse_id_unchanged": asset,
    }
    receipt["texture_preservation"] = validate_texture_preservation(
        asset, canonical_paths(packet_root, asset)["texture"], receipt, output
    )
    receipt["brief_texture_declaration"] = {
        "declared": "64x64",
        "packet_actual": "32x32",
        "resolution_action": "NO_UPSCALE_PRESERVE_PACKET_BYTES",
    }
    receipt["scope_enforcement"] = {
        "exact_lane_assets": sorted(EQUIPMENT_SPECS),
        "bp_rp_files_edited": False,
        "gameplay_or_loot_defined": False,
    }
    if receipt["native_result"].get("warning_count") != 0 or receipt["native_result"].get("error_count") != 0:
        raise lane.EntityAnimationError(f"NONZERO_NATIVE_DIAGNOSTICS:{asset}")
    if len(receipt.get("screenshots", [])) != len(EQUIPMENT_SPECS[asset]["clips"]):
        raise lane.EntityAnimationError(f"SCREENSHOT_COVERAGE_MISMATCH:{asset}")
    receipt_path = output / lane.RECEIPT_NAME
    receipt_path.write_bytes(native.canonical_json_bytes(receipt))
    receipt["receipt_sha256"] = native.sha256_file(receipt_path)
    return receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--asset", action="append", choices=sorted(EQUIPMENT_SPECS))
    result.add_argument("--all", action="store_true")
    result.add_argument("--packet-root", type=Path, default=DEFAULT_PACKET_ROOT)
    result.add_argument("--output-root", type=Path, required=True)
    result.add_argument("--cdp-endpoint", default="http://127.0.0.1:9248")
    result.add_argument("--capture-timeline", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    assets = sorted(EQUIPMENT_SPECS) if args.all else list(dict.fromkeys(args.asset or []))
    if not assets:
        print("EXACT_ASSET_SELECTION_REQUIRED", file=sys.stderr)
        return 2
    args.output_root.mkdir(parents=True, exist_ok=True)
    receipts = []
    try:
        for asset in assets:
            receipts.append(execute_asset(
                asset,
                args.packet_root.resolve(),
                args.output_root.resolve(),
                args.cdp_endpoint,
                args.capture_timeline,
            ))
    except (lane.EntityAnimationError, native.NativeToolError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "PASS",
        "assets": [receipt["asset"] for receipt in receipts],
        "receipts": {receipt["asset"]: receipt["receipt_sha256"] for receipt in receipts},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
