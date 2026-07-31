#!/usr/bin/env python3
"""Allowlisted Studio-side dispatcher.

The installed forced-command wrapper must set CRAZYCRAFT_REMOTE_ROLE and
CRAZYCRAFT_REMOTE_ROOT. Request fields never become shell commands.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT))

from remote_job_lib import (  # noqa: E402
    PROTOCOL_VERSION,
    ValidationError,
    atomic_transition,
    build_bds_docker_create_argv,
    canonical_bytes,
    disclosure_scan,
    ensure_job_root,
    inventory_outputs,
    payload_hash,
    remove_job_scratch,
    reserve_monotonic_job,
    sha256_file,
    utc_timestamp,
    validate_input_manifest,
    validate_request,
    validate_safe_relative_path,
    write_json,
)


def _result_base(request: dict, outcome: str) -> dict:
    return {
        "schema_version": PROTOCOL_VERSION,
        "job_id": request["job_id"],
        "job_type": request["job_type"],
        "requesting_authority": request["requesting_authority"],
        "assignment_id": request["assignment_id"],
        "campaign_id": request["campaign_id"],
        "outcome": outcome,
        "abstract_results": [],
        "opaque_contract_ids": [],
        "opaque_finding_ids": [],
        "required_regression_ids": [],
        "qualification_references": [],
        "proof_boundary": "Remote job execution only; no undeclared product, client, console, rights, or release gate.",
        "external_gates_not_run": [
            "BEDROCK_CLIENT",
            "CONTROLLER",
            "PHYSICAL_PS4",
            "REALM",
            "SPLIT_SCREEN",
            "MARKETPLACE",
        ],
        "disclosure_scan": {"status": "PASS", "matches": []},
        "result_payload_sha256": "",
    }


def _canonical_bds_result(request: dict, detailed: dict) -> dict:
    outcome = detailed.get("outcome")
    if outcome not in {"PASS", "FAIL", "BLOCKED"}:
        raise ValidationError("qualifier result outcome is not canonical")
    result = _result_base(request, outcome)
    for field in (
        "abstract_results",
        "opaque_contract_ids",
        "opaque_finding_ids",
        "required_regression_ids",
        "qualification_references",
        "external_gates_not_run",
    ):
        value = detailed.get(field)
        if not isinstance(value, list):
            raise ValidationError(f"qualifier result {field} is not canonical")
        result[field] = value
    proof_boundary = detailed.get("proof_boundary")
    if not isinstance(proof_boundary, str) or not proof_boundary:
        raise ValidationError("qualifier result proof boundary is not canonical")
    result["proof_boundary"] = proof_boundary
    result["result_payload_sha256"] = payload_hash(
        result, "result_payload_sha256"
    )
    return result


def _execute_synthetic(request: dict, job_root: Path) -> tuple[dict, str, list[str]]:
    result = _result_base(request, "PASS")
    job_type = request["job_type"]
    if job_type == "EVIDENCE_RECOVERY":
        result["opaque_contract_ids"] = ["CR-SYNTHETIC-001"]
        result["abstract_results"] = [
            {
                "contract_id": "CR-SYNTHETIC-001",
                "state_transition": "UNBOUND -> OWNED -> RECOVERABLE",
                "ownership_rule": "one authoritative owner with revision fencing",
                "restart_rule": "pending mutations reconcile idempotently",
                "multiplayer_constraint": "concurrent claims require compare-and-swap",
            }
        ]
        report = "# Sanitized evidence recovery\n\nSynthetic source-neutral boundary fixture passed.\n"
        session = ["synthetic-evidence-session"]
    elif job_type == "PRIVATE_CANDIDATE_AUDIT":
        result["opaque_contract_ids"] = ["ORACLE-SYNTHETIC-001"]
        result["opaque_finding_ids"] = ["FINDING-SYNTHETIC-001"]
        result["required_regression_ids"] = ["REGRESSION-SYNTHETIC-001"]
        result["abstract_results"] = [
            {
                "finding_id": "FINDING-SYNTHETIC-001",
                "severity": "MEDIUM",
                "defect": "transaction retry can duplicate an externally visible effect",
                "allowed_repair_scope": "idempotency reservation and direct regression only",
            }
        ]
        report = "# Private candidate audit\n\nOne opaque synthetic finding returned.\n"
        session = ["synthetic-audit-session"]
    elif job_type in {"BDS_QUALIFICATION", "COMBINED_PRIVATE_AUDIT_AND_QUALIFICATION"}:
        argv = build_bds_docker_create_argv(request, job_root)
        result["qualification_references"] = ["BDS-SYNTHETIC-POLICY-ONLY"]
        result["abstract_results"] = [
            {
                "qualification": "CONTAINER_POLICY_CONSTRUCTION_PASS",
                "container_name": request["bds"]["container_name"],
                "port": request["bds"]["port"],
                "docker_argv_sha256": __import__("hashlib").sha256(
                    canonical_bytes(argv)
                ).hexdigest(),
                "runtime_gate": "NOT_RUN",
            }
        ]
        report = "# BDS qualification\n\nSynthetic container-policy fixture only; BDS was not run.\n"
        session = []
    else:
        raise ValidationError("unreachable job type")
    result["result_payload_sha256"] = payload_hash(result, "result_payload_sha256")
    return result, report, session


def _docker(
    argv: list[str], timeout: int = 60, check: bool = False
) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        argv,
        check=False,
        timeout=timeout,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
    )
    if check and completed.returncode != 0:
        raise ValidationError(
            f"Docker command failed ({completed.returncode}): {completed.stdout[-1000:]}"
        )
    return completed


def _execute_bds_live(
    request: dict, job_root: Path
) -> tuple[dict, str, list[str], list[str]]:
    docker = "/usr/local/bin/docker"
    bds = request["bds"]
    expected = {
        bds["behavior_pack_path"]: (
            bds["behavior_pack_size"],
            bds["behavior_pack_sha256"],
        ),
        bds["resource_pack_path"]: (
            bds["resource_pack_size"],
            bds["resource_pack_sha256"],
        ),
        bds["mcaddon_path"]: (bds["mcaddon_size"], bds["mcaddon_sha256"]),
    }
    observed = {
        path.relative_to(job_root / "inputs").as_posix()
        for path in (job_root / "inputs").rglob("*")
        if path.is_file()
    }
    if observed != set(expected):
        raise ValidationError(f"exact BDS input set mismatch: {sorted(observed)}")
    for name, (expected_size, expected_hash) in expected.items():
        candidate = job_root / "inputs" / name
        if (
            not candidate.is_file()
            or candidate.stat().st_size != expected_size
            or sha256_file(candidate) != expected_hash
        ):
            raise ValidationError(f"exact BDS input mismatch: {name}")
    image = _docker(
        [
            docker,
            "image",
            "inspect",
            bds["image_digest"],
            "--format",
            "{{.Id}}\t{{.Os}}/{{.Architecture}}",
        ],
        check=True,
    ).stdout.strip()
    expected_id = "sha256:" + bds["image_digest"].rsplit("@sha256:", 1)[1]
    if image != f"{expected_id}\t{bds['image_platform']}":
        raise ValidationError(f"qualifier image authority mismatch: {image}")
    output_root = job_root / "artifacts"
    if any(output_root.iterdir()):
        raise ValidationError("qualification output directory must begin empty")
    # Job-local write-only access for the fixed nonroot container user. The
    # Studio owner retains read/control access and restores 0700 immediately.
    os.chmod(output_root, 0o733)
    create_argv = build_bds_docker_create_argv(request, job_root, docker)
    created = _docker(create_argv, check=True)
    container_id = created.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise ValidationError("Docker create omitted canonical container ID")
    verifier = job_root / "logs" / "embedded-qualifier"
    try:
        _docker(
            [
                docker,
                "cp",
                f"{container_id}:/opt/crazycraft/bin/qualify-exact-package",
                str(verifier),
            ],
            check=True,
        )
        if sha256_file(verifier) != bds["qualifier_sha256"] or not os.access(
            verifier, os.X_OK
        ):
            raise ValidationError("embedded qualifier content or mode mismatch")
        started = _docker(
            [docker, "start", "-a", container_id],
            timeout=request["timeout_seconds"],
        )
        (job_root / "logs" / "docker-console.log").write_text(started.stdout)
        inspect = _docker(
            [
                docker,
                "inspect",
                container_id,
                "--format",
                "{{.State.ExitCode}}\t{{.State.OOMKilled}}\t{{.State.Error}}",
            ],
            check=True,
        ).stdout.strip()
        os.chmod(output_root, 0o700)
        result_path = job_root / "artifacts" / "qualification-result.json"
        if not result_path.is_file():
            raise ValidationError(
                f"BDS qualifier omitted result (container={inspect}): {started.stdout[-1000:]}"
            )
        result = json.loads(result_path.read_text())
        if result.get("result_payload_sha256") != payload_hash(
            result, "result_payload_sha256"
        ):
            raise ValidationError("qualifier result payload hash mismatch")
        if started.returncode not in {0, 2}:
            raise ValidationError(
                f"BDS qualifier infrastructure exit {started.returncode}: {started.stdout[-1000:]}"
            )
        for name, (expected_size, expected_hash) in expected.items():
            candidate = job_root / "inputs" / name
            if (
                candidate.stat().st_size != expected_size
                or sha256_file(candidate) != expected_hash
            ):
                raise ValidationError(f"candidate mutated during qualification: {name}")
        return (
            _canonical_bds_result(request, result),
            "# BDS qualification\n\nSee exact-package result, logs, and receipts.\n",
            [],
            [container_id],
        )
    finally:
        os.chmod(output_root, 0o700)
        _docker([docker, "stop", "--time", "10", container_id], timeout=30)
        _docker([docker, "rm", "-f", container_id], timeout=30)
        absent = _docker(
            [docker, "inspect", container_id],
            timeout=10,
        )
        if absent.returncode == 0:
            raise ValidationError("qualification container cleanup failed")


def _execute_live(
    request: dict, job_root: Path
) -> tuple[dict, str, list[str], list[str]]:
    job_type = request["job_type"]
    if job_type in {"EVIDENCE_RECOVERY", "PRIVATE_CANDIDATE_AUDIT"}:
        runner = Path(__file__).resolve().with_name(
            "crazycraft_studio_codex_runner.py"
        )
        if not runner.is_file() or not os.access(runner, os.X_OK):
            raise ValidationError("allowlisted Studio Codex runner unavailable")
        completed = subprocess.run(
            [
                str(runner),
                "--job-root",
                str(job_root),
                "--job-type",
                job_type,
            ],
            check=False,
            timeout=request["timeout_seconds"],
            env={
                "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                "HOME": str(job_root / "runtime-home"),
                "TMPDIR": str(job_root / "runtime-tmp"),
                "CODEX_HOME": os.environ.get(
                    "CRAZYCRAFT_CODEX_HOME", "/Users/blakestudio/.codex"
                ),
            },
        )
        if completed.returncode != 0:
            raise ValidationError(f"Studio Codex runner failed: {completed.returncode}")
        result_path = job_root / "result.json"
        report_path = job_root / "report.md"
        if not result_path.is_file() or not report_path.is_file():
            raise ValidationError("Studio Codex runner omitted result files")
        result = json.loads(result_path.read_text())
        if result.get("result_payload_sha256") != payload_hash(
            result, "result_payload_sha256"
        ):
            raise ValidationError("Studio Codex result hash mismatch")
        return (
            result,
            report_path.read_text(),
            [result.get("codex_session_identifier", "")],
            [],
        )
    if job_type in {"BDS_QUALIFICATION", "COMBINED_PRIVATE_AUDIT_AND_QUALIFICATION"}:
        if job_type == "COMBINED_PRIVATE_AUDIT_AND_QUALIFICATION":
            raise ValidationError(
                "combined private audit is not implemented; submit isolated jobs"
            )
        return _execute_bds_live(request, job_root)
    raise ValidationError("unreachable job type")


def process_job(root: Path, role: str, job_id: str, synthetic: bool = False) -> int:
    ensure_job_root(root)
    active = atomic_transition(root, job_id, "incoming", "active")
    started = utc_timestamp()
    request: dict = {}
    input_manifest: dict = {}
    exit_status = 1
    container_ids: list[str] = []
    codex_sessions: list[str] = []
    try:
        request_path = active / "request.json"
        request_sha_path = active / "request.sha256"
        manifest_path = active / "input-manifest.json"
        if not all(path.is_file() for path in (request_path, request_sha_path, manifest_path)):
            raise ValidationError("job request files missing")
        request = json.loads(request_path.read_text())
        validate_request(request, expected_role=role)
        if request["job_id"] != job_id:
            raise ValidationError("job directory/request mismatch")
        if request_sha_path.read_text().strip() != sha256_file(request_path):
            raise ValidationError("request file hash mismatch")
        reserve_monotonic_job(root, job_id, sha256_file(request_path))
        input_manifest = json.loads(manifest_path.read_text())
        if input_manifest.get("job_id") != job_id:
            raise ValidationError("manifest job mismatch")
        validate_input_manifest(input_manifest, active / "inputs")
        (active / "artifacts").mkdir(mode=0o700, exist_ok=True)
        (active / "logs").mkdir(mode=0o700, exist_ok=True)
        (active / "runtime-home").mkdir(mode=0o700, exist_ok=True)
        (active / "runtime-tmp").mkdir(mode=0o700, exist_ok=True)
        if synthetic:
            result, report, codex_sessions = _execute_synthetic(request, active)
        else:
            result, report, codex_sessions, container_ids = _execute_live(
                request, active
            )
        write_json(active / "result.json", result)
        (active / "report.md").write_text(report)
        scan = disclosure_scan([active / "result.json", active / "report.md", active / "artifacts"])
        if scan["status"] != "PASS":
            raise ValidationError("disclosure policy scan failed")
        result["disclosure_scan"] = scan
        result["result_payload_sha256"] = payload_hash(result, "result_payload_sha256")
        write_json(active / "result.json", result)
        exit_status = 0
        terminal = "completed"
    except Exception as exc:
        error_result = _result_base(
            request
            if request
            else {
                "job_id": job_id,
                "job_type": "UNKNOWN",
                "requesting_authority": role,
                "assignment_id": "UNKNOWN",
                "campaign_id": "UNKNOWN",
            },
            "FAIL",
        )
        error_result["abstract_results"] = [
            {"error_class": type(exc).__name__, "error": str(exc)}
        ]
        error_result["result_payload_sha256"] = payload_hash(
            error_result, "result_payload_sha256"
        )
        write_json(active / "result.json", error_result)
        (active / "report.md").write_text(
            f"# Remote job failed\n\n{type(exc).__name__}: {exc}\n"
        )
        scan = disclosure_scan([active / "result.json", active / "report.md"])
        terminal = "failed"
    ended = utc_timestamp()
    outputs = inventory_outputs(active)
    cleanup_status = remove_job_scratch(active)
    if container_ids:
        cleanup_status = "SCRATCH_REMOVED_AND_CONTAINERS_VERIFIED_ABSENT"
    receipt = {
        "schema_version": PROTOCOL_VERSION,
        "job_id": job_id,
        "request_sha256": sha256_file(active / "request.json")
        if (active / "request.json").is_file()
        else "0" * 64,
        "input_manifest_sha256": sha256_file(active / "input-manifest.json")
        if (active / "input-manifest.json").is_file()
        else "0" * 64,
        "requesting_authority": role,
        "studio_host_identity": socket.gethostname(),
        "studio_executor_identity": f"crazycraft-{role.lower()}-remote",
        "job_type": request.get("job_type", "UNKNOWN"),
        "started_at": started,
        "ended_at": ended,
        "entrypoint": ["remote_job_entrypoint.py", "activate", role, job_id],
        "evidence_roots_accessed": request.get("permitted_evidence_roots", []),
        "candidate_inputs_accessed": request.get("permitted_candidate_paths", []),
        "outputs": outputs,
        "disclosure_policy_scan": scan,
        "exit_status": exit_status,
        "cleanup_status": cleanup_status,
        "docker_container_ids": container_ids,
        "codex_session_identifier": next(
            (value for value in codex_sessions if value), None
        ),
        "authority_envelope": {
            "scheme": "SHA256_CANONICAL_JSON_LOCAL_ENVELOPE",
            "identity": f"crazycraft-{role.lower()}-remote",
            "payload_sha256": "",
            "verification": "TAMPER_EVIDENT_ONLY",
        },
        "proof_boundary": "Job-local execution and disclosure scan only; host/account separation requires independent authority.",
        "receipt_payload_sha256": "",
    }
    envelope_copy = dict(receipt)
    envelope_copy["authority_envelope"] = dict(receipt["authority_envelope"])
    envelope_copy["authority_envelope"]["payload_sha256"] = ""
    envelope_copy["receipt_payload_sha256"] = ""
    receipt["authority_envelope"]["payload_sha256"] = __import__("hashlib").sha256(
        canonical_bytes(envelope_copy)
    ).hexdigest()
    receipt["receipt_payload_sha256"] = payload_hash(
        receipt, "receipt_payload_sha256"
    )
    write_json(active / "receipt.json", receipt)
    write_json(
        active / "status.json",
        {
            "job_id": job_id,
            "state": terminal.upper(),
            "exit_status": exit_status,
            "updated_at": ended,
        },
    )
    atomic_transition(root, job_id, "active", terminal)
    return exit_status


def inspect_job(root: Path, job_id: str) -> int:
    from remote_job_lib import locate_job

    found = locate_job(root, job_id)
    if not found:
        print(json.dumps({"job_id": job_id, "state": "NOT_FOUND"}))
        return 1
    state, path = found
    status = path / "status.json"
    if status.is_file():
        print(status.read_text(), end="")
    else:
        print(json.dumps({"job_id": job_id, "state": state.upper()}))
    return 0


def ingest_job(root: Path, role: str, job_id: str) -> int:
    from remote_job_lib import locate_job

    ensure_job_root(root)
    if locate_job(root, job_id):
        raise ValidationError("duplicate job ID")
    encoded = sys.stdin.buffer.read(1024 * 1024 * 1024 + 1)
    if len(encoded) > 1024 * 1024 * 1024:
        raise ValidationError("transfer exceeds one GiB limit")
    payload = json.loads(encoded.decode("ascii"))
    required = {
        "job_id",
        "request_json_base64",
        "request_sha256_base64",
        "input_manifest_base64",
        "inputs",
    }
    if set(payload) != required or payload["job_id"] != job_id:
        raise ValidationError("transfer framing mismatch")
    destination = root / "incoming" / job_id
    destination.mkdir(mode=0o700)
    try:
        (destination / "inputs").mkdir(mode=0o700)
        fixed = {
            "request.json": payload["request_json_base64"],
            "request.sha256": payload["request_sha256_base64"],
            "input-manifest.json": payload["input_manifest_base64"],
        }
        for name, value in fixed.items():
            data = base64.b64decode(value, validate=True)
            descriptor = os.open(
                destination / name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o400,
            )
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
        request = json.loads((destination / "request.json").read_text())
        validate_request(request, expected_role=role)
        manifest = json.loads((destination / "input-manifest.json").read_text())
        expected_paths = {entry["relative_path"] for entry in manifest["entries"]}
        observed_paths = {entry["relative_path"] for entry in payload["inputs"]}
        if expected_paths != observed_paths:
            raise ValidationError("transfer inputs do not match manifest")
        for entry in payload["inputs"]:
            rel = validate_safe_relative_path(entry["relative_path"])
            path = destination / "inputs" / rel
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            data = base64.b64decode(entry["content_base64"], validate=True)
            descriptor = os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o400,
            )
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
        validate_input_manifest(manifest, destination / "inputs")
    except Exception:
        import shutil

        shutil.rmtree(destination, ignore_errors=True)
        raise
    return 0


def fetch_job(root: Path, role: str, job_id: str, failed: bool = False) -> int:
    state = "failed" if failed else "completed"
    source = root / state / job_id
    if not source.is_dir() or source.is_symlink():
        raise ValidationError(f"{state} job not found")
    request = json.loads((source / "request.json").read_text())
    validate_request(request, expected_role=role)
    allowed = ["result.json", "report.md", "receipt.json", "status.json"]
    files = []
    for name in allowed:
        path = source / name
        if path.is_file():
            files.append(
                {
                    "relative_path": name,
                    "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
                }
            )
    artifacts = source / "artifacts"
    if artifacts.is_dir():
        for path in sorted(artifacts.rglob("*")):
            if path.is_symlink() or (path.is_file() and path.stat().st_nlink != 1):
                raise ValidationError("unsafe artifact in retrieval")
            if path.is_file():
                files.append(
                    {
                        "relative_path": str(path.relative_to(source)),
                        "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
                    }
                )
    if disclosure_scan(
        [source / name for name in allowed if (source / name).exists()] + [artifacts]
    )["status"] != "PASS":
        raise ValidationError("remote result disclosure scan failed")
    sys.stdout.write(
        json.dumps(
            {"job_id": job_id, "state": state.upper(), "files": files},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


def cleanup_job(root: Path, role: str, job_id: str) -> int:
    from remote_job_lib import locate_job

    found = locate_job(root, job_id)
    if not found:
        return 0
    state, path = found
    if state in {"incoming", "active"}:
        raise ValidationError("cannot cleanup nonterminal job")
    request = json.loads((path / "request.json").read_text())
    validate_request(request, expected_role=role)
    artifacts = path / "artifacts"
    if artifacts.exists():
        import shutil

        shutil.rmtree(artifacts)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        choices=("ingest", "activate", "status", "fetch", "fetch-failure", "cleanup"),
    )
    parser.add_argument("role", choices=("T1", "T10"))
    parser.add_argument("job_id")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("CRAZYCRAFT_REMOTE_ROOT", "~/crazycraft-remote-jobs")).expanduser(),
    )
    parser.add_argument("--synthetic-test", action="store_true")
    args = parser.parse_args()
    configured_role = os.environ.get("CRAZYCRAFT_REMOTE_ROLE")
    if configured_role and configured_role != args.role:
        raise ValidationError("executor role mismatch")
    if args.operation == "status":
        return inspect_job(args.root, args.job_id)
    if args.operation == "ingest":
        return ingest_job(args.root, args.role, args.job_id)
    if args.operation in {"fetch", "fetch-failure"}:
        return fetch_job(
            args.root, args.role, args.job_id, failed=args.operation == "fetch-failure"
        )
    if args.operation == "cleanup":
        return cleanup_job(args.root, args.role, args.job_id)
    return process_job(args.root, args.role, args.job_id, synthetic=args.synthetic_test)


if __name__ == "__main__":
    raise SystemExit(main())
