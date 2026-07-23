#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from mccompiler.operations.registry import OperationRegistry
from mccompiler.project.store import ProjectStore


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/original-marketplace-showcase/fixture"
OVERRIDES = ROOT / "benchmarks/original-marketplace-showcase/runtime-overrides.json"


def build(output: Path) -> dict[str, Any]:
    registry = OperationRegistry()

    def call(operation: str, parameters: dict[str, Any] | None = None, *, mutate: bool = False) -> dict[str, Any]:
        request: dict[str, Any] = {
            "schema_version": "1.0.0",
            "request_id": f"benchmark-a-{operation}",
            "operation": operation,
            "project": str(output),
            "parameters": parameters or {},
        }
        if mutate and output.exists():
            request["expected_revision"] = ProjectStore.open(output).revision
        response = registry.execute(request)
        if not response["ok"]:
            raise RuntimeError(json.dumps(response, sort_keys=True))
        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError(f"{operation} returned no structured result")
        return result

    call("create_conversion_project", {
        "name": "Clockwork Gardens",
        "target_profile": "MARKETPLACE_ADDON_STABLE",
    })
    scan = call("scan_mod", {"input": str(FIXTURE)}, mutate=True)
    override_document = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    for override in override_document["overrides"]:
        call("apply_override", {"override": override}, mutate=True)
    call("generate_pack", mutate=True)
    validation: dict[str, bool] = {}
    for operation, key in (
        ("validate_static", "valid"),
        ("validate_scripts", "valid"),
        ("validate_assets", "valid"),
        ("validate_api_symbols", "valid"),
        ("validate_performance", "passed"),
    ):
        result = call(operation, {"marketplace": True} if operation == "validate_static" else {})
        validation[operation] = bool(result.get(key))
    if not all(validation.values()):
        raise RuntimeError(json.dumps(validation, sort_keys=True))
    world = call("generate_world", {"world_name": "Clockwork Gardens Validation"}, mutate=True)
    package = call("package_mcaddon", mutate=True)
    candidate = call("evaluate_marketplace_candidate", mutate=True)
    return {
        "schema_version": "1.0.0",
        "project": str(output),
        "revision": ProjectStore.open(output).revision,
        "content_count": scan["content_count"],
        "behavior_count": scan["behavior_count"],
        "mcaddon": package["archive"],
        "mcworld": world["world"],
        "validation": validation,
        "marketplace_candidate": candidate["candidate"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the original Benchmark A showcase project")
    parser.add_argument("--output", type=Path, required=True, help="New conversion-project directory")
    args = parser.parse_args()
    result = build(args.output.expanduser().resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
