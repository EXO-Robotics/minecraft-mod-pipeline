#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from mccompiler.operations import generation_ops, validation_ops
from mccompiler.project.store import ProjectStore


ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCTION = ROOT / "benchmarks/rights-cleared-java-mod/reconstruction"


def build(output: Path) -> dict[str, Any]:
    store = ProjectStore.create(output, name="DoorLock technical reconstruction")
    store.write("analysis/modir.json", json.loads((RECONSTRUCTION / "modir-seed.json").read_text(encoding="utf-8")))
    store.write("rights/rights-manifest.yaml", json.loads((RECONSTRUCTION / "rights-manifest.json").read_text(encoding="utf-8")))
    store.write("decisions/custom-handlers.json", json.loads((RECONSTRUCTION / "custom-handler.json").read_text(encoding="utf-8")))
    custom = store.resolve("custom/scripts/doorlock.js")
    custom.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(RECONSTRUCTION / "custom/scripts/doorlock.js", custom)

    generation_ops.generate_pack(store, {}, store.revision)
    static, _, _ = validation_ops.validate_static(store, {"marketplace": True})
    scripts, _, _ = validation_ops.validate_scripts(store, {})
    assets, _, _ = validation_ops.validate_assets(store, {})
    api, _, _ = validation_ops.validate_api_symbols(store, {})
    performance, _, _ = validation_ops.validate_performance(store, {})
    if not all((static["valid"], scripts["valid"], assets["valid"], api["valid"], performance["passed"])):
        raise RuntimeError(json.dumps({"static": static, "scripts": scripts, "assets": assets, "api": api, "performance": performance}, sort_keys=True))
    world, _, _ = generation_ops.generate_world(store, {"world_name": "DoorLock Technical Validation"}, store.revision)
    package, _, _ = generation_ops.package_mcaddon(store, {}, store.revision)
    candidate, _, _ = validation_ops.evaluate_marketplace_candidate(store, {}, store.revision)
    return {
        "project": str(store.root),
        "revision": store.revision,
        "mcaddon": package["archive"],
        "mcworld": world["world"],
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
