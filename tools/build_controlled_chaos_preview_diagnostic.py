#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mccompiler.runtime.gametest import augment_mcworld_with_gametest_pack


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks/controlled-chaos-integration"
SOURCE = BENCHMARK / "dist/controlled-chaos-qualification.mcworld"
PACK = BENCHMARK / "diagnostic/server-qualification"
OUTPUT = BENCHMARK / "runtime/preview-server-qualification.mcworld"
RECEIPT = BENCHMARK / "runtime/preview-server-qualification-build.json"


def build() -> dict[str, object]:
    result = augment_mcworld_with_gametest_pack(
        SOURCE,
        PACK,
        OUTPUT,
        diagnostic_server_version="2.10.0",
    )
    result["fixture_sha256"] = hashlib.sha256(
        (PACK / "scripts/main.js").read_bytes()
    ).hexdigest()
    result["probe_contract_sha256"] = hashlib.sha256(
        (PACK / "probes.json").read_bytes()
    ).hexdigest()
    RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
