#!/usr/bin/env python3
"""Deterministically package committed Wave 1 G8 BP/RP source bytes.

This builder does not generate source content, freeze a candidate, or qualify a
package.  Its output names are deliberately successor-specific so invoking it
cannot amend the frozen G7 artifacts inherited by this repository.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
FIXED_TIME = (2026, 1, 1, 0, 0, 0)
GENERATION = 8
GENERATION_ID = "AIONBOUND_WAVE_1_INTEGRATION_G000008"
PRODUCT_SLUG = "aionbound-wave-1-living-world-g8"
BUILD_MODE = "sorted members, fixed timestamps, fixed permissions, deflate level 9"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def atomic_write(target: Path, value: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(value)
        stream.flush()
    temporary.replace(target)


def source_members(root: Path, pack_names: tuple[str, ...] = ("behavior_pack", "resource_pack")) -> list[dict]:
    entries: list[dict] = []
    for pack_name in pack_names:
        source = root / pack_name
        if not source.is_dir():
            raise FileNotFoundError(f"missing source pack: {source}")
        for member in sorted(path for path in source.rglob("*") if path.is_file()):
            relative = member.relative_to(root).as_posix()
            entries.append({"path": relative, "sha256": digest(member), "size": member.stat().st_size})
    return entries


def source_ledger(root: Path) -> dict:
    entries = source_members(root)
    aggregate_input = "".join(
        f'{row["path"]}\t{row["sha256"]}\t{row["size"]}\n' for row in entries
    ).encode()
    return {
        "aggregate_sha256": sha256_bytes(aggregate_input),
        "entries": entries,
        "generation": GENERATION,
        "generation_id": GENERATION_ID,
        "member_count": len(entries),
        "scope": ["behavior_pack", "resource_pack"],
        "state": "SOURCE_BYTE_LEDGER_COMPLETE",
    }


def pack_tree_bytes(source: Path) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for member in sorted(path for path in source.rglob("*") if path.is_file()):
            relative = member.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, member.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def pack_addon_bytes(packs: list[tuple[str, bytes]]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in packs:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload)
    return output.getvalue()


def safe_archive_member(value: str) -> str:
    member = PurePosixPath(value)
    if member.is_absolute() or not member.parts or ".." in member.parts:
        raise ValueError(f"unsafe packaged entrypoint: {value!r}")
    return member.as_posix()


def packaged_entrypoint(root: Path, behavior_pack_name: str, addon_name: str) -> dict:
    manifest = json.loads((root / "behavior_pack/manifest.json").read_text())
    script_modules = [module for module in manifest.get("modules", []) if module.get("type") == "script"]
    if len(script_modules) != 1:
        raise ValueError(f"expected exactly one behavior-pack script module, found {len(script_modules)}")
    entrypoint = safe_archive_member(script_modules[0].get("entry", ""))
    source = root / "behavior_pack" / entrypoint
    if not source.is_file():
        raise FileNotFoundError(f"manifest script entrypoint is absent: {source}")
    return {
        "address": f"{addon_name}!/{behavior_pack_name}!/{entrypoint}",
        "behavior_mcpack_member": behavior_pack_name,
        "entrypoint_member": entrypoint,
        "sha256": digest(source),
        "size": source.stat().st_size,
    }


def output_names() -> dict[str, str]:
    return {
        "behavior": f"{PRODUCT_SLUG}-behavior.mcpack",
        "resources": f"{PRODUCT_SLUG}-resources.mcpack",
        "addon": f"{PRODUCT_SLUG}.mcaddon",
        "ledger": f"{PRODUCT_SLUG}-source-byte-ledger.json",
        "manifest": f"{PRODUCT_SLUG}-artifact-manifest.json",
    }


def build_once(root: Path = ROOT, output_dir: Path = DIST) -> dict:
    """Build one deterministic, mutable workspace output set.

    Candidate freeze and immutable provenance binding are intentionally outside
    this function.  Returned hashes are suitable inputs to that later step.
    """
    root = root.resolve()
    output_dir = output_dir.resolve()
    names = output_names()
    if any("g7" in name.lower() for name in names.values()):
        raise AssertionError("successor builder must never target a G7 artifact name")

    behavior_bytes = pack_tree_bytes(root / "behavior_pack")
    resource_bytes = pack_tree_bytes(root / "resource_pack")
    addon_bytes = pack_addon_bytes([
        (names["behavior"], behavior_bytes),
        (names["resources"], resource_bytes),
    ])
    ledger = source_ledger(root)
    entrypoint = packaged_entrypoint(root, names["behavior"], names["addon"])

    payloads = {
        names["behavior"]: behavior_bytes,
        names["resources"]: resource_bytes,
        names["addon"]: addon_bytes,
        names["ledger"]: canonical_json(ledger),
    }
    for name, payload in payloads.items():
        atomic_write(output_dir / name, payload)

    artifacts = [
        {"path": name, "sha256": sha256_bytes(payload), "size": len(payload)}
        for name, payload in payloads.items()
    ]
    manifest = {
        "artifacts": artifacts,
        "build_mode": BUILD_MODE,
        "generation": GENERATION,
        "generation_id": GENERATION_ID,
        "packaged_entrypoint": entrypoint,
        "source_generation_performed": False,
        "source_ledger": {
            "aggregate_sha256": ledger["aggregate_sha256"],
            "artifact": names["ledger"],
            "artifact_sha256": sha256_bytes(payloads[names["ledger"]]),
            "member_count": ledger["member_count"],
        },
        "state": "DETERMINISTIC_WORKSPACE_BUILD_COMPLETE_NOT_FROZEN_NOT_QUALIFIED",
    }
    manifest_bytes = canonical_json(manifest)
    atomic_write(output_dir / names["manifest"], manifest_bytes)
    return manifest


def comparison_signature(manifest: dict) -> dict:
    return {
        "artifacts": {row["path"]: row["sha256"] for row in manifest["artifacts"]},
        "packaged_entrypoint": manifest["packaged_entrypoint"],
        "source_ledger": manifest["source_ledger"],
    }


def build_twice_and_compare(root: Path, first_output: Path, second_output: Path) -> dict:
    first = build_once(root, first_output)
    second = build_once(root, second_output)
    first_signature = comparison_signature(first)
    second_signature = comparison_signature(second)
    equal = first_signature == second_signature
    return {
        "build_1_equals_build_2": equal,
        "build_invocations": 2,
        "generation": GENERATION,
        "generation_id": GENERATION_ID,
        "signature": first_signature if equal else None,
        "state": "DETERMINISTIC_BUILD_COMPARISON_PASS" if equal else "DETERMINISTIC_BUILD_COMPARISON_FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=DIST)
    parser.add_argument("--compare-output-dir", type=Path)
    args = parser.parse_args()
    if args.compare_output_dir:
        result = build_twice_and_compare(args.root, args.output_dir, args.compare_output_dir)
        if not result["build_1_equals_build_2"]:
            raise SystemExit(json.dumps(result, sort_keys=True))
    else:
        result = build_once(args.root, args.output_dir)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
