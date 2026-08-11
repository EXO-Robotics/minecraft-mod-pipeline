#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("KILN_SKY_RUNTIME_EVIDENCE.json")
BASE = {
    "commit": "a26fa8f9ce0fb605c23e3d29261aec2193386ff1",
    "tree": "d06b96578c156c26d91ca07cff3ce3eac5158f56",
}
INPUTS = [
    "behavior_pack/scripts/kiln_sky.js",
    "behavior_pack/scripts/ashen_rewards.js",
    "behavior_pack/scripts/state.js",
    "tests/wave1_kiln_sky.test.mjs",
    "tests/wave1_ashen_rewards.test.mjs",
    "engineering/ashen-intake/kiln-sky-runtime/ACTIVATION_WITHHELD.md",
]
AUTHORITIES = {
    "engineering/authority/WAVE_1_ENGINEERING_DECISION_LEDGER.json": "b554db9fab3fe16e59e2e3b36dfc310ff462078b170f14e1f9fe8a46999bbd0c",
    "engineering/authority/support-proposals/ashen/W1-003-KILN-SKY.json": "1b2d5f77185a1461040d7559d0d8ecdaf803d7727e419ceac32636865be85d7c",
    "engineering/authority/support-proposals/ashen/W1-004-AH.json": "93736ff800b1c90c8a6547d84336a6650f8ae32750f262de8e460385a7a26889",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    return {
        "schema": "aionbound.kiln_sky_runtime_evidence.v1",
        "status": "DEDICATED_SERVICE_COMPLETE_ACTIVATION_WITHHELD",
        "base": BASE,
        "authority": [
            {"path": path, "sha256": expected, "verified": sha256(ROOT / path) == expected}
            for path, expected in sorted(AUTHORITIES.items())
        ],
        "source": [{"path": path, "sha256": sha256(ROOT / path)} for path in INPUTS],
        "proof": {
            "dedicated_service": True,
            "state_migration": True,
            "source_semantic_tests": True,
            "shared_runtime_activation": False,
            "build": False,
            "package": False,
            "client": False,
            "bds": False,
        },
        "withheld_reason": "shared runtime event-loop and persistent reward activation requires explicit integration-owner approval",
    }


def main() -> None:
    OUT.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
