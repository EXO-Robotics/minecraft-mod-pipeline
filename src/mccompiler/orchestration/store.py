from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .mailbox import FactoryMailbox, MAILBOX_SCHEMA


WAITING = "WAITING"
AWAITING_APPROVAL = "AWAITING_APPROVAL"
READY = "READY"
RUNNING = "RUNNING"
RETRY_WAIT = "RETRY_WAIT"
SUCCEEDED = "SUCCEEDED"
FAILED = "FAILED"
BLOCKED = "BLOCKED"
QUARANTINED = "QUARANTINED"
CANCELLED = "CANCELLED"

TERMINAL_FAILURES = {FAILED, BLOCKED, QUARANTINED, CANCELLED}
TERMINAL_STATES = TERMINAL_FAILURES | {SUCCEEDED}
ACTIVE_STATES = {WAITING, AWAITING_APPROVAL, READY, RUNNING, RETRY_WAIT}


SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    stage TEXT NOT NULL,
    lane TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 1,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    available_at REAL NOT NULL,
    lease_owner TEXT,
    lease_expires_at REAL,
    heartbeat_at REAL,
    idempotency_key TEXT NOT NULL UNIQUE,
    result_json TEXT,
    last_error TEXT,
    receipt_path TEXT,
    receipt_sha256 TEXT,
    approved_by TEXT,
    approval_reason TEXT,
    approved_at REAL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS job_dependencies (
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    dependency_job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, dependency_job_id),
    CHECK (job_id <> dependency_job_id)
);

CREATE TABLE IF NOT EXISTS events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT NOT NULL,
    job_id TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS jobs_claim_idx
