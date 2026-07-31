#!/usr/bin/env python3
"""Minimal, fail-closed Crazy Craft remote-job protocol primitives."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import time
import uuid
import fcntl
from pathlib import Path, PurePosixPath
from typing import Any

PROTOCOL_VERSION = "crazycraft-remote-v1"
JOB_TYPES = {
    "EVIDENCE_RECOVERY",
    "PRIVATE_CANDIDATE_AUDIT",
    "BDS_QUALIFICATION",
    "COMBINED_PRIVATE_AUDIT_AND_QUALIFICATION",
}
ROLE_JOB_TYPES = {
    "T1": {"EVIDENCE_RECOVERY", "BDS_QUALIFICATION"},
    "T10": {
        "PRIVATE_CANDIDATE_AUDIT",
        "BDS_QUALIFICATION",
        "COMBINED_PRIVATE_AUDIT_AND_QUALIFICATION",
    },
}
JOB_ID_RE = re.compile(r"^JOB-[0-9]{12}$")
SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")

PROHIBITED_DISCLOSURE_CLASSES = {
    "RAW_JAVA",
    "DECOMPILED_TEXT",
    "SOURCE_IDENTIFIERS",
    "SOURCE_PATHS",
    "SOURCE_ASSETS",
    "HIDDEN_CASES",
    "PRIVATE_ORACLE_VALUES",
    "CREDENTIALS",
    "SOURCE_EXPRESSION",
}

PROHIBITED_OUTPUT_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"AKIA",
    b"private-oracle-value:",
    b"hidden-case-value:",
    b"decompiled-java:",
    b"java-source-path:",
    b"source-identifier:",
)


class ValidationError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def payload_hash(record: dict[str, Any], field: str) -> str:
    copy = dict(record)
    copy.pop(field, None)
    return sha256_bytes(canonical_bytes(copy))


def validate_safe_relative_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise ValidationError("unsafe relative path length")
    if "\\" in value or "\x00" in value or "\n" in value or "\r" in value:
        raise ValidationError("unsafe relative path characters")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValidationError("path traversal or absolute path rejected")
    if len(path.parts) > 16:
        raise ValidationError("path depth exceeded")
    if any(part.startswith(".") for part in path.parts):
        raise ValidationError("hidden path rejected")
    return path


def _require_keys(record: dict[str, Any], required: set[str], allowed: set[str]) -> None:
    missing = sorted(required - record.keys())
    extra = sorted(record.keys() - allowed)
    if missing:
        raise ValidationError(f"missing fields: {missing}")
    if extra:
        raise ValidationError(f"unexpected fields: {extra}")


def validate_request(request: dict[str, Any], expected_role: str | None = None) -> None:
    required = {
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
    }
    allowed = required | {"bds"}
    _require_keys(request, required, allowed)
    if request["schema_version"] != PROTOCOL_VERSION:
        raise ValidationError("unsupported request schema")
    if not JOB_ID_RE.fullmatch(request["job_id"]):
        raise ValidationError("invalid job ID")
    role = request["requesting_authority"]
    if role not in ROLE_JOB_TYPES:
        raise ValidationError("unknown requesting authority")
    if expected_role is not None and role != expected_role:
        raise ValidationError("requesting identity mismatch")
    job_type = request["job_type"]
    if job_type not in JOB_TYPES or job_type not in ROLE_JOB_TYPES[role]:
        raise ValidationError("job type not authorized for role")
    for field in ("assignment_id", "campaign_id", "requested_result_schema"):
        if not isinstance(request[field], str) or not SAFE_TOKEN_RE.fullmatch(request[field]):
            raise ValidationError(f"invalid {field}")
    if request["termination_policy"] != "TERMINATE_AND_RECEIPT":
        raise ValidationError("unsupported termination policy")
    if not isinstance(request["timeout_seconds"], int) or not (
        1 <= request["timeout_seconds"] <= 21600
    ):
        raise ValidationError("invalid timeout")
    if request["permitted_output_directory"] != "artifacts":
        raise ValidationError("output directory must be job-local artifacts")
    for collection in (
        "exact_input_authorities",
        "permitted_evidence_roots",
        "permitted_candidate_paths",
        "prohibited_disclosure_classes",
    ):
        if not isinstance(request[collection], list):
            raise ValidationError(f"{collection} must be an array")
    unknown_classes = set(request["prohibited_disclosure_classes"]) - PROHIBITED_DISCLOSURE_CLASSES
    if unknown_classes:
        raise ValidationError(f"unknown disclosure classes: {sorted(unknown_classes)}")
    if set(request["prohibited_disclosure_classes"]) != PROHIBITED_DISCLOSURE_CLASSES:
        raise ValidationError("all prohibited disclosure classes are mandatory")
    for root in request["permitted_evidence_roots"]:
        if not isinstance(root, str) or not root.startswith("/"):
            raise ValidationError("evidence roots must be absolute")
        if ".." in PurePosixPath(root).parts:
            raise ValidationError("evidence root traversal rejected")
    for candidate in request["permitted_candidate_paths"]:
        validate_safe_relative_path(candidate)
    if request["request_payload_sha256"] != payload_hash(
        request, "request_payload_sha256"
    ):
        raise ValidationError("request payload hash mismatch")
    if job_type in {"BDS_QUALIFICATION", "COMBINED_PRIVATE_AUDIT_AND_QUALIFICATION"}:
        validate_bds(request.get("bds"))
        bds = request["bds"]
        expected_candidate_paths = {
            bds["behavior_pack_path"],
            bds["resource_pack_path"],
            bds["mcaddon_path"],
            "request.json",
        }
        if set(request["permitted_candidate_paths"]) != expected_candidate_paths:
            raise ValidationError("BDS candidate path allowlist mismatch")
    elif "bds" in request:
        raise ValidationError("BDS policy supplied to non-BDS job")


def validate_bds(bds: Any) -> None:
    if not isinstance(bds, dict):
        raise ValidationError("missing BDS policy")
    required = {
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
    _require_keys(bds, required, required | {"candidate_profile"})
    for field in (
        "content_commit",
        "content_tree",
        "metadata_commit",
        "metadata_tree",
    ):
        if not isinstance(bds[field], str) or not GIT_OID_RE.fullmatch(bds[field]):
            raise ValidationError(f"invalid BDS {field}")
    for field in (
        "behavior_pack_sha256",
        "resource_pack_sha256",
        "mcaddon_sha256",
        "qualifier_sha256",
        "bds_binary_sha256",
        "base_world_sha256",
    ):
        if not isinstance(bds[field], str) or not SHA256_RE.fullmatch(bds[field]):
            raise ValidationError(f"invalid BDS {field}")
    if bds["bds_channel"] not in {"STABLE", "PREVIEW"}:
        raise ValidationError("invalid BDS channel")
    if bds["image_platform"] != "linux/amd64":
        raise ValidationError("BDS image platform must be linux/amd64")
    if not re.fullmatch(r"^[a-z0-9][a-z0-9._/-]*@sha256:[0-9a-f]{64}$", bds["image_digest"]):
        raise ValidationError("BDS image authority must be one canonical OCI digest")
    if not isinstance(bds["candidate_ref"], str) or not bds["candidate_ref"].startswith("refs/"):
        raise ValidationError("invalid candidate ref")
    artifact_paths = [
        str(validate_safe_relative_path(bds[field]))
        for field in (
            "behavior_pack_path",
            "resource_pack_path",
            "mcaddon_path",
        )
    ]
    if len(set(artifact_paths)) != 3:
        raise ValidationError("BDS artifact paths must be distinct")
    for field in ("behavior_pack_size", "resource_pack_size", "mcaddon_size"):
        if not isinstance(bds[field], int) or bds[field] <= 0:
            raise ValidationError(f"invalid BDS {field}")
    if not isinstance(bds["port"], int) or not 19132 <= bds["port"] <= 29999:
        raise ValidationError("invalid BDS port")
    if not SAFE_TOKEN_RE.fullmatch(bds["container_name"]):
        raise ValidationError("invalid container name")
    if not isinstance(bds["expected_gates"], list) or not bds["expected_gates"]:
        raise ValidationError("missing BDS gates")
    if not isinstance(bds["cpus"], int) or not 1 <= bds["cpus"] <= 8:
        raise ValidationError("invalid CPU limit")
    if not isinstance(bds["memory_mb"], int) or not 512 <= bds["memory_mb"] <= 16384:
        raise ValidationError("invalid memory limit")
    if "candidate_profile" in bds:
        validate_candidate_profile(bds["candidate_profile"])


def _manifest_version(value: Any) -> None:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(not isinstance(part, int) or not 0 <= part <= 65535 for part in value)
    ):
        raise ValidationError("invalid candidate-profile version")


def _canonical_uuid(value: Any) -> None:
    try:
        canonical = str(uuid.UUID(str(value)))
    except (ValueError, AttributeError) as exc:
        raise ValidationError("invalid candidate-profile UUID") from exc
    if value != canonical:
        raise ValidationError("candidate-profile UUID must be canonical lowercase")


def validate_candidate_profile(profile: Any) -> None:
    if not isinstance(profile, dict):
        raise ValidationError("invalid candidate profile")
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
    _require_keys(profile, required, required)
    if profile["schema_version"] != "crazycraft-bds-candidate-profile-v1":
        raise ValidationError("unsupported candidate profile")
    for role in ("behavior_pack", "resource_pack"):
        value = profile[role]
        pack_required = {"manifest_uuid", "version", "install_directory"}
        if not isinstance(value, dict):
            raise ValidationError(f"invalid candidate-profile {role}")
        _require_keys(value, pack_required, pack_required)
        _canonical_uuid(value["manifest_uuid"])
        _manifest_version(value["version"])
        install = validate_safe_relative_path(value["install_directory"])
        if len(install.parts) != 1:
            raise ValidationError("pack install directory must be one component")
    addon = profile["addon"]
    addon_required = {"behavior_member", "resource_member"}
    if not isinstance(addon, dict):
        raise ValidationError("invalid candidate-profile addon")
    _require_keys(addon, addon_required, addon_required)
    members: list[str] = []
    for field in sorted(addon_required):
        member = validate_safe_relative_path(addon[field])
        if len(member.parts) != 1 or not member.name.endswith(".mcpack"):
            raise ValidationError("invalid candidate-profile addon member")
        members.append(member.name)
    if len(set(members)) != 2:
        raise ValidationError("candidate-profile addon members must be distinct")
    script = profile["script"]
    if script is not None:
        script_required = {"entry_path", "expected_marker"}
        if not isinstance(script, dict):
            raise ValidationError("invalid candidate-profile script")
        _require_keys(script, script_required, script_required)
        validate_safe_relative_path(script["entry_path"])
        marker = script["expected_marker"]
        if marker is not None and (
            not isinstance(marker, str)
            or not marker
            or len(marker) > 200
            or "\n" in marker
            or "\r" in marker
        ):
            raise ValidationError("invalid candidate-profile script marker")
    for field, limit in (
        ("expected_pack_marker", 160),
        ("world_name", 96),
        ("fixture_id", 128),
    ):
        value = profile[field]
        if (
            not isinstance(value, str)
            or not value
            or len(value) > limit
            or "\n" in value
            or "\r" in value
        ):
            raise ValidationError(f"invalid candidate-profile {field}")


def validate_input_manifest(manifest: dict[str, Any], input_root: Path) -> None:
    required = {"schema_version", "job_id", "entries", "manifest_payload_sha256"}
    _require_keys(manifest, required, required)
    if manifest["schema_version"] != PROTOCOL_VERSION:
        raise ValidationError("unsupported input manifest")
    if not JOB_ID_RE.fullmatch(manifest["job_id"]):
        raise ValidationError("invalid manifest job ID")
    if manifest["manifest_payload_sha256"] != payload_hash(
        manifest, "manifest_payload_sha256"
    ):
        raise ValidationError("input manifest payload hash mismatch")
    if not isinstance(manifest["entries"], list) or not manifest["entries"]:
        raise ValidationError("empty input manifest")
    seen: set[str] = set()
    for entry in manifest["entries"]:
        required_entry = {"relative_path", "sha256", "size_bytes", "content_role"}
        _require_keys(entry, required_entry, required_entry)
        rel = str(validate_safe_relative_path(entry["relative_path"]))
        if rel in seen:
            raise ValidationError("duplicate input path")
        seen.add(rel)
        if not SHA256_RE.fullmatch(entry["sha256"]):
            raise ValidationError("invalid input hash")
        path = input_root / rel
        try:
            info = path.lstat()
        except FileNotFoundError as exc:
            raise ValidationError(f"missing input: {rel}") from exc
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValidationError(f"non-regular or linked input: {rel}")
        if info.st_size != entry["size_bytes"] or sha256_file(path) != entry["sha256"]:
            raise ValidationError(f"input authority mismatch: {rel}")


def disclosure_scan(paths: list[Path]) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    for root in paths:
        if not root.exists():
            continue
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in candidates:
            if path.is_symlink():
                raise ValidationError(f"output symlink rejected: {path}")
            if not path.is_file():
                continue
            if path.stat().st_nlink != 1:
                raise ValidationError(f"output hardlink rejected: {path}")
            data = path.read_bytes()
            for marker in PROHIBITED_OUTPUT_MARKERS:
                if marker.lower() in data.lower():
                    matches.append(
                        {"path": str(path), "marker_sha256": sha256_bytes(marker)}
                    )
    return {"status": "PASS" if not matches else "FAIL", "matches": matches}


def inventory_outputs(job_root: Path) -> list[dict[str, Any]]:
    allowed_top = {"result.json", "report.md", "receipt.json", "artifacts"}
    unexpected = sorted(
        path.name
        for path in job_root.iterdir()
        if path.name not in allowed_top
        and path.name
        not in {
            "request.json",
            "request.sha256",
            "input-manifest.json",
            "inputs",
            "logs",
            "status.json",
            "runtime-home",
            "runtime-tmp",
        }
    )
    if unexpected:
        raise ValidationError(f"unexpected job outputs: {unexpected}")
    records: list[dict[str, Any]] = []
    for name in ("result.json", "report.md"):
        path = job_root / name
        if path.exists():
            records.append(
                {
                    "relative_path": name,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    artifacts = job_root / "artifacts"
    if artifacts.exists():
        for path in sorted(artifacts.rglob("*")):
            if path.is_symlink():
                raise ValidationError("artifact symlink rejected")
            if path.is_file():
                if path.stat().st_nlink != 1:
                    raise ValidationError("artifact hardlink rejected")
                records.append(
                    {
                        "relative_path": str(path.relative_to(job_root)),
                        "size_bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
    return records


def ensure_job_root(root: Path) -> None:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name in ("incoming", "active", "completed", "failed", "templates", "runtime"):
        (root / name).mkdir(mode=0o700, exist_ok=True)


def locate_job(root: Path, job_id: str) -> tuple[str, Path] | None:
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValidationError("invalid job ID")
    for state in ("incoming", "active", "completed", "failed"):
        path = root / state / job_id
        if path.exists():
            return state, path
    return None


def reserve_monotonic_job(root: Path, job_id: str, request_sha256: str) -> None:
    sequence = int(job_id.removeprefix("JOB-"))
    lock_path = root / "runtime" / "job-sequence.lock"
    state_path = root / "runtime" / "job-sequence.json"
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if state_path.exists():
            state = json.loads(state_path.read_text())
        else:
            state = {"last_sequence": 0, "events": []}
        expected = state["last_sequence"] + 1
        if sequence != expected:
            raise ValidationError(
                f"non-monotonic job sequence: expected {expected:012d}, observed {sequence:012d}"
            )
        state["last_sequence"] = sequence
        state["events"].append(
            {
                "job_id": job_id,
                "request_sha256": request_sha256,
                "accepted_at": utc_timestamp(),
            }
        )
        write_json(state_path, state)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def atomic_transition(root: Path, job_id: str, source: str, target: str) -> Path:
    source_path = root / source / job_id
    target_path = root / target / job_id
    if not source_path.is_dir() or source_path.is_symlink():
        raise ValidationError("source job directory missing or unsafe")
    if target_path.exists():
        raise ValidationError("target job directory already exists")
    os.replace(source_path, target_path)
    return target_path


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    os.replace(temporary, path)


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def remove_job_scratch(job_root: Path) -> str:
    for name in ("inputs", "logs", "runtime-home", "runtime-tmp"):
        path = job_root / name
        if path.exists():
            shutil.rmtree(path)
    return "SCRATCH_REMOVED"


def verify_worker_environment(env: dict[str, str], forbidden_key_paths: list[Path]) -> None:
    for name in ("SSH_AUTH_SOCK", "CRAZYCRAFT_T1_IDENTITY", "CRAZYCRAFT_T10_IDENTITY"):
        if env.get(name):
            raise ValidationError(f"privileged worker environment inherited: {name}")
    for path in forbidden_key_paths:
        if path.exists() and os.access(path, os.R_OK):
            raise ValidationError(f"worker can read privileged key path: {path}")


def build_bds_docker_create_argv(
    request: dict[str, Any], job_root: Path, docker_executable: str = "docker"
) -> list[str]:
    validate_request(request)
    bds = request["bds"]
    input_root = (job_root / "inputs").resolve()
    request_path = (job_root / "request.json").resolve()
    output_root = (job_root / "artifacts").resolve()
    command = [
        docker_executable,
        "create",
        "--name",
        bds["container_name"],
        "--platform",
        bds["image_platform"],
        "--network",
        "none",
        "--read-only",
        "--user",
        "65532:65532",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "256",
        "--cpus",
        str(bds["cpus"]),
        "--memory",
        f"{bds['memory_mb']}m",
        "--restart",
        "no",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=256m",
        "--tmpfs",
        "/work:rw,exec,nosuid,nodev,size=1024m,uid=65532,gid=65532,mode=0700",
        "--mount",
        f"type=bind,src={input_root},dst=/input,readonly,bind-propagation=rprivate",
        "--mount",
        f"type=bind,src={request_path},dst=/control/request.json,readonly,bind-propagation=rprivate",
        "--mount",
        f"type=bind,src={output_root},dst=/output,bind-propagation=rprivate",
        bds["image_digest"],
    ]
    if bds["fixture_set"] == "REMOTE_BOUNDARY_SYNTHETIC_V1":
        command.extend(
            [
                "python3",
                "-c",
                (
                    "import hashlib,json,pathlib,time;time.sleep(8);"
                    "p=pathlib.Path('/input/candidate.mcaddon');"
                    "o=pathlib.Path('/output/qualification-result.json');"
                    "d=hashlib.sha256(p.read_bytes()).hexdigest();"
                    "o.write_text(json.dumps({"
                    "'schema_version':'crazycraft-remote-v1',"
                    "'job_id':" + repr(request["job_id"]) + ","
                    "'job_type':'BDS_QUALIFICATION',"
                    "'requesting_authority':" + repr(request["requesting_authority"]) + ","
                    "'assignment_id':" + repr(request["assignment_id"]) + ","
                    "'campaign_id':" + repr(request["campaign_id"]) + ","
                    "'outcome':'PASS',"
                    "'abstract_results':[{'qualification':'REMOTE_CONTAINER_ISOLATION_PASS','candidate_sha256':d,'runtime_gate':'NOT_RUN'}],"
                    "'opaque_contract_ids':[],'opaque_finding_ids':[],"
                    "'required_regression_ids':[],"
                    "'qualification_references':['REMOTE-DOCKER-SYNTHETIC-V1'],"
                    "'proof_boundary':'Synthetic remote Docker isolation only; no BDS runtime.',"
                    "'external_gates_not_run':['BDS_RUNTIME','BEDROCK_CLIENT','CONTROLLER','PHYSICAL_PS4','REALM','SPLIT_SCREEN','MARKETPLACE'],"
                    "'disclosure_scan':{'status':'PENDING','matches':[]},"
                    "'result_payload_sha256':''},sort_keys=True,separators=(',',':'))+'\\n')"
                ),
            ]
        )
    else:
        command.extend(
            [
                "/opt/crazycraft/bin/qualify-exact-package",
                "--request",
                "/control/request.json",
                "--output",
                "/output",
            ]
        )
    return command


def build_bds_docker_argv(
    request: dict[str, Any], job_root: Path, docker_executable: str = "docker"
) -> list[str]:
    """Compatibility alias retained for synthetic policy tests."""
    return build_bds_docker_create_argv(request, job_root, docker_executable)
