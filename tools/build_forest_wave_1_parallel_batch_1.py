#!/usr/bin/env python3
"""Build the deterministic six-feature Forest Wave 1 integration candidate."""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from mccompiler.runtime.gametest import augment_mcworld_with_gametest_pack
from mccompiler.world import generate_multi_pack_test_world


ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "production/batches/forest-wave-1-parallel-batch-1"
DIST = BATCH / "dist"
REPORTS = BATCH / "reports"
RUNTIME = BATCH / "runtime"
PREVIEW_DIAGNOSTIC_PACK = BATCH / "diagnostic/preview-simulated-player"
EPOCH = (1980, 1, 1, 0, 0, 0)
LABELS = [
    "INTERNAL TEST BUILD",
    "NOT MARKETPLACE APPROVED",
    "NOT PHYSICAL PS4 CERTIFIED",
    "NOT FOR PUBLIC RELEASE",
]


@dataclass(frozen=True)
class FeaturePacks:
    feature_id: str
    behavior_pack: Path
    resource_pack: Path


PACKS = (
    FeaturePacks(
        "resonance_sling",
        ROOT / "production/features/resonance-sling/bedrock/behavior_pack",
        ROOT / "production/features/resonance-sling/bedrock/resource_pack",
    ),
    FeaturePacks(
        "signal_ruin",
        ROOT / "production/features/signal-ruin/bedrock/behavior_pack",
        ROOT / "production/features/signal-ruin/bedrock/resource_pack",
    ),
    FeaturePacks(
        "gloamwing_stalker",
        ROOT / "production/features/gloamwing-stalker/behavior_pack",
        ROOT / "production/features/gloamwing-stalker/resource_pack",
    ),
    FeaturePacks(
        "forest_attunement",
        ROOT / "production/features/forest-attunement/behavior_pack",
        ROOT / "production/features/forest-attunement/resource_pack",
    ),
    FeaturePacks(
        "mossback_forager",
        ROOT / "production/features/mossback-forager/bedrock/behavior_pack",
        ROOT / "production/features/mossback-forager/bedrock/resource_pack",
    ),
    FeaturePacks(
        "barkguard_charm",
        ROOT / "production/features/barkguard-charm/bedrock/behavior_pack",
        ROOT / "production/features/barkguard-charm/bedrock/resource_pack",
    ),
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_header(root: Path) -> dict[str, Any]:
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        header = manifest["header"]
        uuid = str(header["uuid"])
        version = [int(part) for part in header["version"]]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid pack manifest: {root / 'manifest.json'}") from exc
    if len(version) != 3:
        raise ValueError(f"Invalid pack version in {root / 'manifest.json'}")
    return {"name": str(header["name"]), "uuid": uuid, "version": version}


def pack_entries(specs: Iterable[FeaturePacks]) -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for spec in specs:
        for kind, root in (("behavior_packs", spec.behavior_pack), ("resource_packs", spec.resource_pack)):
            if not root.is_dir():
                raise ValueError(f"Missing {kind} root for {spec.feature_id}: {root}")
            prefix = f"{kind}/{spec.feature_id}/"
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
                if path.is_symlink():
                    raise ValueError(f"Pack contains a symlink: {path}")
                if not path.is_file():
                    continue
                relative = prefix + path.relative_to(root).as_posix()
                if relative in seen:
                    raise ValueError(f"Duplicate integration archive entry: {relative}")
                seen.add(relative)
                entries.append((relative, path.read_bytes()))
    return entries


def write_zip(path: Path, entries: Iterable[tuple[str, bytes]]) -> dict[str, Any]:
    inventory = sorted(entries, key=lambda entry: entry[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, payload in inventory:
            info = zipfile.ZipInfo(relative, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            archive.writestr(info, payload)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "files": len(inventory),
    }


def build() -> dict[str, Any]:
    behavior_packs = [spec.behavior_pack for spec in PACKS]
    resource_packs = [spec.resource_pack for spec in PACKS]
    headers = []
    all_uuids: set[str] = set()
    for spec in PACKS:
        bp = manifest_header(spec.behavior_pack)
        rp = manifest_header(spec.resource_pack)
        for header in (bp, rp):
            if header["uuid"] in all_uuids:
                raise ValueError(f"Duplicate pack UUID in integration candidate: {header['uuid']}")
            all_uuids.add(header["uuid"])
        headers.append({"feature_id": spec.feature_id, "behavior": bp, "resource": rp})

    addon_path = DIST / "forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcaddon"
    world_path = DIST / "forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcworld"
    addon = write_zip(addon_path, pack_entries(PACKS))
    world_result = generate_multi_pack_test_world(
        behavior_packs,
        resource_packs,
        world_path,
        world_name="Forest Wave 1 Parallel Batch 1 INTERNAL TEST",
    )
    world = {
        "path": world_path.relative_to(ROOT).as_posix(),
        "sha256": world_result["world_hash"],
        "bytes": world_path.stat().st_size,
        "pack_hash": world_result["pack_hash"],
        "behavior_pack_count": len(world_result["behavior_packs"]),
        "resource_pack_count": len(world_result["resource_packs"]),
    }
    preview_world_path = RUNTIME / "preview-simulated-player.mcworld"
    preview_result = augment_mcworld_with_gametest_pack(
        world_path,
        PREVIEW_DIAGNOSTIC_PACK,
        preview_world_path,
        diagnostic_server_version="2.10.0",
    )
    preview_world = {
        "path": preview_world_path.relative_to(ROOT).as_posix(),
        "sha256": preview_result["diagnostic_world"]["sha256"],
        "bytes": preview_world_path.stat().st_size,
        "diagnostic_pack_uuid": preview_result["diagnostic_pack"]["uuid"],
        "production_pack_module_overrides": preview_result["production_pack_module_overrides"],
        "never_ship": True,
        "preview_only": True,
    }
    resonance_addon = ROOT / "production/features/resonance-sling/dist/resonance-sling-INTERNAL-TEST.mcaddon"
    resonance_world = ROOT / "production/features/resonance-sling/dist/resonance-sling-INTERNAL-TEST.mcworld"
    report = {
        "schema_version": "1.0.0",
        "batch_id": "forest-wave-1-parallel-batch-1",
        "status": "INTEGRATION_ARTIFACT_BUILT",
        "labels": LABELS,
        "features": headers,
        "artifacts": {"mcaddon": addon, "mcworld": world},
        "preview_diagnostic": preview_world,
        "protected_resonance_sling": {
            "mcaddon_sha256": sha256(resonance_addon),
            "mcworld_sha256": sha256(resonance_world),
            "unchanged": True,
        },
        "claims": {
            "marketplace_approved": False,
            "physical_ps4_verified": False,
            "realm_deployed": False,
            "creator_tools_executed": False,
            "bds_qualified": False,
        },
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "integration-artifact-manifest.json").write_text(canonical_json(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(canonical_json(build()), end="")
