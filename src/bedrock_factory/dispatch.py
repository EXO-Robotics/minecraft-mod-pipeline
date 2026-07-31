from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
LANES = {"EVIDENCE", "CONTROL", "PRODUCTION", "INTEGRATION", "AUDIT", "QUALIFICATION"}
STATES = {"PENDING_SEND", "SENT", "ACKNOWLEDGED", "FAILED", "SUPERSEDED"}


class DispatchError(ValueError):
    pass


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(canonical_bytes(value) + b"\n")
    os.replace(temporary, path)


def validate_dispatch_record(record: dict[str, Any], *, verify_files: bool = True) -> None:
    required = {
        "schema_version",
        "request_id",
        "campaign_id",
        "assignment_id",
        "role",
        "skill",
        "lane",
        "assignment_path",
        "assignment_sha256",
        "activation_path",
        "activation_sha256",
        "prompt",
        "state",
        "created_at",
        "supersedes_request_id",
    }
    missing = sorted(required - record.keys())
    if missing:
        raise DispatchError(f"dispatch record missing fields: {missing}")
    if record["schema_version"] != "studio-thread-dispatch-v1":
        raise DispatchError("dispatch schema version rejected")
    if record["lane"] not in LANES:
        raise DispatchError("dispatch lane rejected")
    if record["state"] not in STATES:
        raise DispatchError("dispatch state rejected")
    if not all(
        isinstance(record[field], str) and record[field]
        for field in ("request_id", "campaign_id", "assignment_id", "role", "skill", "prompt")
    ):
        raise DispatchError("dispatch identity fields must be non-empty strings")
    for path_field, hash_field in (
        ("assignment_path", "assignment_sha256"),
        ("activation_path", "activation_sha256"),
    ):
        path = Path(record[path_field]).expanduser()
        if not path.is_absolute():
            raise DispatchError(f"{path_field} must be absolute")
        expected = record[hash_field]
        if not isinstance(expected, str) or not SHA256.fullmatch(expected):
            raise DispatchError(f"{hash_field} must be lowercase SHA-256")
        if verify_files:
            if not path.is_file():
                raise DispatchError(f"dispatch input missing: {path}")
            observed = file_sha256(path)
            if observed != expected:
                raise DispatchError(
                    f"dispatch input hash mismatch: {path}: expected={expected} observed={observed}"
                )


class ThreadDispatchOutbox:
    """Durable outbox consumed by the conversation-facing overseer task.

    The outbox does not create a UI or assume a specific Codex transport. The
    overseer may spawn a local subagent, a Codex task, or a fixed CLI worker,
    then acknowledge the exact request only after delivery succeeds.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.pending_root = self.root / "pending"
        self.history_root = self.root / "history"

    def enqueue(
        self,
        *,
        campaign_id: str,
        assignment_id: str,
        role: str,
        skill: str,
        lane: str,
        assignment_path: str | Path,
        activation_path: str | Path,
        supersedes_request_id: str | None = None,
    ) -> dict[str, Any]:
        assignment = Path(assignment_path).expanduser().resolve()
        activation = Path(activation_path).expanduser().resolve()
        if not assignment.is_file() or not activation.is_file():
            raise DispatchError("assignment and activation must exist before dispatch")
        identity = {
            "campaign_id": campaign_id,
            "assignment_id": assignment_id,
            "role": role,
            "skill": skill,
            "lane": lane,
            "assignment_sha256": file_sha256(assignment),
            "activation_sha256": file_sha256(activation),
            "supersedes_request_id": supersedes_request_id,
        }
        request_id = hashlib.sha256(canonical_bytes(identity)).hexdigest()
        path = self.pending_root / f"{request_id}.json"
        history_path = self.history_root / f"{request_id}.json"
        if history_path.exists():
            existing = json.loads(history_path.read_text(encoding="utf-8"))
            validate_dispatch_record(existing)
            return existing
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            validate_dispatch_record(existing)
            return existing
        prompt = f"Use ${skill} with the assignment packet at {assignment}. Activation authority: {activation}."
        record: dict[str, Any] = {
            "schema_version": "studio-thread-dispatch-v1",
            "request_id": request_id,
            "campaign_id": campaign_id,
            "assignment_id": assignment_id,
            "role": role,
            "skill": skill,
            "lane": lane,
            "assignment_path": str(assignment),
            "assignment_sha256": identity["assignment_sha256"],
            "activation_path": str(activation),
            "activation_sha256": identity["activation_sha256"],
            "prompt": prompt,
            "state": "PENDING_SEND",
            "created_at": utc_now(),
            "supersedes_request_id": supersedes_request_id,
        }
        validate_dispatch_record(record)
        _atomic_json(path, record)
        return record

    def pending(self) -> list[dict[str, Any]]:
        if not self.pending_root.exists():
            return []
        records: list[dict[str, Any]] = []
        for path in sorted(self.pending_root.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            validate_dispatch_record(record)
            if record["state"] == "PENDING_SEND":
                records.append(record)
        return records

    def acknowledge(
        self,
        request_id: str,
        *,
        state: str,
        worker_task_id: str | None = None,
        error_code: str | None = None,
    ) -> dict[str, Any]:
        if state not in {"SENT", "ACKNOWLEDGED", "FAILED", "SUPERSEDED"}:
            raise DispatchError("invalid acknowledgement state")
        source = self.pending_root / f"{request_id}.json"
        if not source.is_file():
            raise DispatchError(f"unknown pending dispatch: {request_id}")
        record = json.loads(source.read_text(encoding="utf-8"))
        validate_dispatch_record(record)
        record["state"] = state
        record["updated_at"] = utc_now()
        record["worker_task_id"] = worker_task_id
        record["error_code"] = error_code
        target = self.history_root / f"{request_id}.json"
        if target.exists():
            existing = json.loads(target.read_text(encoding="utf-8"))
            if canonical_bytes(existing) != canonical_bytes(record):
                raise DispatchError("dispatch acknowledgement already exists with different data")
            return existing
        _atomic_json(target, record)
        source.unlink()
        return record
