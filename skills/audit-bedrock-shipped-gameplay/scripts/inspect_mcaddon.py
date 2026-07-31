#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import zipfile


DEFAULT_VALIDATOR = (
    Path(__file__).resolve().parents[2]
    / "translate-java-mods-to-bedrock/scripts/validate_bedrock_pack_hazards.py"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    for info in members:
        path = PurePosixPath(info.filename)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive member: {info.filename}")
        mode = info.external_attr >> 16
        if mode & 0o170000 == 0o120000:
            raise ValueError(f"symlink archive member: {info.filename}")
    return members


def pack_kind(pack_path: Path) -> str:
    with zipfile.ZipFile(pack_path) as archive:
        safe_members(archive)
        manifest = json.loads(archive.read("manifest.json"))
    types = {
        module.get("type")
        for module in manifest.get("modules", [])
        if isinstance(module, dict)
    }
    if "data" in types or "script" in types:
        return "behavior"
    if "resources" in types:
        return "resource"
    raise ValueError(f"cannot classify nested pack {pack_path.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcaddon", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--cooperative", action="store_true")
    parser.add_argument("--require-pack-icons", action="store_true")
    parser.add_argument(
        "--validator",
        type=Path,
        default=DEFAULT_VALIDATOR,
    )
    args = parser.parse_args()

    package_bytes = args.mcaddon.read_bytes()
    package_sha = sha256(package_bytes)
    if package_sha != args.expected_sha256.lower():
        raise SystemExit(
            json.dumps({
                "status": "FAIL",
                "code": "PACKAGE_HASH_MISMATCH",
                "actual": package_sha,
                "expected": args.expected_sha256.lower(),
            })
        )

    with tempfile.TemporaryDirectory(prefix="bedrock-shipped-audit-") as tmp:
        root = Path(tmp)
        nested_root = root / "nested"
        nested_root.mkdir()
        with zipfile.ZipFile(args.mcaddon) as addon:
            members = safe_members(addon)
            addon.extractall(nested_root)

        packs: dict[str, Path] = {}
        pack_hashes: dict[str, str] = {}
        for path in sorted(nested_root.rglob("*.mcpack")):
            kind = pack_kind(path)
            if kind in packs:
                raise SystemExit(f"multiple {kind} packs are not supported")
            packs[kind] = path
            pack_hashes[kind] = sha256(path.read_bytes())
        if set(packs) != {"behavior", "resource"}:
            raise SystemExit(f"expected one BP and one RP, found {sorted(packs)}")

        extracted: dict[str, Path] = {}
        for kind, pack in packs.items():
            target = root / kind
            target.mkdir()
            with zipfile.ZipFile(pack) as archive:
                safe_members(archive)
                archive.extractall(target)
            extracted[kind] = target

        command = [
            "python3",
            str(args.validator),
            "--behavior-pack",
            str(extracted["behavior"]),
            "--resource-pack",
            str(extracted["resource"]),
        ]
        if args.cooperative:
            command.append("--cooperative")
        if args.require_pack_icons:
            command.append("--require-pack-icons")
        completed = subprocess.run(command, text=True, capture_output=True)
        try:
            validation = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            validation = {
                "status": "FAIL",
                "findings": [{
                    "code": "VALIDATOR_OUTPUT_INVALID",
                    "path": str(args.validator),
                    "detail": str(error),
                }],
            }

        result = {
            "schema_version": "1.0.0",
            "status": validation.get("status", "FAIL"),
            "candidate": {
                "path": str(args.mcaddon),
                "sha256": package_sha,
                "member_count": len(members),
            },
            "nested_pack_sha256": pack_hashes,
            "validator": {
                "path": str(args.validator),
                "exit_status": completed.returncode,
                "result": validation,
                "stderr": completed.stderr,
            },
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
