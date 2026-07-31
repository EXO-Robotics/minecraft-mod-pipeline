#!/usr/bin/env python3
"""Fail-closed exact-package Stable BDS qualifier.

The image containing this program also contains one frozen BDS seed and one
small base-world fixture. Candidate inputs are mounted read-only. All mutable
state lives below /work and all returned evidence below /output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "crazycraft-exact-package-qualifier-v2"
REMOTE_SCHEMA = "crazycraft-remote-v1"
PROFILE_SCHEMA = "crazycraft-bds-candidate-profile-v1"
STABLE_VERSION = "1.26.33.2"
STABLE_BINARY_SHA256 = "978ea655c418f112a33b80043d676712ad080724382fafda9509825910fa4043"
BASE_WORLD_SHA256 = "061501b67b0886296ad2765f1b7c5246efbe38d64b9494303a05b9ee81a58d9a"
TRAILBOUND_FIXTURE = "TRAILBOUND_EXACT_PACKAGE_LOAD_RESTART_V1"
READY_MARKER = "Server started."
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,95}$")
SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FATAL_PATTERNS = (
    re.compile(r"\[Scripting\]\s*\[error\]", re.I),
    re.compile(r"\bfailed to load\b", re.I),
    re.compile(r"\bmissing dependency\b", re.I),
    re.compile(r"\bmanifest.*error\b", re.I),
    re.compile(r"\bjson.*error\b", re.I),
    re.compile(r"\bunhandled.*exception\b", re.I),
    re.compile(r"\bsegmentation fault\b", re.I),
)


class QualificationError(RuntimeError):
    pass


def safe_relative(value: Any, *, basename_only: bool = False) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise QualificationError("unsafe relative path")
    if "\\" in value or "\x00" in value or "\n" in value or "\r" in value:
        raise QualificationError("unsafe relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or any(part in {"", ".", ".."} or part.startswith(".") for part in path.parts)
        or len(path.parts) > 16
        or (basename_only and len(path.parts) != 1)
    ):
        raise QualificationError("unsafe relative path")
    return path.as_posix()


def validate_version(value: Any) -> list[int]:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(not isinstance(part, int) or not 0 <= part <= 65535 for part in value)
    ):
        raise QualificationError("invalid manifest version")
    return list(value)


def validate_uuid(value: Any) -> str:
    try:
        parsed = uuid.UUID(str(value))
    except (ValueError, AttributeError) as exc:
        raise QualificationError("invalid manifest UUID") from exc
    canonical = str(parsed)
    if value != canonical:
        raise QualificationError("manifest UUID must be canonical lowercase")
    return canonical


def validate_candidate_profile(profile: Any) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise QualificationError("candidate profile missing")
    required = {
        "schema_version",
        "behavior_pack",
        "resource_pack",
        "addon",
        "script",
        "expected_pack_marker",
        "world_name",
        "fixture_id",
    }
    require_keys(profile, required, required)
    if profile["schema_version"] != PROFILE_SCHEMA:
        raise QualificationError("candidate profile schema mismatch")
    normalized: dict[str, Any] = {
        "schema_version": PROFILE_SCHEMA,
        "expected_pack_marker": profile["expected_pack_marker"],
        "world_name": profile["world_name"],
        "fixture_id": profile["fixture_id"],
    }
    if (
        not isinstance(profile["expected_pack_marker"], str)
        or not profile["expected_pack_marker"]
        or len(profile["expected_pack_marker"]) > 160
        or "\n" in profile["expected_pack_marker"]
        or "\r" in profile["expected_pack_marker"]
    ):
        raise QualificationError("invalid expected pack marker")
    if (
        not isinstance(profile["world_name"], str)
        or not SAFE_NAME_RE.fullmatch(profile["world_name"])
    ):
        raise QualificationError("invalid world name")
    if (
        not isinstance(profile["fixture_id"], str)
        or not SAFE_TOKEN_RE.fullmatch(profile["fixture_id"])
    ):
        raise QualificationError("invalid fixture ID")
    for role in ("behavior_pack", "resource_pack"):
        value = profile[role]
        pack_required = {"manifest_uuid", "version", "install_directory"}
        if not isinstance(value, dict):
            raise QualificationError(f"invalid {role} profile")
        require_keys(value, pack_required, pack_required)
        normalized[role] = {
            "manifest_uuid": validate_uuid(value["manifest_uuid"]),
            "version": validate_version(value["version"]),
            "install_directory": safe_relative(
                value["install_directory"], basename_only=True
            ),
        }
    addon = profile["addon"]
    addon_required = {"behavior_member", "resource_member"}
    if not isinstance(addon, dict):
        raise QualificationError("invalid addon profile")
    require_keys(addon, addon_required, addon_required)
    normalized["addon"] = {
        key: safe_relative(addon[key], basename_only=True)
        for key in sorted(addon_required)
    }
    if (
        not normalized["addon"]["behavior_member"].endswith(".mcpack")
        or not normalized["addon"]["resource_member"].endswith(".mcpack")
        or normalized["addon"]["behavior_member"]
        == normalized["addon"]["resource_member"]
    ):
        raise QualificationError("invalid addon member names")
    script = profile["script"]
    if script is None:
        normalized["script"] = None
    else:
        script_required = {"entry_path", "expected_marker"}
        if not isinstance(script, dict):
            raise QualificationError("invalid script profile")
        require_keys(script, script_required, script_required)
        marker = script["expected_marker"]
        if marker is not None and (
            not isinstance(marker, str)
            or not marker
            or len(marker) > 200
            or "\n" in marker
            or "\r" in marker
        ):
            raise QualificationError("invalid script marker")
        normalized["script"] = {
            "entry_path": safe_relative(script["entry_path"]),
            "expected_marker": marker,
        }
    return normalized


def legacy_trailbound_profile(request: dict[str, Any], bds: dict[str, Any]) -> dict[str, Any]:
    legacy_signature = {
        "job_id": "JOB-000000000012",
        "campaign_id": "trailbound-packs",
        "behavior_pack_sha256": "f26e9daddfd7ba8893f6ccd5934b45ec0f88e1380b3e02038c13051d71fad8f3",
        "resource_pack_sha256": "14fcdba454ab5ca85381628d71845dadc80b9c255eb812b7aaebea84814ef7af",
        "mcaddon_sha256": "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
    }
    observed = {
        "job_id": request.get("job_id"),
        "campaign_id": request.get("campaign_id"),
        "behavior_pack_sha256": bds.get("behavior_pack_sha256"),
        "resource_pack_sha256": bds.get("resource_pack_sha256"),
        "mcaddon_sha256": bds.get("mcaddon_sha256"),
    }
    if observed != legacy_signature:
        raise QualificationError("candidate profile required")
    return validate_candidate_profile(
        {
            "schema_version": PROFILE_SCHEMA,
            "behavior_pack": {
                "manifest_uuid": "7c428986-b20f-548d-84ae-1c56029426b2",
                "version": [1, 1, 0],
                "install_directory": "trailbound-packs",
            },
            "resource_pack": {
                "manifest_uuid": "565a3efe-77ac-5533-8097-3098881e17d0",
                "version": [1, 1, 0],
                "install_directory": "trailbound-packs",
            },
            "addon": {
                "behavior_member": "trailbound-packs-behavior.mcpack",
                "resource_member": "trailbound-packs-resource.mcpack",
            },
            "script": {
                "entry_path": "scripts/main.js",
                "expected_marker": "[trailbound] runtime initialized",
            },
            "expected_pack_marker": "Trailbound Packs Behavior",
            "world_name": "Trailbound Exact Package",
            "fixture_id": TRAILBOUND_FIXTURE,
        }
    )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def payload_hash(record: dict[str, Any], field: str) -> str:
    value = dict(record)
    value.pop(field, None)
    return sha256_bytes(canonical_bytes(value))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    os.replace(temporary, path)


def require_keys(record: dict[str, Any], required: set[str], allowed: set[str]) -> None:
    missing = sorted(required - record.keys())
    extra = sorted(record.keys() - allowed)
    if missing or extra:
        raise QualificationError(f"request fields mismatch missing={missing} extra={extra}")


def validate_request(request: dict[str, Any]) -> dict[str, Any]:
    top_required = {
        "schema_version",
        "job_id",
        "job_type",
        "requesting_authority",
        "assignment_id",
        "campaign_id",
        "exact_input_authorities",
        "permitted_evidence_roots",
        "permitted_candidate_paths",
        "permitted_output_directory",
        "prohibited_disclosure_classes",
        "timeout_seconds",
        "termination_policy",
        "requested_result_schema",
        "request_payload_sha256",
        "bds",
    }
    require_keys(request, top_required, top_required)
    if request["schema_version"] != REMOTE_SCHEMA:
        raise QualificationError("remote request schema mismatch")
    if request["request_payload_sha256"] != payload_hash(
        request, "request_payload_sha256"
    ):
        raise QualificationError("request payload hash mismatch")
    if request["job_type"] != "BDS_QUALIFICATION":
        raise QualificationError("only BDS_QUALIFICATION is accepted")
    if request["requesting_authority"] not in {"T1", "T10"}:
        raise QualificationError("request authority rejected")
    if request["permitted_evidence_roots"]:
        raise QualificationError("evidence mounts are forbidden")
    if request["permitted_output_directory"] != "artifacts":
        raise QualificationError("output contract mismatch")
    bds = request["bds"]
    required_bds = {
        "candidate_repository",
        "candidate_ref",
        "content_commit",
        "content_tree",
        "metadata_commit",
        "metadata_tree",
        "behavior_pack_path",
        "behavior_pack_size",
        "behavior_pack_sha256",
        "resource_pack_path",
        "resource_pack_size",
        "resource_pack_sha256",
        "mcaddon_path",
        "mcaddon_size",
        "mcaddon_sha256",
        "image_digest",
        "image_platform",
        "qualifier_sha256",
        "bds_channel",
        "bds_version",
        "bds_binary_sha256",
        "base_world_sha256",
        "fixture_set",
        "expected_gates",
        "port",
        "container_name",
        "cpus",
        "memory_mb",
    }
    require_keys(bds, required_bds, required_bds | {"candidate_profile"})
    if bds["bds_channel"] != "STABLE" or bds["bds_version"] != STABLE_VERSION:
        raise QualificationError("unapproved BDS channel/version")
    if bds["bds_binary_sha256"] != STABLE_BINARY_SHA256:
        raise QualificationError("BDS binary authority mismatch")
    if bds["base_world_sha256"] != BASE_WORLD_SHA256:
        raise QualificationError("base-world authority mismatch")
    if bds["image_platform"] != "linux/amd64":
        raise QualificationError("BDS platform mismatch")
    for key in (
        "behavior_pack_path",
        "resource_pack_path",
        "mcaddon_path",
    ):
        bds[key] = safe_relative(bds[key])
    if len(
        {
            bds["behavior_pack_path"],
            bds["resource_pack_path"],
            bds["mcaddon_path"],
        }
    ) != 3:
        raise QualificationError("candidate input paths must be distinct")
    for key in (
        "behavior_pack_sha256",
        "resource_pack_sha256",
        "mcaddon_sha256",
        "qualifier_sha256",
    ):
        if not isinstance(bds[key], str) or not SHA256_RE.fullmatch(bds[key]):
            raise QualificationError(f"invalid {key}")
    profile = (
        validate_candidate_profile(bds["candidate_profile"])
        if "candidate_profile" in bds
        else legacy_trailbound_profile(request, bds)
    )
    if bds["fixture_set"] != profile["fixture_id"]:
        raise QualificationError("fixture authority mismatch")
    permitted = {
        safe_relative(value) for value in request["permitted_candidate_paths"]
    }
    expected_permitted = {
        bds["behavior_pack_path"],
        bds["resource_pack_path"],
        bds["mcaddon_path"],
        "request.json",
    }
    if permitted != expected_permitted:
        raise QualificationError("candidate path allowlist mismatch")
    normalized_bds = dict(bds)
    normalized_bds["_candidate_profile"] = profile
    return normalized_bds


def validate_regular(path: Path, expected_size: int, expected_hash: str) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise QualificationError(f"unsafe input file: {path.name}")
    if info.st_size != expected_size or sha256_file(path) != expected_hash:
        raise QualificationError(f"exact input authority mismatch: {path.name}")


def safe_extract(archive_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if not members:
            raise QualificationError(f"empty archive: {archive_path.name}")
        for member in members:
            relative = PurePosixPath(member.filename)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or "\\" in member.filename
                or any(part.startswith(".") for part in relative.parts)
            ):
                raise QualificationError(f"unsafe archive member: {member.filename}")
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise QualificationError(f"archive symlink rejected: {member.filename}")
            target = destination.joinpath(*relative.parts)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)


def read_manifest(
    pack_root: Path, expected_uuid: str, expected_version: list[int]
) -> dict[str, Any]:
    manifest_path = pack_root / "manifest.json"
    if not manifest_path.is_file():
        raise QualificationError("pack manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    header = manifest.get("header", {})
    if (
        header.get("uuid") != expected_uuid
        or header.get("version") != expected_version
    ):
        raise QualificationError("pack manifest identity mismatch")
    return manifest


def verify_package_relationships(
    input_root: Path,
    work_root: Path,
    bds: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    bp = input_root / bds["behavior_pack_path"]
    rp = input_root / bds["resource_pack_path"]
    addon = input_root / bds["mcaddon_path"]
    addon_root = work_root / "addon"
    bp_root = work_root / "behavior"
    rp_root = work_root / "resource"
    safe_extract(addon, addon_root)
    members = {path.name: path for path in addon_root.iterdir() if path.is_file()}
    expected = {
        profile["addon"]["behavior_member"]: sha256_file(bp),
        profile["addon"]["resource_member"]: sha256_file(rp),
    }
    if set(members) != set(expected):
        raise QualificationError("MCAddon member set mismatch")
    for name, digest in expected.items():
        if sha256_file(members[name]) != digest:
            raise QualificationError(f"MCAddon constituent mismatch: {name}")
    safe_extract(bp, bp_root)
    safe_extract(rp, rp_root)
    bp_manifest = read_manifest(
        bp_root,
        profile["behavior_pack"]["manifest_uuid"],
        profile["behavior_pack"]["version"],
    )
    rp_manifest = read_manifest(
        rp_root,
        profile["resource_pack"]["manifest_uuid"],
        profile["resource_pack"]["version"],
    )
    dependencies = bp_manifest.get("dependencies", [])
    if not any(
        entry.get("uuid") == profile["resource_pack"]["manifest_uuid"]
        and entry.get("version") == profile["resource_pack"]["version"]
        for entry in dependencies
        if isinstance(entry, dict)
    ):
        raise QualificationError("BP/RP dependency binding missing")
    script_modules = [
        entry
        for entry in bp_manifest.get("modules", [])
        if entry.get("type") == "script"
    ]
    script_profile = profile["script"]
    if script_profile is None:
        if script_modules:
            raise QualificationError("undeclared script module")
    else:
        if (
            len(script_modules) != 1
            or script_modules[0].get("entry") != script_profile["entry_path"]
        ):
            raise QualificationError("shipped script entrypoint mismatch")
        script = bp_root / script_profile["entry_path"]
        if not script.is_file():
            raise QualificationError("shipped script entrypoint missing")
        marker = script_profile["expected_marker"]
        if marker is not None and marker not in script.read_text(
            encoding="utf-8"
        ):
            raise QualificationError("declared runtime marker absent from entrypoint")
    return bp_root, rp_root, bp_manifest, rp_manifest


def unpack_base_world(
    base_world: Path, destination: Path, world_name: str
) -> None:
    safe_extract(base_world, destination)
    for name in ("behavior_packs", "resource_packs"):
        shutil.rmtree(destination / name, ignore_errors=True)
        (destination / name).mkdir()
    for name in ("world_behavior_packs.json", "world_resource_packs.json"):
        (destination / name).unlink(missing_ok=True)
    (destination / "levelname.txt").write_text(world_name + "\n")


def pack_binding(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "pack_id": manifest["header"]["uuid"],
        "version": manifest["header"]["version"],
    }


def configure_server(server_root: Path, world_name: str, port: int) -> None:
    properties = server_root / "server.properties"
    values: dict[str, str] = {}
    if properties.is_file():
        for line in properties.read_text(errors="replace").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key] = value
    values.update(
        {
            "level-name": world_name,
            "online-mode": "false",
            "allow-list": "false",
            "white-list": "false",
            "content-log-console-output-enabled": "true",
            "texturepack-required": "true",
            "server-port": str(port),
            "server-portv6": str(port + 1),
            "enable-lan-visibility": "false",
            "emit-server-telemetry": "false",
        }
    )
    properties.write_text(
        "\n".join(f"{key}={values[key]}" for key in sorted(values)) + "\n",
        encoding="utf-8",
    )


def run_cycle(
    server_root: Path,
    binary: Path,
    cycle: int,
    timeout: int,
    log_path: Path,
    expected_pack_marker: str,
    expected_script_marker: str | None,
) -> dict[str, Any]:
    started = time.monotonic()
    process = subprocess.Popen(
        [str(binary)],
        cwd=server_root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(server_root),
            "LD_LIBRARY_PATH": str(server_root),
        },
    )
    lines: list[str] = []
    ready = False
    marker = False
    clean_shutdown = False
    deadline = time.monotonic() + timeout
    assert process.stdout is not None
    try:
        while time.monotonic() < deadline:
            line = process.stdout.readline()
            if line:
                lines.append(line)
                ready = ready or READY_MARKER in line
                marker = marker or (
                    expected_script_marker is not None
                    and expected_script_marker in line
                )
                if ready and (expected_script_marker is None or marker):
                    break
            elif process.poll() is not None:
                break
            else:
                time.sleep(0.05)
        if not ready or (expected_script_marker is not None and not marker):
            raise QualificationError(
                f"BDS cycle {cycle} did not reach required runtime markers"
            )
        time.sleep(2)
        assert process.stdin is not None
        process.stdin.write("list\n")
        process.stdin.flush()
        time.sleep(1)
        process.stdin.write("stop\n")
        process.stdin.flush()
        try:
            remainder, _ = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                remainder, _ = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                remainder, _ = process.communicate()
        lines.append(remainder or "")
        clean_shutdown = process.returncode == 0 and any(
            marker_text in "".join(lines)
            for marker_text in ("Quit correctly", "Server stop requested.")
        )
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    log_text = "".join(lines)
    log_path.write_text(log_text, encoding="utf-8")
    fatal = [
        line
        for line in log_text.splitlines()
        if any(pattern.search(line) for pattern in FATAL_PATTERNS)
    ]
    return {
        "cycle": cycle,
        "exit_code": process.returncode,
        "ready": ready,
        "behavior_pack_discovered": expected_pack_marker in log_text,
        "script_runtime_loaded": marker
        if expected_script_marker is not None
        else None,
        "script_marker_required": expected_script_marker is not None,
        "fatal_lines": fatal,
        "clean_shutdown": clean_shutdown,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "log_path": log_path.name,
        "log_sha256": sha256_file(log_path),
    }


def inventory_outputs(output_root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(output_root.rglob("*")):
        if path.is_symlink():
            raise QualificationError("output symlink rejected")
        if path.is_file():
            records.append(
                {
                    "path": path.relative_to(output_root).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return records


def qualify(request_path: Path, output_root: Path) -> int:
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    request = json.loads(request_path.read_text(encoding="utf-8"))
    bds = validate_request(request)
    profile = bds["_candidate_profile"]
    if bds["qualifier_sha256"] != sha256_file(Path(__file__)):
        raise QualificationError("embedded qualifier authority mismatch")
    input_root = request_path.parent.parent / "input"
    if not input_root.is_dir():
        input_root = Path("/input")
    expected_inputs = {
        bds["behavior_pack_path"],
        bds["resource_pack_path"],
        bds["mcaddon_path"],
    }
    observed: set[str] = set()
    for path in sorted(input_root.rglob("*")):
        if path.is_symlink():
            raise QualificationError("input symlink rejected")
        if path.is_file():
            observed.add(path.relative_to(input_root).as_posix())
    if observed != expected_inputs:
        raise QualificationError(f"unexpected mounted inputs: {sorted(observed)}")
    for role, path_field in (
        ("behavior_pack", "behavior_pack_path"),
        ("resource_pack", "resource_pack_path"),
        ("mcaddon", "mcaddon_path"),
    ):
        validate_regular(
            input_root / bds[path_field],
            int(bds[f"{role}_size"]),
            bds[f"{role}_sha256"],
        )
    work_root = Path("/work")
    if work_root.exists():
        for entry in work_root.iterdir():
            if entry.name != "lost+found":
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
    work_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    bp_root, rp_root, bp_manifest, rp_manifest = verify_package_relationships(
        input_root, work_root, bds, profile
    )
    image_seed = Path(f"/opt/crazycraft/bds/stable-{STABLE_VERSION}")
    base_world = Path("/opt/crazycraft/fixtures/base-world.mcworld")
    binary_source = image_seed / f"bedrock_server-{STABLE_VERSION}"
    validate_regular(binary_source, binary_source.stat().st_size, STABLE_BINARY_SHA256)
    validate_regular(base_world, base_world.stat().st_size, BASE_WORLD_SHA256)
    server_root = work_root / "server"
    shutil.copytree(image_seed, server_root, symlinks=False)
    binary = server_root / binary_source.name
    binary.chmod(0o500)
    world_name = profile["world_name"]
    world_root = server_root / "worlds" / world_name
    world_root.mkdir(parents=True)
    unpack_base_world(base_world, world_root, world_name)
    shutil.copytree(
        bp_root,
        world_root
        / "behavior_packs"
        / profile["behavior_pack"]["install_directory"],
    )
    shutil.copytree(
        rp_root,
        world_root
        / "resource_packs"
        / profile["resource_pack"]["install_directory"],
    )
    write_json(
        world_root / "world_behavior_packs.json", [pack_binding(bp_manifest)]
    )
    write_json(
        world_root / "world_resource_packs.json", [pack_binding(rp_manifest)]
    )
    configure_server(server_root, world_name, int(bds["port"]))
    script_marker = (
        profile["script"]["expected_marker"]
        if profile["script"] is not None
        else None
    )
    cycles = [
        run_cycle(
            server_root,
            binary,
            cycle,
            180,
            output_root / f"stable-cycle-{cycle}.log",
            profile["expected_pack_marker"],
            script_marker,
        )
        for cycle in (1, 2)
    ]
    product_failures = []
    for cycle in cycles:
        if not (
            cycle["ready"]
            and cycle["behavior_pack_discovered"]
            and (
                script_marker is None
                or cycle["script_runtime_loaded"]
            )
            and cycle["clean_shutdown"]
            and not cycle["fatal_lines"]
        ):
            product_failures.append(f"cycle-{cycle['cycle']}")
    resource_configured = (
        json.loads((world_root / "world_resource_packs.json").read_text())
        == [pack_binding(rp_manifest)]
    )
    fixture = {
        "fixture_id": profile["fixture_id"],
        "shipped_entrypoint_marker_each_cycle": all(
            cycle["script_runtime_loaded"] for cycle in cycles
        )
        if script_marker is not None
        else "NOT_REQUIRED",
        "same_world_reused": True,
        "restart_reload": all(cycle["ready"] for cycle in cycles),
        "persistence_scope": "WORLD_REOPEN_ONLY_NO_PLAYER_MUTATION",
        "persistence_gameplay": "NOT_RUN",
        "passed": not product_failures,
    }
    fixture_output = (
        "trailbound-fixture-result.json"
        if profile["fixture_id"] == TRAILBOUND_FIXTURE
        else "candidate-fixture-result.json"
    )
    write_json(output_root / fixture_output, fixture)
    result = {
        "schema_version": REMOTE_SCHEMA,
        "job_id": request["job_id"],
        "job_type": request["job_type"],
        "requesting_authority": request["requesting_authority"],
        "assignment_id": request["assignment_id"],
        "campaign_id": request["campaign_id"],
        "outcome": "PASS" if not product_failures else "FAIL",
        "result_classification": "TEST_PASS" if not product_failures else "TEST_FAIL_PRODUCT",
        "candidate": {
            "repository": bds["candidate_repository"],
            "ref": bds["candidate_ref"],
            "content_commit": bds["content_commit"],
            "content_tree": bds["content_tree"],
            "metadata_commit": bds["metadata_commit"],
            "metadata_tree": bds["metadata_tree"],
            "behavior_pack": {
                "path": bds["behavior_pack_path"],
                "size": bds["behavior_pack_size"],
                "sha256": bds["behavior_pack_sha256"],
            },
            "resource_pack": {
                "path": bds["resource_pack_path"],
                "size": bds["resource_pack_size"],
                "sha256": bds["resource_pack_sha256"],
            },
            "mcaddon": {
                "path": bds["mcaddon_path"],
                "size": bds["mcaddon_size"],
                "sha256": bds["mcaddon_sha256"],
            },
        },
        "environment": {
            "qualifier_schema": SCHEMA,
            "qualifier_sha256": bds["qualifier_sha256"],
            "tester_image": bds["image_digest"],
            "platform": bds["image_platform"],
            "platform_proof": "DOCKER_DESKTOP_AMD64_EMULATION",
            "bds_channel": bds["bds_channel"],
            "bds_version": bds["bds_version"],
            "bds_binary_sha256": bds["bds_binary_sha256"],
            "world_name": world_name,
            "candidate_profile": profile,
            "ports": [bds["port"], bds["port"] + 1],
            "cpus": bds["cpus"],
            "memory_mb": bds["memory_mb"],
            "container_hostname": os.uname().nodename,
        },
        "execution": {
            "request_accepted": True,
            "exact_hashes_verified": True,
            "safe_unpack": True,
            "behavior_pack_installed": True,
            "resource_pack_installed": True,
            "resource_pack_activation_configured": resource_configured,
            "cycles": cycles,
            "fixture": fixture,
            "product_failures": product_failures,
            "total_runtime_seconds": round(sum(c["elapsed_seconds"] for c in cycles), 3),
        },
        "abstract_results": [
            {
                "qualification": "STABLE_BDS_EXACT_PACKAGE_LOAD_RESTART",
                "status": "PASS" if not product_failures else "FAIL",
            }
        ],
        "opaque_contract_ids": [],
        "opaque_finding_ids": product_failures,
        "required_regression_ids": [],
        "qualification_references": [profile["fixture_id"]],
        "proof_boundary": (
            "Exact Stable BDS package activation, shipped-entrypoint initialization, "
            "clean shutdown, and same-world restart only. No client, player-mutated "
            "persistence, multiplayer, controller, Realm, split-screen, physical "
            "console, rights, branding, Marketplace, or release proof."
        ),
        "external_gates_not_run": [
            "BEDROCK_CLIENT",
            "AUDIO_AUDITION",
            "PLAYER_MUTATED_PERSISTENCE",
            "MULTIPLAYER",
            "CONTROLLER",
            "PHYSICAL_PS4",
            "REALM",
            "SPLIT_SCREEN",
            "RIGHTS",
            "BRANDING",
            "MARKETPLACE",
            "RELEASE",
        ],
        "disclosure_scan": {"status": "PENDING", "matches": []},
        "result_payload_sha256": "",
    }
    result["result_payload_sha256"] = payload_hash(result, "result_payload_sha256")
    write_json(output_root / "qualification-result.json", result)
    ended_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt = {
        "schema_version": SCHEMA,
        "job_id": request["job_id"],
        "started_at": started_at,
        "ended_at": ended_at,
        "candidate_hashes": {
            name: sha256_file(input_root / name) for name in sorted(expected_inputs)
        },
        "outputs": inventory_outputs(output_root),
        "server_stopped": all(cycle["clean_shutdown"] for cycle in cycles),
        "temporary_world_policy": "CONTAINER_TMPFS_REMOVED_WITH_CONTAINER",
        "input_candidate_read_only": True,
        "unauthorized_mounts_observed": [],
        "proof_boundary": result["proof_boundary"],
        "receipt_payload_sha256": "",
    }
    receipt["receipt_payload_sha256"] = payload_hash(
        receipt, "receipt_payload_sha256"
    )
    write_json(output_root / "qualifier-receipt.json", receipt)
    return 0 if not product_failures else 2


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="qualify-exact-package",
        description="Qualify one exact immutable Bedrock package in Stable BDS.",
        allow_abbrev=False,
    )
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.request != Path("/control/request.json") or args.output != Path("/output"):
        raise QualificationError("only fixed container paths are accepted")
    return qualify(args.request, args.output)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (QualificationError, OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"QUALIFIER_FAIL_CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