ON jobs(status, available_at, priority DESC, created_at);
CREATE INDEX IF NOT EXISTS jobs_campaign_idx
ON jobs(campaign_id, status, stage);
CREATE INDEX IF NOT EXISTS dependencies_job_idx
ON job_dependencies(job_id);
CREATE INDEX IF NOT EXISTS events_campaign_idx
ON events(campaign_id, sequence);
"""


class StoreError(RuntimeError):
    pass


class OrchestrationStore:
    """SQLite queue with transactional claims and recoverable leases."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(SCHEMA + MAILBOX_SCHEMA)

    @property
    def mailbox(self) -> FactoryMailbox:
        """Return the append-only factory mailbox sharing this database."""

        return FactoryMailbox(self)

    def append_mailbox_message(self, **values: Any) -> dict[str, Any]:
        """Compatibility facade for :meth:`FactoryMailbox.append_message`."""

        return self.mailbox.append_message(**values)

    def append_message(self, **values: Any) -> dict[str, Any]:
        return self.mailbox.append_message(**values)

    def get_mailbox_message(self, message_id: str) -> dict[str, Any]:
        return self.mailbox.get_message(message_id)

    def get_message(self, message_id: str) -> dict[str, Any]:
        return self.mailbox.get_message(message_id)

    def list_mailbox_messages(self, **filters: Any) -> list[dict[str, Any]]:
        return self.mailbox.list_messages(**filters)

    def list_messages(self, **filters: Any) -> list[dict[str, Any]]:
        return self.mailbox.list_messages(**filters)

    def publish_candidate(self, **values: Any) -> dict[str, Any]:
        return self.mailbox.publish_candidate(**values)

    def publish_repair_candidate(self, **values: Any) -> dict[str, Any]:
        return self.mailbox.publish_repair_candidate(**values)

    def get_candidate(self, **identity: Any) -> dict[str, Any]:
        return self.mailbox.get_candidate(**identity)

    def list_candidates(self, **filters: Any) -> list[dict[str, Any]]:
        return self.mailbox.list_candidates(**filters)

    def latest_candidate(self, **identity: Any) -> dict[str, Any] | None:
        return self.mailbox.latest_candidate(**identity)

    def next_candidate_generation(self, **identity: Any) -> int:
        return self.mailbox.next_generation(**identity)

    def next_generation(self, **identity: Any) -> int:
        return self.mailbox.next_generation(**identity)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=30,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()

    @staticmethod
    def _event(
        connection: sqlite3.Connection,
        campaign_id: str,
        job_id: str | None,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO events(campaign_id, job_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                job_id,
                event_type,
                json.dumps(payload or {}, sort_keys=True),
                time.time(),
            ),
        )

    def create_campaign(
        self,
        *,
        campaign_id: str,
        name: str,
        kind: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM campaigns WHERE id = ?",
                (campaign_id,),
            ).fetchone()
            encoded_metadata = json.dumps(metadata or {}, sort_keys=True)
            if existing is not None:
                if (
                    existing["name"] != name
                    or existing["kind"] != kind
                    or existing["metadata_json"] != encoded_metadata
                ):
                    raise StoreError(
                        f"campaign id already exists with a different definition: "
                        f"{campaign_id}"
                    )
                result = dict(existing)
                result["metadata"] = json.loads(result.pop("metadata_json"))
                return result
            connection.execute(
                """
                INSERT INTO campaigns(id, name, kind, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id,
                    name,
                    kind,
                    encoded_metadata,
                    now,
                    now,
                ),
            )
            self._event(connection, campaign_id, None, "CAMPAIGN_CREATED")
        return self.get_campaign(campaign_id)

    def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
            ).fetchone()
        if row is None:
            raise StoreError(f"unknown campaign: {campaign_id}")
        result = dict(row)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        return result

    def enqueue_job(
        self,
        *,
        campaign_id: str,
        name: str,
        stage: str,
        lane: str,
        kind: str,
        payload: dict[str, Any],
        dependencies: list[str] | None = None,
        max_attempts: int = 1,
        priority: int = 0,
        idempotency_key: str | None = None,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        if max_attempts < 1:
            raise StoreError("max_attempts must be at least 1")
        job_id = job_id or f"job-{uuid.uuid4().hex}"
        idempotency_key = idempotency_key or f"{campaign_id}:{job_id}"
        dependencies = dependencies or []
        now = time.time()
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT id FROM jobs WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                return self._get_job(connection, existing["id"])
            if connection.execute(
                "SELECT 1 FROM campaigns WHERE id = ?", (campaign_id,)
            ).fetchone() is None:
                raise StoreError(f"unknown campaign: {campaign_id}")
            for dependency in dependencies:
                dependency_row = connection.execute(
                    "SELECT campaign_id FROM jobs WHERE id = ?", (dependency,)
                ).fetchone()
                if dependency_row is None:
                    raise StoreError(f"unknown dependency: {dependency}")
                if dependency_row["campaign_id"] != campaign_id:
                    raise StoreError("cross-campaign dependencies are not allowed")
            connection.execute(
                """
                INSERT INTO jobs(
                    id, campaign_id, name, stage, lane, kind, payload_json,
                    status, priority, max_attempts, available_at,
                    idempotency_key, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    campaign_id,
                    name,
                    stage,
                    lane,
                    kind,
                    json.dumps(payload, sort_keys=True),
                    WAITING,
                    priority,
                    max_attempts,
                    now,
                    idempotency_key,
                    now,
                    now,
                ),
            )
            for dependency in dependencies:
                connection.execute(
                    """
                    INSERT INTO job_dependencies(job_id, dependency_job_id)
                    VALUES (?, ?)
                    """,
                    (job_id, dependency),
                )
            self._event(
                connection,
                campaign_id,
                job_id,
                "JOB_ENQUEUED",
                {"dependencies": dependencies, "kind": kind},
            )
            self._refresh_locked(connection, now)
            return self._get_job(connection, job_id)

    @staticmethod
    def _get_job(connection: sqlite3.Connection, job_id: str) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT j.*,
                   COALESCE(
                     json_group_array(d.dependency_job_id)
                       FILTER (WHERE d.dependency_job_id IS NOT NULL),
                     json('[]')
                   ) AS dependencies_json
            FROM jobs j
            LEFT JOIN job_dependencies d ON d.job_id = j.id
            WHERE j.id = ?
            GROUP BY j.id
            """,
            (job_id,),
        ).fetchone()
        if row is None:
            raise StoreError(f"unknown job: {job_id}")
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        result["dependencies"] = json.loads(result.pop("dependencies_json"))
        result_json = result.pop("result_json")
        result["result"] = json.loads(result_json) if result_json is not None else None
        return result

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            return self._get_job(connection, job_id)

    def list_jobs(
        self,
        *,
        campaign_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if campaign_id is not None:
            clauses.append("campaign_id = ?")
            values.append(campaign_id)
        if status is not None:
            clauses.append("status = ?")
            values.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT id FROM jobs
                {where}
                ORDER BY priority DESC, created_at, id
                """,
                values,
            ).fetchall()
            return [self._get_job(connection, row["id"]) for row in rows]

    def _refresh_locked(self, connection: sqlite3.Connection, now: float) -> None:
        expired = connection.execute(
            """
            SELECT id, campaign_id, attempt_count, max_attempts, payload_json
            FROM jobs
            WHERE status = ? AND lease_expires_at < ?
            """,
            (RUNNING, now),
        ).fetchall()
        for row in expired:
            payload = json.loads(row["payload_json"])
            if row["attempt_count"] < row["max_attempts"]:
                backoff = float(payload.get("retry_backoff_seconds", 1.0))
                delay = backoff * (2 ** max(0, row["attempt_count"] - 1))
                next_status = RETRY_WAIT
                available_at = now + delay
            else:
                next_status = QUARANTINED
                available_at = now
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, available_at = ?, lease_owner = NULL,
                    lease_expires_at = NULL, heartbeat_at = NULL,
                    last_error = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    next_status,
                    available_at,
                    "worker lease expired",
                    now,
                    row["id"],
                ),
            )
            self._event(
                connection,
                row["campaign_id"],
                row["id"],
                "LEASE_EXPIRED",
                {"next_status": next_status},
            )

        retry_ready = connection.execute(
            """
            SELECT id, campaign_id
            FROM jobs
            WHERE status = ? AND available_at <= ?
            ORDER BY id
            """,
            (RETRY_WAIT, now),
        ).fetchall()
        for row in retry_ready:
            connection.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
                (READY, now, row["id"]),
            )
            self._event(
                connection,
                row["campaign_id"],
                row["id"],
                "JOB_RETRY_READY",
            )

        waiting = connection.execute(
            "SELECT id, campaign_id, kind FROM jobs WHERE status = ?",
            (WAITING,),
        ).fetchall()
        for row in waiting:
            dependency_statuses = [
                result["status"]
                for result in connection.execute(
                    """
                    SELECT dependency.status
                    FROM job_dependencies link
                    JOIN jobs dependency ON dependency.id = link.dependency_job_id
                    WHERE link.job_id = ?
                    """,
                    (row["id"],),
                ).fetchall()
            ]
            if any(status in TERMINAL_FAILURES for status in dependency_statuses):
                next_status = BLOCKED
                event = "JOB_BLOCKED_BY_DEPENDENCY"
            elif all(status == SUCCEEDED for status in dependency_statuses):
                next_status = (
                    AWAITING_APPROVAL if row["kind"] == "manual_gate" else READY
                )
                event = (
                    "APPROVAL_REQUIRED"
                    if next_status == AWAITING_APPROVAL
                    else "JOB_READY"
                )
            else:
                continue
            connection.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
                (next_status, now, row["id"]),
            )
            self._event(connection, row["campaign_id"], row["id"], event)

        campaigns = connection.execute(
            "SELECT id, status FROM campaigns WHERE status = 'ACTIVE'"
        ).fetchall()
        for campaign in campaigns:
            states = [
                row["status"]
                for row in connection.execute(
                    "SELECT status FROM jobs WHERE campaign_id = ?",
                    (campaign["id"],),
                ).fetchall()
            ]
            if states and all(state in TERMINAL_STATES for state in states):
                final = (
                    "SUCCEEDED"
                    if all(state == SUCCEEDED for state in states)
                    else "NEEDS_ATTENTION"
                )
                connection.execute(
                    "UPDATE campaigns SET status = ?, updated_at = ? WHERE id = ?",
                    (final, now, campaign["id"]),
                )
                self._event(
                    connection,
                    campaign["id"],
                    None,
                    "CAMPAIGN_TERMINAL",
                    {"status": final},
                )

    def refresh(self) -> None:
        with self._transaction() as connection:
            self._refresh_locked(connection, time.time())

    def claim(
        self,
        *,
        worker_id: str,
        lease_seconds: float,
        lanes: set[str] | None = None,
    ) -> dict[str, Any] | None:
        now = time.time()
        with self._transaction() as connection:
            self._refresh_locked(connection, now)
            values: list[Any] = [READY, now]
            lane_clause = ""
            if lanes:
                placeholders = ",".join("?" for _ in lanes)
                lane_clause = f"AND lane IN ({placeholders})"
                values.extend(sorted(lanes))
            row = connection.execute(
                f"""
                SELECT id
                FROM jobs
                WHERE status = ? AND available_at <= ?
                {lane_clause}
                ORDER BY priority DESC, created_at, id
                LIMIT 1
                """,
                values,
            ).fetchone()
            if row is None:
                return None
            updated = connection.execute(
                """
                UPDATE jobs
                SET status = ?, attempt_count = attempt_count + 1,
                    lease_owner = ?, lease_expires_at = ?, heartbeat_at = ?,
                    updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    RUNNING,
                    worker_id,
                    now + lease_seconds,
                    now,
                    now,
                    row["id"],
                    READY,
                ),
            )
            if updated.rowcount != 1:
                return None
            job = self._get_job(connection, row["id"])
            self._event(
                connection,
                job["campaign_id"],
                job["id"],
                "JOB_CLAIMED",
                {
                    "worker_id": worker_id,
                    "attempt": job["attempt_count"],
                    "lease_seconds": lease_seconds,
                },
            )
            return job

    def heartbeat(
        self,
        job_id: str,
        *,
        worker_id: str,
        lease_seconds: float,
    ) -> bool:
        now = time.time()
        with self._transaction() as connection:
            updated = connection.execute(
                """
                UPDATE jobs
                SET heartbeat_at = ?, lease_expires_at = ?, updated_at = ?
                WHERE id = ? AND status = ? AND lease_owner = ?
                """,
                (now, now + lease_seconds, now, job_id, RUNNING, worker_id),
            )
            return updated.rowcount == 1

    def succeed(
        self,
        job_id: str,
        *,
        worker_id: str,
        result: dict[str, Any],
        receipt_path: str,
        receipt_sha256: str,
    ) -> None:
        now = time.time()
        with self._transaction() as connection:
            job = self._get_job(connection, job_id)
            updated = connection.execute(
                """
                UPDATE jobs
                SET status = ?, result_json = ?, receipt_path = ?,
                    receipt_sha256 = ?, lease_owner = NULL,
                    lease_expires_at = NULL, heartbeat_at = NULL,
                    last_error = NULL, updated_at = ?
                WHERE id = ? AND status = ? AND lease_owner = ?
                """,
                (
                    SUCCEEDED,
                    json.dumps(result, sort_keys=True),
                    receipt_path,
                    receipt_sha256,
                    now,
                    job_id,
                    RUNNING,
                    worker_id,
                ),
            )
            if updated.rowcount != 1:
                raise StoreError(f"job lease lost before completion: {job_id}")
            self._event(
                connection,
                job["campaign_id"],
                job_id,
                "JOB_SUCCEEDED",
                {"receipt_sha256": receipt_sha256},
            )
            self._refresh_locked(connection, now)

    def fail(
        self,
        job_id: str,
        *,
        worker_id: str,
        error: str,
        receipt_path: str | None = None,
        receipt_sha256: str | None = None,
    ) -> str:
        now = time.time()
        with self._transaction() as connection:
            job = self._get_job(connection, job_id)
            if job["status"] != RUNNING or job["lease_owner"] != worker_id:
                raise StoreError(f"job lease lost before failure report: {job_id}")
            if job["attempt_count"] < job["max_attempts"]:
                backoff = float(job["payload"].get("retry_backoff_seconds", 1.0))
                delay = backoff * (2 ** max(0, job["attempt_count"] - 1))
                status = RETRY_WAIT
                available_at = now + delay
            else:
                status = QUARANTINED
                available_at = now
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, available_at = ?, last_error = ?,
                    receipt_path = COALESCE(?, receipt_path),
                    receipt_sha256 = COALESCE(?, receipt_sha256),
                    lease_owner = NULL, lease_expires_at = NULL,
                    heartbeat_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    available_at,
                    error,
                    receipt_path,
                    receipt_sha256,
                    now,
                    job_id,
                ),
            )
            self._event(
                connection,
                job["campaign_id"],
                job_id,
                "JOB_FAILED_ATTEMPT",
                {
                    "attempt": job["attempt_count"],
                    "next_status": status,
                    "error": error,
                },
            )
            self._refresh_locked(connection, now)
            return status

    def approve(self, job_id: str, *, operator: str, reason: str) -> None:
        if not operator.strip() or not reason.strip():
            raise StoreError("operator and reason are required")
        now = time.time()
        with self._transaction() as connection:
            job = self._get_job(connection, job_id)
            if job["kind"] != "manual_gate" or job["status"] != AWAITING_APPROVAL:
                raise StoreError(f"job is not awaiting manual approval: {job_id}")
            dependencies = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT dependency.id, dependency.receipt_path,
                           dependency.receipt_sha256
                    FROM job_dependencies link
                    JOIN jobs dependency ON dependency.id = link.dependency_job_id
                    WHERE link.job_id = ?
                    ORDER BY dependency.id
                    """,
                    (job_id,),
                ).fetchall()
            ]
            result = {
                "approved_by": operator,
                "approval_reason": reason,
                "approved_at": now,
            }
            approval_receipt = {
                "schema_version": "1.0.0",
                "receipt_id": f"approval-{uuid.uuid4().hex}",
                "campaign_id": job["campaign_id"],
                "job_id": job_id,
                "stage": job["stage"],
                "approved_by": operator,
                "approval_reason": reason,
                "approved_at": now,
                "dependency_receipts": dependencies,
            }
            receipt_path = (
                self.path.parent
                / "approvals"
                / job["campaign_id"]
                / f"{job_id}.json"
            )
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = receipt_path.with_name(
                f".{receipt_path.name}.{uuid.uuid4().hex}.tmp"
            )
            receipt_bytes = (
                json.dumps(approval_receipt, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            temporary.write_bytes(receipt_bytes)
            os.replace(temporary, receipt_path)
            receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, result_json = ?, approved_by = ?,
                    approval_reason = ?, approved_at = ?,
                    receipt_path = ?, receipt_sha256 = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    SUCCEEDED,
                    json.dumps(result, sort_keys=True),
                    operator,
                    reason,
                    now,
                    str(receipt_path),
                    receipt_sha256,
                    now,
                    job_id,
                ),
            )
            self._event(
                connection,
                job["campaign_id"],
                job_id,
                "MANUAL_GATE_APPROVED",
                {**result, "receipt_sha256": receipt_sha256},
            )
            self._refresh_locked(connection, now)

    def retry(
        self,
        job_id: str,
        *,
        operator: str,
        reason: str,
        additional_attempts: int = 1,
    ) -> None:
        if not operator.strip() or not reason.strip():
            raise StoreError("operator and reason are required")
        if additional_attempts < 1:
            raise StoreError("additional_attempts must be at least 1")
        now = time.time()
        with self._transaction() as connection:
            job = self._get_job(connection, job_id)
            if job["status"] not in TERMINAL_FAILURES:
                raise StoreError(f"job is not retryable from {job['status']}: {job_id}")
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, max_attempts = max_attempts + ?, available_at = ?,
                    last_error = NULL, result_json = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (WAITING, additional_attempts, now, now, job_id),
            )
            # Only descendants of the repaired job can have been unblocked by
            # this retry. Resetting every blocked job in the campaign would
            # wake unrelated failure branches and duplicate work.
            connection.execute(
                """
                WITH RECURSIVE descendants(id) AS (
                    SELECT job_id
                    FROM job_dependencies
                    WHERE dependency_job_id = ?
                    UNION
                    SELECT link.job_id
                    FROM job_dependencies AS link
                    JOIN descendants
                      ON link.dependency_job_id = descendants.id
                )
                UPDATE jobs
                SET status = ?, updated_at = ?
                WHERE id IN (SELECT id FROM descendants)
                  AND campaign_id = ?
                  AND status = ?
                """,
                (job_id, WAITING, now, job["campaign_id"], BLOCKED),
            )
            connection.execute(
                """
                UPDATE campaigns
                SET status = 'ACTIVE', updated_at = ?
                WHERE id = ?
                """,
                (now, job["campaign_id"]),
            )
            self._event(
                connection,
                job["campaign_id"],
                job_id,
                "JOB_RETRIED",
                {
                    "operator": operator,
                    "reason": reason,
                    "additional_attempts": additional_attempts,
                    "prior_attempt_count": job["attempt_count"],
                },
            )
            self._refresh_locked(connection, now)

    def events(
        self,
        campaign_id: str,
        *,
        after_sequence: int = 0,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        if after_sequence < 0:
            raise StoreError("after_sequence must not be negative")
        if not 1 <= limit <= 1000:
            raise StoreError("event limit must be between 1 and 1000")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM events
                WHERE campaign_id = ? AND sequence > ?
                ORDER BY sequence
                LIMIT ?
                """,
                (campaign_id, after_sequence, limit),
            ).fetchall()
        output: list[dict[str, Any]] = []
        for row in rows:
            event = dict(row)
            event["payload"] = json.loads(event.pop("payload_json"))
            output.append(event)
        return output

    def counts(self, campaign_id: str | None = None) -> dict[str, int]:
        values: tuple[Any, ...] = ()
        where = ""
        if campaign_id is not None:
            where = "WHERE campaign_id = ?"
            values = (campaign_id,)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT status, COUNT(*) AS count FROM jobs {where} GROUP BY status",
                values,
            ).fetchall()
        return {row["status"]: row["count"] for row in rows}

    def has_claimable_or_running(self) -> bool:
        self.refresh()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM jobs
                WHERE status IN (?, ?, ?)
                LIMIT 1
                """,
                (READY, RUNNING, RETRY_WAIT),
            ).fetchone()
        return row is not None
