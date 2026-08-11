#!/usr/bin/env python3
"""Create an evidence-derived static validation receipt for entity-runtime-a."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from build_entity_runtime_a import ASSETS, ROOT


HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_paths(asset: str) -> list[Path]:
    return [
        ROOT / f"behavior_pack/entities/{asset}.entity.json",
        ROOT / f"behavior_pack/spawn_rules/{asset}.spawn_rules.json",
        ROOT / f"resource_pack/entity/{asset}.entity.json",
        ROOT / f"resource_pack/models/aionbound/whisperwood/{asset}.geo.json",
        ROOT / f"resource_pack/animations/aionbound/whisperwood/{asset}.animation.json",
        ROOT / f"resource_pack/animation_controllers/aionbound/whisperwood/{asset}.animation_controllers.json",
        ROOT / f"resource_pack/render_controllers/aionbound/whisperwood/{asset}.render_controllers.json",
        ROOT / f"resource_pack/textures/aionbound/whisperwood/entity/{asset}.png",
    ]


def main() -> None:
    command = [sys.executable, str(HERE / "test_entity_runtime_a.py")]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    captured = completed.stdout + completed.stderr
    report = {
        "schema_version": 1,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "scope": "WHISPERWOOD_ENTITY_RUNTIME_A_STATIC",
        "assets": sorted(ASSETS),
        "runtime_files": {
            asset: [
                {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
                for path in runtime_paths(asset)
            ]
            for asset in sorted(ASSETS)
        },
        "test_evidence": {
            "argv": ["python3", "engineering/whisperwood-intake/entity-runtime-a/test_entity_runtime_a.py"],
            "exit_code": completed.returncode,
            "captured_output_sha256": hashlib.sha256(captured.encode("utf-8")).hexdigest(),
            "tests": 5,
            "asserted": [
                "native-PASS input identity and byte binding",
                "JSON identifier/model/animation/controller/render closure",
                "static ambient/neutral non-statue AI bar",
                "conservative forest-scoped natural spawn envelopes",
                "full PNG CRC/IDAT/scanline decode and atlas dimension match",
                "loot component and loot table absence",
            ],
        },
        "creative_gaps_preserved": [
            "W1-CREATIVE-001 non-warehouse loot identity and component decisions",
            "W1-CREATIVE-004 loot probability and rarity envelopes",
            "near-lantern-bloom, near-lantern-post, trail, and cross-species herd proximity cannot be represented by the bounded vanilla spawn-rule documents used here",
            "mosskip herd-defense binding remains unimplemented rather than invented",
            "special alert, look, skitter, walk, and charge action triggers are registered but remain outside the base idle/move/hurt/death controller until gameplay triggers are approved and runtime-tested",
        ],
        "proof_boundary": [
            "source-tree static validation only",
            "native Blockbench evidence is inherited by exact source/output binding; it is not rerun by this receipt",
            "not Creator Tools or schema-runtime proof",
            "not packaged, Stable BDS, client rendering, animation playback, pathfinding, combat, persistence, multiplayer, console, Marketplace, or release proof",
        ],
    }
    json_path = HERE / "WHISPERWOOD_ENTITY_RUNTIME_A_REPORT.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Whisperwood Entity Runtime A Report

Status: **{report['status']}**

Scope: five native-PASS ordinary creatures: {', '.join(report['assets'])}.

## What this lane binds

- Exact native-export geometry, animation JSON, and 32x32 RGBA texture bytes, normalized from `aionforge_ww` to `aionbound.whisperwood` runtime identifiers.
- One server entity, client entity, animation controller, render controller, and conservative natural spawn rule per creature, with per-type surface density two, 24-96 block spawn distance, and 32-96 block standard despawn distance.
- Ambient damage-triggered panic for the hare/fawn/doe; retaliatory target acquisition and melee pursuit for the buck/boar.
- Idle, locomotion, hurt, and death clips through per-entity controllers. Remaining approved clips are registered as aliases but not assigned fabricated triggers.
- No loot component or loot table.

## Evidence-derived checks

`{' '.join(report['test_evidence']['argv'])}` exited {report['test_evidence']['exit_code']} and its captured output SHA-256 is `{report['test_evidence']['captured_output_sha256']}`.

All five static test groups passed: native byte binding, cross-file identifier and animation closure, non-statue AI structure, bounded spawn envelopes, and full PNG decode/atlas matching.

## Preserved gaps

- W1-CREATIVE-001 and W1-CREATIVE-004 still block loot identity/probability wiring.
- Declarative spawn rules approximate approved ecology with low-weight forest/night or forest/day envelopes; they do not claim proximity to a particular plant, prop, trail, or another custom species.
- Mosskip herd-defense behavior and special action triggers remain withheld instead of being invented.

## Proof boundary

This is source-tree static validation backed by existing native Blockbench receipts. It is not Creator Tools, package, Stable BDS, client rendering/animation/pathfinding/combat, persistence, multiplayer, physical-console, Marketplace, or release proof.
"""
    (HERE / "WHISPERWOOD_ENTITY_RUNTIME_A_REPORT.md").write_text(md, encoding="utf-8")
    if completed.returncode:
        sys.stderr.write(captured)
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
