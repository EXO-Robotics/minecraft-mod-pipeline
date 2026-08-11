#!/usr/bin/env python3
"""Fail-closed verifier for Whisperwood equipment native lane A evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
PACKET = Path(
    "/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-pack-production-v1/"
    "studio-prep/sprints/asset-sprint-006-equipment-progression"
)
RECEIPT_NAME = "equipment-a-native-receipt.json"
EXPECTED = {
    "mossfang_spear": ["idle_hold", "thrust_pose", "sweep_pose"],
    "widow_fang_dagger": ["idle_hold", "stab_pose"],
    "thorn_whip": ["idle_coil", "crack_pose", "extend_pose"],
    "briar_cleaver": ["idle_hold", "chop_pose"],
    "moon_sap_staff": ["idle_hold", "cast_raise", "pulse"],
    "root_knife": ["hold"],
    "whisperwood_hatchet": ["hold", "chop"],
    "lantern_hook": ["hold", "hang"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    print(f"FAIL:{message}", file=sys.stderr)
    raise SystemExit(1)


def assert_record(root: Path, record: dict, label: str) -> Path:
    path = root / record["path"]
    if not path.is_file():
        fail(f"MISSING_FILE:{label}:{path}")
    if sha256(path) != record["sha256"]:
        fail(f"HASH_MISMATCH:{label}:{path}")
    return path


def packet_paths(asset: str) -> dict[str, Path]:
    return {
        "bbmodel": PACKET / "assets/editable" / f"{asset}.bbmodel",
        "texture": PACKET / "assets/editable" / f"{asset}.png",
        "geometry": PACKET / "assets/export/models" / f"{asset}.geo.json",
        "animation": PACKET / "assets/export/animations" / f"{asset}.animation.json",
        "brief": PACKET / "assets/briefs" / f"{asset}.json",
    }


def locator_from_geometry(path: Path) -> tuple[str, list]:
    value = json.loads(path.read_text())
    found = []
    for bone in value["minecraft:geometry"][0]["bones"]:
        if "effect" in bone.get("locators", {}):
            found.append((bone["name"], bone["locators"]["effect"]))
    if len(found) != 1:
        fail(f"LOCATOR_CARDINALITY:{path}:{len(found)}")
    return found[0]


def main() -> None:
    if not EVIDENCE.is_dir():
        fail("EVIDENCE_DIRECTORY_MISSING")
    actual_assets = {path.name for path in EVIDENCE.iterdir() if path.is_dir()}
    if actual_assets != set(EXPECTED):
        fail(f"ASSET_SET_DRIFT:{sorted(actual_assets)}")

    total_screenshots = 0
    for asset in sorted(EXPECTED):
        root = EVIDENCE / asset
        receipt_path = root / RECEIPT_NAME
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("status") != "PASS" or receipt.get("diagnostics") != []:
            fail(f"RECEIPT_NOT_CLEAN:{asset}")
        native_result = receipt["native_result"]
        if native_result.get("blockbench_version") != "5.1.6":
            fail(f"BLOCKBENCH_VERSION_DRIFT:{asset}")
        if native_result.get("warning_count") != 0 or native_result.get("error_count") != 0:
            fail(f"NONZERO_NATIVE_DIAGNOSTICS:{asset}")
        if native_result.get("locator_names") != ["effect"]:
            fail(f"NATIVE_LOCATOR_SET_DRIFT:{asset}")

        expected_names = [f"animation.aionbound.{asset}.{leaf}" for leaf in EXPECTED[asset]]
        if receipt["native_clip_names"] != expected_names:
            fail(f"NATIVE_CLIP_SET_DRIFT:{asset}")
        if sorted(native_result["final_animation_names"]) != sorted(expected_names):
            fail(f"FINAL_NATIVE_CLIP_SET_DRIFT:{asset}")
        if receipt["namespace_normalization"]["shipping_geometry_identifier"] != f"geometry.aionbound.{asset}":
            fail(f"SHIPPING_NAMESPACE_DRIFT:{asset}")

        canonical_records = receipt["warehouse_canonical_inputs"]
        for label, packet_path in packet_paths(asset).items():
            evidence_path = assert_record(root, canonical_records[label], f"canonical:{asset}:{label}")
            if sha256(evidence_path) != sha256(packet_path):
                fail(f"CANONICAL_PACKET_DRIFT:{asset}:{label}")

        texture = packet_paths(asset)["texture"]
        png = texture.read_bytes()
        if png[:8] != b"\x89PNG\r\n\x1a\n" or int.from_bytes(png[16:20], "big") != 32 or int.from_bytes(png[20:24], "big") != 32:
            fail(f"TEXTURE_CONTRACT_DRIFT:{asset}")
        preservation = receipt["texture_preservation"]
        if not preservation.get("byte_identical") or preservation.get("dimensions") != [32, 32]:
            fail(f"TEXTURE_PRESERVATION_NOT_PROVEN:{asset}")
        staged_texture = assert_record(root, receipt["staged_texture"], f"staged-texture:{asset}")
        if sha256(staged_texture) != sha256(texture):
            fail(f"STAGED_TEXTURE_BYTES_CHANGED:{asset}")

        project = assert_record(root, receipt["staged_project"], f"native-project:{asset}")
        project_json = json.loads(project.read_text())
        if project_json.get("model_identifier") != f"aionbound.{asset}":
            fail(f"PROJECT_NAMESPACE_DRIFT:{asset}")
        textures = project_json.get("textures", [])
        if len(textures) != 1 or textures[0].get("relative_path") != f"textures/{asset}.png":
            fail(f"PROJECT_TEXTURE_PATH_NOT_PORTABLE:{asset}")
        if textures[0].get("width") != 32 or textures[0].get("height") != 32:
            fail(f"PROJECT_TEXTURE_DIMENSION_DRIFT:{asset}")

        canonical_parent, canonical_transform = locator_from_geometry(packet_paths(asset)["geometry"])
        if canonical_parent != "chassis":
            fail(f"CANONICAL_LOCATOR_PARENT_DRIFT:{asset}")
        plan = receipt["locator_repair_plan"]["effect"]
        if plan["parent"] != "chassis" or plan["position"] != canonical_transform:
            fail(f"LOCATOR_REPAIR_PLAN_DRIFT:{asset}")
        pass2_geometry = assert_record(root, receipt["exports"]["geometry"]["pass_2"], f"pass2-geometry:{asset}")
        native_parent, native_transform = locator_from_geometry(pass2_geometry)
        if (native_parent, native_transform) != (canonical_parent, canonical_transform):
            fail(f"NATIVE_LOCATOR_EXPORT_DRIFT:{asset}")

        for export_class in ("geometry", "animations"):
            export = receipt["exports"][export_class]
            if not export.get("canonical_equivalent"):
                fail(f"TWO_PASS_NOT_EQUIVALENT:{asset}:{export_class}")
            first = assert_record(root, export["pass_1"], f"pass1-{export_class}:{asset}")
            second = assert_record(root, export["pass_2"], f"pass2-{export_class}:{asset}")
            if export["pass_1"]["canonical_sha256"] != export["pass_2"]["canonical_sha256"]:
                fail(f"TWO_PASS_CANONICAL_HASH_DRIFT:{asset}:{export_class}")
            if not first.stat().st_size or not second.stat().st_size:
                fail(f"EMPTY_NATIVE_EXPORT:{asset}:{export_class}")

        signatures = receipt["geometry_signatures_excluding_intended_locators"]
        if len(set(signatures.values())) != 1:
            fail(f"SHAPE_SIGNATURE_DRIFT:{asset}")

        screenshots = receipt.get("screenshots", [])
        if [entry["clip"] for entry in screenshots] != EXPECTED[asset]:
            fail(f"TIMELINE_CLIP_COVERAGE_DRIFT:{asset}")
        for screenshot in screenshots:
            path = assert_record(root, screenshot, f"timeline:{asset}:{screenshot['clip']}")
            if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                fail(f"TIMELINE_NOT_PNG:{asset}:{screenshot['clip']}")
        total_screenshots += len(screenshots)

    if total_screenshots != 18:
        fail(f"TIMELINE_TOTAL_DRIFT:{total_screenshots}")

    print("PASS: exact eight-asset native lane")
    print("PASS: Blockbench 5.1.6, zero warnings/errors for all assets")
    print("PASS: 18 exact brief clips and 18 per-clip timeline PNGs")
    print("PASS: true effect locator on chassis from canonical export authority")
    print("PASS: two native save-close-reopen export passes are canonically equivalent")
    print("PASS: geometry signatures unchanged outside intended locator repair")
    print("PASS: exact approved 32x32 packet texture bytes preserved; no upscale")
    print("PASS: geometry/animation namespace normalized to aionbound with portable texture refs")


if __name__ == "__main__":
    main()
