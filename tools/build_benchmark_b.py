#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from mccompiler.operations import generation_ops, validation_ops
from mccompiler.project.store import ProjectStore


ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCTION = ROOT / "benchmarks/rights-cleared-java-mod/reconstruction"

LEGACY_SEED_SCRIPT = """import { system, world } from '@minecraft/server';
const LEGACY_STATE_KEY = 'mccompiler:doorlock:locks:v0';
const SEED_KEY = 'mccompiler:doorlock:legacy-seed';
const BOOT_KEY = 'mccompiler:doorlock:diagnostic_boot';
system.run(() => {
  if (world.getDynamicProperty(SEED_KEY) !== 'seeded') {
    world.setDynamicProperty(LEGACY_STATE_KEY, JSON.stringify(['10,64,10_deadbeef']));
    world.setDynamicProperty(SEED_KEY, 'seeded');
  }
  const current = (Number(world.getDynamicProperty(BOOT_KEY)) || 0) + 1;
  world.setDynamicProperty(BOOT_KEY, current);
  console.warn('[mccompiler:doorlock] legacy_seed=1');
  console.warn(`[mccompiler:doorlock] persistent_boot=${current}`);
});
"""


def build_legacy_seed_world(current_world: Path, destination: Path) -> dict[str, Any]:
    files: dict[str, bytes] = {}
    replaced = 0
    with zipfile.ZipFile(current_world) as source:
        for member in source.infolist():
            if member.is_dir():
                continue
            data = source.read(member)
            if member.filename.endswith("/scripts/custom/doorlock.js"):
                data = LEGACY_SEED_SCRIPT.encode("utf-8")
                replaced += 1
            files[member.filename] = data
    if replaced != 1:
        raise RuntimeError(f"Expected one DoorLock script in generated world, replaced {replaced}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w") as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    payload = destination.read_bytes()
    return {"path": destination.as_posix(), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def build(output: Path) -> dict[str, Any]:
    store = ProjectStore.create(output, name="DoorLock technical reconstruction")
    store.write("analysis/modir.json", json.loads((RECONSTRUCTION / "modir-seed.json").read_text(encoding="utf-8")))
    store.write("rights/rights-manifest.yaml", json.loads((RECONSTRUCTION / "rights-manifest.json").read_text(encoding="utf-8")))
    store.write("reports/fidelity.json", json.loads((RECONSTRUCTION / "quality-records.json").read_text(encoding="utf-8")))
    store.write("decisions/custom-handlers.json", json.loads((RECONSTRUCTION / "custom-handler.json").read_text(encoding="utf-8")))
    for name in ("doorlock-state.js", "doorlock.js"):
        custom = store.resolve(f"custom/scripts/{name}")
        custom.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RECONSTRUCTION / f"custom/scripts/{name}", custom)

    generation_ops.generate_pack(store, {}, store.revision)
    static, _, _ = validation_ops.validate_static(store, {"marketplace": True})
    scripts, _, _ = validation_ops.validate_scripts(store, {})
    assets, _, _ = validation_ops.validate_assets(store, {})
    api, _, _ = validation_ops.validate_api_symbols(store, {})
    performance, _, _ = validation_ops.validate_performance(store, {})
    if not all((static["valid"], scripts["valid"], assets["valid"], api["valid"], performance["passed"])):
        raise RuntimeError(json.dumps({"static": static, "scripts": scripts, "assets": assets, "api": api, "performance": performance}, sort_keys=True))
    world, _, _ = generation_ops.generate_world(store, {"world_name": "DoorLock Technical Validation"}, store.revision)
    current_world = store.resolve(world["world"]["path"])
    legacy_world = store.resolve("dist/test-world/legacy-seed-world.mcworld")
    legacy = build_legacy_seed_world(current_world, legacy_world)
    package, _, _ = generation_ops.package_mcaddon(store, {}, store.revision)
    candidate, _, _ = validation_ops.evaluate_marketplace_candidate(store, {}, store.revision)
    return {
        "project": str(store.root),
        "revision": store.revision,
        "mcaddon": package["archive"],
        "mcworld": world["world"],
        "legacy_seed_mcworld": legacy,
        "validation": {"static": True, "scripts": True, "assets": True, "api": True, "performance": True},
        "marketplace_candidate": candidate["candidate"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the clean-room Benchmark B technical reconstruction")
    parser.add_argument("--output", type=Path, required=True, help="New conversion-project directory")
    args = parser.parse_args()
    result = build(args.output.expanduser().resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
