#!/usr/bin/env python3
"""Validate the deterministic Packet 006 Whisperwood equipment intake map."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PROGRAM = REPO.parents[2]
BEDROCK_ROOT = PROGRAM.parent
MAP_PATH = HERE / "WHISPERWOOD_EQUIPMENT_INTAKE.json"
NORMALIZATION = REPO / "engineering/normalization/PACKET_NORMALIZATION_INVENTORY.json"
G7 = BEDROCK_ROOT / "program/aionbound-core-content-beta-production-runs/AIONBOUND_CORE_CONTENT_BETA_FEATURE_PRODUCER_G000007/repo"


EXPECTED_IDS = {
    "mossfang_spear", "widow_fang_dagger", "thorn_whip", "briar_cleaver", "moon_sap_staff",
    "whisperwood_helmet", "whisperwood_chest", "whisperwood_legs", "whisperwood_boots",
    "root_knife", "whisperwood_hatchet", "lantern_hook",
    "moss_charm", "root_bracelet", "lantern_badge", "moon_sap_pendant", "briar_ring",
    "thorn_stalker_skull", "briar_elk_trophy", "mosskip_trophy", "ancient_acorn_display",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_authority(path: str) -> Path:
    candidate = REPO / path
    if candidate.exists():
        return candidate
    return BEDROCK_ROOT / path


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    intake = json.loads(MAP_PATH.read_text())
    normalization = json.loads(NORMALIZATION.read_text())
    assets = intake["assets"]

    ids = [asset["id"] for asset in assets]
    if len(ids) != len(set(ids)):
        fail("duplicate intake IDs")
    if set(ids) != EXPECTED_IDS:
        fail(f"subset mismatch missing={sorted(EXPECTED_IDS-set(ids))} extra={sorted(set(ids)-EXPECTED_IDS)}")

    counts = Counter(asset["category"] for asset in assets)
    expected_counts = intake["scope"]["counts"]
    if dict(sorted(counts.items())) != dict(sorted(expected_counts.items())):
        fail(f"category counts mismatch {dict(counts)}")

    for authority in intake["authority"]:
        path = resolve_authority(authority["path"])
        if not path.is_file():
            fail(f"missing authority {path}")
        if sha256(path) != authority["sha256"]:
            fail(f"authority hash mismatch {path}")

    by_id = {entry["warehouse_id"]: entry for entry in normalization["assets"]}
    packet_root = BEDROCK_ROOT / intake["canonical_source_contract"]["packet_root"]
    templates = intake["canonical_source_contract"]["files_for_each_source_id"]
    for asset in assets:
        asset_id = asset["id"]
        entry = by_id.get(asset_id)
        if not entry or entry.get("packet_id") != "006":
            fail(f"missing Packet 006 normalization entry {asset_id}")
        if asset["runtime_id"] != f"aionbound:{asset_id}":
            fail(f"runtime ID drift {asset_id}")
        expected_files = {value["path"]: value["sha256"] for value in entry["canonical"].values() if value}
        for template in templates:
            relative = template.format(source_id=asset_id)
            path = packet_root / relative
            if not path.is_file():
                fail(f"missing canonical source {path}")
            normalization_key = str(path.relative_to(BEDROCK_ROOT / "program"))
            expected_hash = expected_files.get(normalization_key)
            if not expected_hash:
                fail(f"source not bound in normalization inventory {normalization_key}")
            if sha256(path) != expected_hash:
                fail(f"canonical source hash mismatch {path}")
        if entry["normalization"]["native_locator_gap"] != ["effect"]:
            fail(f"unexpected locator classification {asset_id}")
        expected_clips = set(asset["declared_clips"])
        if set(entry["normalization"]["animation_gap"]) != expected_clips:
            fail(f"declared clip gap mismatch {asset_id}")
        if entry["static"]["png"]["width"] != 32 or entry["static"]["png"]["height"] != 32:
            fail(f"unexpected packet PNG dimensions {asset_id}")

    g7_hits = []
    for asset_id in sorted(EXPECTED_IDS):
        result = subprocess.run(
            ["rg", "-l", "--fixed-strings", f"aionbound:{asset_id}", "behavior_pack", "resource_pack"],
            cwd=G7,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            fail(f"rg failed for G7 ID {asset_id}: {result.stderr.strip()}")
        if result.stdout.strip():
            g7_hits.append(asset_id)
    if g7_hits:
        fail(f"exact G7 runtime collisions {g7_hits}")

    proposed_existing = []
    for asset in assets:
        asset_id = asset["id"]
        profile = asset["target_profile"]
        for template in intake["target_profiles"][profile]:
            if " when " in template or " key " in template or " entry " in template or template.endswith(".name"):
                continue
            path = REPO / template.format(id=asset_id)
            if path.exists():
                proposed_existing.append(str(path.relative_to(REPO)))
    if proposed_existing:
        fail(f"proposed target path collisions {proposed_existing}")

    role_clip_count = sum(bool(asset["declared_clips"]) for asset in assets)
    if role_clip_count != intake["native_gate"]["role_clip_authoring_required_assets"]:
        fail(f"role clip count mismatch {role_clip_count}")

    print("PASS: exact 21-ID Packet 006 Whisperwood subset")
    print("PASS: 10 authority hashes")
    print("PASS: 105 canonical source files exist and match normalization hashes")
    print("PASS: 21 effect-locator gaps and 10 role-clip repair sets remain explicit")
    print("PASS: 0 exact G7 runtime-ID collisions")
    print("PASS: 0 proposed target-path collisions at integration base")


if __name__ == "__main__":
    main()
