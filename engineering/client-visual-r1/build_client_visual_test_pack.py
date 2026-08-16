#!/usr/bin/env python3
"""Build the bounded G8 client-visual R1 test package.

This is deliberately an overlay compiler.  It leaves the Wave 1 source packs
unchanged, stages complete successor packs, and emits deterministic archives.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
LANE = ROOT / "engineering/client-visual-r1"
VERSION = [1, 3, 2]
FIXED_TIME = (1980, 1, 1, 0, 0, 0)

BASE_HASHES = {
    "resource_pack/attachables/trophy_edge.attachable.json": "44291a5651169ae5def8958d0cf761c51f1896744f2cd0b2f0c9cb7c7205f085",
    "resource_pack/models/aionbound/trophy_edge_assembled.geo.json": "befe5dc94885526ed554643cb1856385d99b6da85b87d57264d03479281e0cdb",
    "resource_pack/models/aionbound/ashen/entities/char_wolf.geo.json": "30073a3ab274f4e30d0ecf083015c47fe763b7e842dce2c5c53b565e124387bb",
    "resource_pack/textures/aionbound/trophy_edge.png": "9eb1aa75187b19b70a5102bcc83a0f105c7430acc56ca9c8ea327f14268b3cfd",
    "engineering/native-assets/ashen/creatures/evidence/char_wolf/native-exports/pass-2.geo.json": "30073a3ab274f4e30d0ecf083015c47fe763b7e842dce2c5c53b565e124387bb",
    "engineering/native-assets/ashen/creatures/evidence/char_wolf/ashen-creature-native-receipt.json": "3bd1f78352b8d714a9fe67f128102086d041f22c3233e418dcd015d6fe56c470",
    "engineering/client-visual-r1/assets/trophy_edge.png": "ae67ffc31d6b18f0d4fb2e618bdbf26b8e79240e1e107ecb32ae56b95eaf653e",
    "engineering/client-visual-r1/sources/trophy_edge_imagegen_master.png": "0b60ad4a260acceefd232b296de5293a8a1baf15faeec542b011c60835b5b3ca",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_base_hashes() -> None:
    for relative, expected in BASE_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing authority input: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"authority drift for {relative}: {actual} != {expected}")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def patch_manifest(path: Path, peer_uuid: str) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["header"]["version"] = VERSION
    manifest["header"]["name"] += " (Client Visual R1)"
    manifest["header"]["description"] = (
        "Aionbound Wave 1 G8 bounded client-visual test: Trophy Edge and one entity-path A/B probe"
    )
    for module in manifest["modules"]:
        module["version"] = VERSION
    for dependency in manifest.get("dependencies", []):
        if dependency.get("uuid") == peer_uuid:
            dependency["version"] = VERSION
    write_json(path, manifest)


def trophy_attachable() -> dict:
    return {
        "format_version": "1.20.30",
        "minecraft:attachable": {
            "description": {
                "identifier": "aionbound:trophy_edge",
                "item": {
                    "aionbound:trophy_edge": "query.is_owner_identifier_any('minecraft:player')"
                },
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": "textures/aionbound/trophy_edge_assembled"},
                "geometry": {"default": "geometry.aionbound.trophy_edge_assembled"},
                "animations": {
                    "hold_first_person": "animation.steve_head.hold_first_person",
                    "hold_third_person": "animation.steve_head.hold_third_person",
                },
                "scripts": {
                    "animate": [
                        {"hold_first_person": "context.is_first_person == 1.0"},
                        {"hold_third_person": "context.is_first_person == 0.0"},
                    ]
                },
                "render_controllers": ["controller.render.item_default"],
            }
        },
    }


def normalize_trophy_geometry(source: Path) -> dict:
    document = json.loads(source.read_text(encoding="utf-8"))
    geometry = document["minecraft:geometry"][0]
    roots = [bone for bone in geometry["bones"] if "parent" not in bone]
    if len(roots) != 1 or roots[0].get("name") != "root":
        raise RuntimeError("Trophy Edge requires one root bone named root")
    root = roots[0]
    root["binding"] = "q.item_slot_to_bone_name(context.item_slot)"
    root["pivot"] = [0, 5, -6]
    root["rotation"] = [125, 0, 0]

    converted = 0
    for bone in geometry["bones"]:
        for cube in bone.get("cubes", []):
            faces = cube.get("uv")
            if not isinstance(faces, dict):
                continue
            for face in faces.values():
                legacy = face.get("uv") if isinstance(face, dict) else None
                if isinstance(legacy, list) and len(legacy) == 4 and "uv_size" not in face:
                    face["uv"] = legacy[:2]
                    # The legacy payload stores two corners, not origin+size.
                    face["uv_size"] = [legacy[2] - legacy[0], legacy[3] - legacy[1]]
                    converted += 1
    if converted != 168:
        raise RuntimeError(f"expected 168 Trophy Edge UV conversions, got {converted}")
    return document


def stage(output: Path) -> tuple[Path, Path]:
    require_base_hashes()
    stage_root = output / "staging"
    if stage_root.exists():
        shutil.rmtree(stage_root)
    bp = stage_root / "behavior_pack"
    rp = stage_root / "resource_pack"
    shutil.copytree(ROOT / "behavior_pack", bp)
    shutil.copytree(ROOT / "resource_pack", rp)

    patch_manifest(bp / "manifest.json", "3b13350a-2634-5083-948e-29f3fef39a45")
    patch_manifest(rp / "manifest.json", "2cf5e36d-e80f-5a00-9d46-adefbac35524")

    write_json(rp / "attachables/trophy_edge.attachable.json", trophy_attachable())

    old_trophy = rp / "models/aionbound/trophy_edge_assembled.geo.json"
    new_trophy = rp / "models/entity/aionbound/trophy_edge_assembled.geo.json"
    write_json(new_trophy, normalize_trophy_geometry(old_trophy))
    old_trophy.unlink()

    # A/B probe: only Char Wolf moves to the previously PS4-proven discovery
    # root. Cinder Lynx remains byte-identical under the old path as control.
    old_representative = rp / "models/aionbound/ashen/entities/char_wolf.geo.json"
    new_representative = rp / "models/entity/aionbound/ashen/char_wolf.geo.json"
    new_representative.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(old_representative, new_representative)
    old_representative.unlink()

    shutil.copyfile(LANE / "assets/trophy_edge.png", rp / "textures/aionbound/trophy_edge.png")
    return bp, rp


def zip_tree(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            relative = str(PurePosixPath(path.relative_to(source)))
            info = zipfile.ZipInfo(relative, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def zip_addon(bp_pack: Path, rp_pack: Path, target: Path) -> None:
    members = [(bp_pack.name, bp_pack.read_bytes()), (rp_pack.name, rp_pack.read_bytes())]
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in members:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(output: Path) -> dict:
    bp, rp = stage(output)
    bp_pack = output / "aionbound-wave1-g8-client-visual-r1-behavior.mcpack"
    rp_pack = output / "aionbound-wave1-g8-client-visual-r1-resources.mcpack"
    addon = output / "aionbound-wave1-g8-client-visual-r1.mcaddon"
    zip_tree(bp, bp_pack)
    zip_tree(rp, rp_pack)
    zip_addon(bp_pack, rp_pack, addon)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    receipt = {
        "schema": "aionbound.client-visual-test-pack.v1",
        "status": "CLIENT_VISUAL_TEST_PACKAGE_BUILT_PS4_RESULT_PENDING",
        "source_commit": commit,
        "pack_version": VERSION,
        "changes": {
            "trophy_edge": [
                "explicit item mapping",
                "standard item render controller",
                "conditional first-person and third-person holder animations",
                "item-slot root binding with bounded G6-overlay pivot and rotation hypothesis",
                "168 legacy face UV arrays normalized to uv plus uv_size",
                "isolated transparent 64x64 inventory sprite",
            ],
            "entity_ab_probe": {
                "corrected": "aionbound:char_wolf geometry moved to models/entity/aionbound/ashen",
                "control": "aionbound:cinder_lynx remains under models/aionbound/ashen/entities",
                "geometry_bytes_changed": False,
                "negative_uv_sizes_preserved": True,
            },
        },
        "artifacts": {
            path.name: {"sha256": sha256(path), "size": path.stat().st_size}
            for path in (bp_pack, rp_pack, addon)
        },
        "proof_boundary": {
            "proven": ["deterministic package construction", "static client-resource contracts"],
            "pending": ["physical PS4 rendering", "Trophy Edge socket placement", "representative visibility A/B"],
            "not_claimed": ["BDS rendering proof", "remaining mob repair", "candidate", "release"],
            "live_deployment_modified": False,
        },
    }
    write_json(output / "CLIENT_VISUAL_TEST_PACK_RECEIPT.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "output/g8-client-visual-r1")
    args = parser.parse_args()
    receipt = build(args.output.resolve())
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
