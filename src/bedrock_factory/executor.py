from __future__ import annotations

import hashlib
import json
import os
import signal
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Callable


class ExecutionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        receipt_path: str | None = None,
        receipt_sha256: str | None = None,
    ):
        super().__init__(message)
        self.receipt_path = receipt_path
        self.receipt_sha256 = receipt_sha256


def file_sha256(
    path: Path,
    heartbeat: Callable[[], None] | None = None,
) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            if heartbeat is not None:
                heartbeat()
    return digest.hexdigest()


def tree_sha256(
    root: Path,
    heartbeat: Callable[[], None] | None = None,
) -> str:
    if root.is_file():
        return file_sha256(root, heartbeat)
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ExecutionError(f"symlinks are not transferable: {path}")
        if path.is_dir():
            digest.update(f"D:{relative}\0".encode())
            continue
        digest.update(f"F:{relative}\0".encode())
        digest.update(file_sha256(path, heartbeat).encode())
        digest.update(b"\0")
    return digest.hexdigest()


def artifact_record(
    path: str | Path,
    heartbeat: Callable[[], None] | None = None,
) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise ExecutionError(f"artifact does not exist: {resolved}")
    return {
        "path": str(resolved),
        "kind": "directory" if resolved.is_dir() else "file",
        "sha256": tree_sha256(resolved, heartbeat),
        "size": (
            sum(item.stat().st_size for item in resolved.rglob("*") if item.is_file())
            if resolved.is_dir()
            else resolved.stat().st_size
        ),
    }


def _within(path: Path, roots: list[str]) -> bool:
    return any(
        path == Path(root).expanduser().resolve()
        or Path(root).expanduser().resolve() in path.parents
        for root in roots
    )


def _check_path_policy(path: Path, roots: list[str] | None, purpose: str) -> None:
    if roots is not None and not _within(path, roots):
        raise ExecutionError(f"{purpose} path is outside its allowed roots: {path}")


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)
    return file_sha256(path)


