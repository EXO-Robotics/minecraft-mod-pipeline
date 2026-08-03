"""Canonical chained lifecycle events and disposable SQLite projections."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

from .identity import validate_identity


EVENT_SCHEMA = "bedrock-factory.canonical-event.v1.0.0"
ZERO_HASH = "0" * 64
PROJECTION_SCHEMA = "bedrock-factory.lifecycle-projection.v1.0.0"


class EventLogError(RuntimeError):
    pass


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def event_digest(event: dict[str, Any]) -> str:
    normalized = dict(event)
    normalized.pop("event_sha256", None)
    return hashlib.sha256(canonical_bytes(normalized)).hexdigest()


class CanonicalEventLog:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        previous = ZERO_HASH
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EventLogError(f"invalid event JSON at line {line_number}") from exc
            if event.get("schema_version") != EVENT_SCHEMA:
                raise EventLogError(f"event schema rejected at line {line_number}")
            if event.get("sequence") != line_number:
                raise EventLogError(f"event sequence mismatch at line {line_number}")
            if event.get("previous_event_sha256") != previous:
                raise EventLogError(f"event chain mismatch at line {line_number}")
            observed = event_digest(event)
            if event.get("event_sha256") != observed:
                raise EventLogError(f"event digest mismatch at line {line_number}")
            previous = observed
            events.append(event)
        return events

    def append(
        self,
        *,
        campaign_id: str,
        workload_id: str,
        event_type: str,
        authority_hash: str,
        candidate_id: str | None = None,
        activation_id: str | None = None,
        gate_run_id: str | None = None,
        input_hashes: dict[str, str] | None = None,
        output_hashes: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        created_at: float | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        if candidate_id is not None:
            validate_identity(candidate_id, "candidate")
        if activation_id is not None:
            validate_identity(activation_id, "activation")
        if not isinstance(authority_hash, str) or len(authority_hash) != 64:
            raise EventLogError("authority_hash must be SHA-256")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            stream.seek(0)
            raw_lines = stream.read().splitlines()
            existing = self.read() if raw_lines else []
            previous = existing[-1]["event_sha256"] if existing else ZERO_HASH
            event = {
                "schema_version": EVENT_SCHEMA,
                "event_id": event_id or f"evt-{uuid.uuid4().hex}",
                "sequence": len(existing) + 1,
                "campaign_id": campaign_id,
                "workload_id": workload_id,
                "candidate_id": candidate_id,
                "activation_id": activation_id,
                "gate_run_id": gate_run_id,
                "event_type": event_type,
                "input_hashes": input_hashes or {},
                "output_hashes": output_hashes or {},
                "authority_hash": authority_hash,
                "created_at": time.time() if created_at is None else float(created_at),
                "payload": payload or {},
                "previous_event_sha256": previous,
            }
            event["event_sha256"] = event_digest(event)
            stream.seek(0, os.SEEK_END)
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            return event


PROJECTION_SQL = """
CREATE TABLE kernel_events (
    sequence INTEGER PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    campaign_id TEXT NOT NULL,
    workload_id TEXT NOT NULL,
    candidate_id TEXT,
    activation_id TEXT,
    gate_run_id TEXT,
    event_type TEXT NOT NULL,
    created_at REAL NOT NULL,
    event_sha256 TEXT NOT NULL,
    event_json TEXT NOT NULL
);
CREATE TABLE kernel_frontier (
    campaign_id TEXT NOT NULL,
    workload_id TEXT NOT NULL,
    candidate_id TEXT,
    activation_id TEXT,
    last_event_type TEXT NOT NULL,
    last_sequence INTEGER NOT NULL,
    updated_at REAL NOT NULL,
    PRIMARY KEY (campaign_id, workload_id)
);
CREATE TABLE projection_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def projection_digest(connection: sqlite3.Connection) -> str:
    rows = [
        dict(zip(("sequence", "event_id", "event_sha256"), row))
        for row in connection.execute(
            "SELECT sequence, event_id, event_sha256 FROM kernel_events ORDER BY sequence"
        )
    ]
    frontier = [
        dict(zip(("campaign_id", "workload_id", "candidate_id", "activation_id", "last_event_type", "last_sequence", "updated_at"), row))
        for row in connection.execute(
            "SELECT campaign_id, workload_id, candidate_id, activation_id, last_event_type, last_sequence, updated_at FROM kernel_frontier ORDER BY campaign_id, workload_id"
        )
    ]
    return hashlib.sha256(canonical_bytes({"events": rows, "frontier": frontier})).hexdigest()


def rebuild_projection(events: Iterable[dict[str, Any]], database: str | Path) -> dict[str, Any]:
    target = Path(database).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    if temporary.exists():
        temporary.unlink()
    with sqlite3.connect(temporary) as connection:
        connection.executescript(PROJECTION_SQL)
        count = 0
        for event in events:
            count += 1
            connection.execute(
                "INSERT INTO kernel_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event["sequence"], event["event_id"], event["campaign_id"],
                    event["workload_id"], event.get("candidate_id"),
                    event.get("activation_id"), event.get("gate_run_id"),
                    event["event_type"], event["created_at"],
                    event["event_sha256"], json.dumps(event, sort_keys=True),
                ),
            )
            connection.execute(
                """
                INSERT INTO kernel_frontier VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(campaign_id, workload_id) DO UPDATE SET
                  candidate_id=COALESCE(excluded.candidate_id, kernel_frontier.candidate_id),
                  activation_id=COALESCE(excluded.activation_id, kernel_frontier.activation_id),
                  last_event_type=excluded.last_event_type,
                  last_sequence=excluded.last_sequence,
                  updated_at=excluded.updated_at
                """,
                (
                    event["campaign_id"], event["workload_id"],
                    event.get("candidate_id"), event.get("activation_id"),
                    event["event_type"], event["sequence"], event["created_at"],
                ),
            )
        digest = projection_digest(connection)
        connection.executemany(
            "INSERT INTO projection_meta VALUES (?, ?)",
            (("schema_version", PROJECTION_SCHEMA), ("projection_sha256", digest), ("event_count", str(count))),
        )
        connection.commit()
    os.replace(temporary, target)
    return {"schema_version": PROJECTION_SCHEMA, "event_count": count, "projection_sha256": digest, "database": str(target)}


def verify_projection(events: Iterable[dict[str, Any]], database: str | Path) -> dict[str, Any]:
    target = Path(database).expanduser().resolve()
    if not target.is_file():
        raise EventLogError(f"projection is missing: {target}")
    with sqlite3.connect(target) as retained:
        retained_digest = projection_digest(retained)
    comparison = target.with_name(f".{target.name}.verify.{os.getpid()}.tmp")
    try:
        rebuilt = rebuild_projection(events, comparison)
        match = retained_digest == rebuilt["projection_sha256"]
        if not match:
            raise EventLogError("retained projection differs from rebuild-from-zero")
        return {"status": "PASS", "projection_sha256": retained_digest, "rebuild_match": True}
    finally:
        if comparison.exists():
            comparison.unlink()