class JobExecutor:
    def __init__(self, runtime_root: str | Path):
        self.runtime_root = Path(runtime_root).expanduser().resolve()
        self.runtime_root.mkdir(parents=True, exist_ok=True)

    def execute(
        self,
        job: dict[str, Any],
        *,
        worker_id: str,
        heartbeat: Callable[[], None],
    ) -> tuple[dict[str, Any], str, str]:
        started_at = time.time()
        receipt: dict[str, Any] = {
            "schema_version": "1.0.0",
            "receipt_id": f"receipt-{uuid.uuid4().hex}",
            "campaign_id": job["campaign_id"],
            "job_id": job["id"],
            "idempotency_key": job["idempotency_key"],
            "attempt": job["attempt_count"],
            "worker_id": worker_id,
            "stage": job["stage"],
            "lane": job["lane"],
            "kind": job["kind"],
            "started_at": started_at,
        }
        receipt_dir = self.runtime_root / "receipts" / job["campaign_id"]
        receipt_path = receipt_dir / f"{job['id']}-attempt-{job['attempt_count']}.json"
        try:
            if job["kind"] == "command":
                result = self._execute_command(job, receipt, heartbeat)
            elif job["kind"] == "transfer":
                result = self._execute_transfer(job, receipt, heartbeat)
            else:
                raise ExecutionError(f"unsupported executable job kind: {job['kind']}")
            receipt["status"] = "SUCCEEDED"
            receipt["result"] = result
        except Exception as exc:
            receipt["status"] = "FAILED"
            receipt["error"] = f"{type(exc).__name__}: {exc}"
            receipt["ended_at"] = time.time()
            receipt_hash = _write_json_atomic(receipt_path, receipt)
            if isinstance(exc, ExecutionError):
                raise ExecutionError(
                    str(exc),
                    receipt_path=str(receipt_path),
                    receipt_sha256=receipt_hash,
                ) from exc
            raise ExecutionError(
                str(exc),
                receipt_path=str(receipt_path),
                receipt_sha256=receipt_hash,
            ) from exc
        receipt["ended_at"] = time.time()
        receipt_hash = _write_json_atomic(receipt_path, receipt)
        return result, str(receipt_path), receipt_hash

    @staticmethod
    def _terminate_process_group(process: subprocess.Popen[Any]) -> None:
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            process.terminate()
        try:
            process.wait(timeout=10)
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            process.kill()
        process.wait()

    @staticmethod
    def _verify_inputs(
        payload: dict[str, Any],
        heartbeat: Callable[[], None],
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        allowed = payload.get("allowed_read_roots")
        for expected in payload.get("input_artifacts", []):
            path = Path(expected["path"]).expanduser().resolve()
            _check_path_policy(path, allowed, "input")
            record = artifact_record(path, heartbeat)
            if record["sha256"] != expected["sha256"]:
                raise ExecutionError(
                    f"input hash mismatch for {path}: "
                    f"expected {expected['sha256']}, got {record['sha256']}"
                )
            records.append(record)
        return records

    @staticmethod
    def _verify_outputs(
        payload: dict[str, Any],
        heartbeat: Callable[[], None],
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        allowed = payload.get("allowed_write_roots")
        for expected in payload.get("expected_outputs", []):
            path = Path(expected["path"]).expanduser().resolve()
            _check_path_policy(path, allowed, "output")
            if not path.exists() and not expected.get("required", True):
                continue
            record = artifact_record(path, heartbeat)
            expected_hash = expected.get("sha256")
            if expected_hash is not None and record["sha256"] != expected_hash:
                raise ExecutionError(
                    f"output hash mismatch for {path}: "
                    f"expected {expected_hash}, got {record['sha256']}"
                )
            records.append(record)
        return records

    def _execute_command(
        self,
        job: dict[str, Any],
        receipt: dict[str, Any],
        heartbeat: Callable[[], None],
    ) -> dict[str, Any]:
        payload = job["payload"]
        if job["lane"] in {"PRODUCTION", "INTEGRATION"}:
            if not isinstance(payload.get("sandbox_profile"), dict):
                raise ExecutionError(
                    "production and integration commands require a hash-bound sandbox profile"
                )
            if payload.get("activation_attestation_required") is not True:
                raise ExecutionError(
                    "production and integration commands require a minimal activation attestation"
                )
        argv = payload.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(part, str) and part for part in argv)
        ):
            raise ExecutionError("command payload requires a non-empty argv string array")
        cwd = Path(payload.get("cwd", ".")).expanduser().resolve()
        _check_path_policy(cwd, payload.get("allowed_read_roots"), "cwd")
        if not cwd.is_dir():
            raise ExecutionError(f"command cwd is not a directory: {cwd}")
        input_records = self._verify_inputs(payload, heartbeat)
        sandbox_profile = payload.get("sandbox_profile")
        if sandbox_profile is not None:
            if sandbox_profile.get("mode") == "generated_by_launcher":
                profile_path = Path(
                    sandbox_profile["launcher_path"]
                ).expanduser().resolve()
                expected_profile_hash = sandbox_profile["launcher_sha256"]
                profile_label = "sandbox launcher"
            else:
                profile_path = Path(sandbox_profile["path"]).expanduser().resolve()
                expected_profile_hash = sandbox_profile["sha256"]
                profile_label = "sandbox profile"
            _check_path_policy(
                profile_path,
                payload.get("allowed_read_roots"),
                profile_label,
            )
            profile_record = artifact_record(profile_path, heartbeat)
            if profile_record["sha256"] != expected_profile_hash:
                raise ExecutionError(
                    f"{profile_label} hash mismatch for {profile_path}: "
                    f"expected {expected_profile_hash}, "
                    f"got {profile_record['sha256']}"
                )
            input_records.append(profile_record)
        log_dir = self.runtime_root / "logs" / job["campaign_id"]
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = log_dir / f"{job['id']}-attempt-{job['attempt_count']}.stdout.log"
        stderr_path = log_dir / f"{job['id']}-attempt-{job['attempt_count']}.stderr.log"
        environment = os.environ.copy()
        for key, value in payload.get("env", {}).items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ExecutionError("command env must be a string-to-string object")
            environment[key] = value
        timeout = float(payload.get("timeout_seconds", 3600))
        receipt.update(
            {
                "argv": argv,
                "cwd": str(cwd),
                "input_artifacts": input_records,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "timeout_seconds": timeout,
            }
        )
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                shell=False,
                start_new_session=True,
            )
            receipt["pid"] = process.pid
            deadline = time.monotonic() + timeout
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    self._terminate_process_group(process)
                    raise ExecutionError(f"command timed out after {timeout} seconds")
                heartbeat()
                time.sleep(0.2)
            exit_code = process.returncode
        receipt["exit_code"] = exit_code
        if exit_code != 0:
            raise ExecutionError(f"command exited with status {exit_code}")
        outputs = self._verify_outputs(payload, heartbeat)
        receipt["output_artifacts"] = outputs
        activation_attestation_record = self._record_activation_attestation(
            payload,
            receipt=receipt,
            heartbeat=heartbeat,
        )
        return {
            "exit_code": exit_code,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "output_artifacts": outputs,
            "activation_attestation": activation_attestation_record,
        }

    @staticmethod
    def _record_activation_attestation(
        payload: dict[str, Any],
        *,
        receipt: dict[str, Any],
        heartbeat: Callable[[], None],
    ) -> dict[str, Any] | None:
        required = payload.get("activation_attestation_required", False)
        specification = payload.get("activation_attestation")
        if not required and specification is None:
            return None
        if not isinstance(specification, dict):
            raise ExecutionError("activation attestation specification is required")
        path = Path(specification["path"]).expanduser().resolve()
        _check_path_policy(
            path,
            payload.get("allowed_write_roots"),
            "activation attestation",
        )
        if path.stat().st_size > 8192:
            raise ExecutionError("activation attestation exceeds 8192 bytes")
        record = artifact_record(path, heartbeat)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExecutionError("activation attestation must be valid JSON") from exc
        required_fields = {
            "schema_version",
            "activation_id",
            "assignment_sha256",
            "platform_qualification_sha256",
            "repository_ref",
            "exit_code",
            "cleanup_status",
        }
        allowed_fields = required_fields | {"candidate_id", "candidate_sha256", "stop_code"}
        if set(document) - allowed_fields or not required_fields.issubset(document):
            raise ExecutionError("activation attestation fields are not minimal v1")
        if document.get("schema_version") != "bedrock-factory.activation-attestation.v1.0.0":
            raise ExecutionError("activation attestation schema rejected")
        if not isinstance(document.get("exit_code"), int):
            raise ExecutionError("activation attestation exit_code is invalid")
        if document.get("cleanup_status") not in {"PASS", "FAIL"}:
            raise ExecutionError("activation attestation cleanup_status is invalid")
        receipt["activation_attestation_recorded"] = record
        return record

    @staticmethod
    def _copy_with_heartbeats(
        source: Path,
        destination: Path,
        heartbeat: Callable[[], None],
    ) -> None:
        def copy_file(source_file: Path, destination_file: Path) -> None:
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            with source_file.open("rb") as reader, destination_file.open("xb") as writer:
                for block in iter(lambda: reader.read(1024 * 1024), b""):
                    writer.write(block)
                    heartbeat()
            shutil.copystat(source_file, destination_file, follow_symlinks=False)

        if source.is_file():
            copy_file(source, destination)
            return
        destination.mkdir(parents=True)
        directories = [source]
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ExecutionError(f"symlinks are not transferable: {path}")
            target = destination / path.relative_to(source)
            if path.is_dir():
                target.mkdir()
                directories.append(path)
            elif path.is_file():
                copy_file(path, target)
            else:
                raise ExecutionError(f"unsupported transfer object: {path}")
        for directory in reversed(directories):
            target = (
                destination
                if directory == source
                else destination / directory.relative_to(source)
            )
            shutil.copystat(directory, target, follow_symlinks=False)
            heartbeat()

    def _execute_transfer(
        self,
        job: dict[str, Any],
        receipt: dict[str, Any],
        heartbeat: Callable[[], None],
    ) -> dict[str, Any]:
        payload = job["payload"]
        if payload.get("transport", "local") != "local":
            raise ExecutionError(
                "only the verified local transport is enabled; use a command job "
                "with a receipt-bound transport adapter for remote hosts"
            )
        source = Path(payload["source"]).expanduser().resolve()
        destination = Path(payload["destination"]).expanduser().resolve()
        _check_path_policy(source, payload.get("allowed_read_roots"), "source")
        _check_path_policy(
            destination,
            payload.get("allowed_write_roots"),
            "destination",
        )
        source_record = artifact_record(source, heartbeat)
        expected_hash = payload.get("sha256")
        if not expected_hash:
            raise ExecutionError("transfer payload requires an exact sha256")
        if source_record["sha256"] != expected_hash:
            raise ExecutionError(
                f"source hash mismatch: expected {expected_hash}, "
                f"got {source_record['sha256']}"
            )
        if destination.exists():
            destination_record = artifact_record(destination, heartbeat)
            if destination_record["sha256"] == expected_hash:
                return {
                    "idempotent": True,
                    "source": source_record,
                    "destination": destination_record,
                }
            raise ExecutionError(
                f"destination already exists with different bytes: {destination}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        incoming_root = destination.parent / ".mccompiler-incoming"
        incoming_root.mkdir(parents=True, exist_ok=True)
        staging = incoming_root / f"{job['id']}-{uuid.uuid4().hex}"
        heartbeat()
        self._copy_with_heartbeats(source, staging, heartbeat)
        heartbeat()
        staging_record = artifact_record(staging, heartbeat)
        if staging_record["sha256"] != expected_hash:
            raise ExecutionError(
                f"staging hash mismatch: expected {expected_hash}, "
                f"got {staging_record['sha256']}"
            )
        os.replace(staging, destination)
        destination_record = artifact_record(destination, heartbeat)
        receipt["source_artifact"] = source_record
        receipt["destination_artifact"] = destination_record
        return {
            "idempotent": False,
            "source": source_record,
            "destination": destination_record,
        }
