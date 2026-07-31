from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Protocol


MAILBOX_SCHEMA = """
CREATE TABLE IF NOT EXISTS factory_messages (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL UNIQUE,
    campaign_id TEXT NOT NULL,
    pack_id TEXT NOT NULL,
    message_type TEXT NOT NULL,
    sender_role TEXT NOT NULL,
    recipient_role TEXT,
    candidate_generation INTEGER,
    parent_message_id TEXT REFERENCES factory_messages(message_id) ON DELETE RESTRICT,
    supersedes_message_id TEXT REFERENCES factory_messages(message_id) ON DELETE RESTRICT,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    created_at REAL NOT NULL,
    CHECK (candidate_generation IS NULL OR candidate_generation >= 1),
    CHECK (parent_message_id IS NULL OR parent_message_id <> message_id),
    CHECK (supersedes_message_id IS NULL OR supersedes_message_id <> message_id)
);

CREATE TABLE IF NOT EXISTS factory_candidates (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL UNIQUE,
    campaign_id TEXT NOT NULL,
    pack_id TEXT NOT NULL,
    generation INTEGER NOT NULL CHECK (generation >= 1),
    repair_of_generation INTEGER,
    source_message_id TEXT REFERENCES factory_messages(message_id) ON DELETE RESTRICT,
    idempotency_key TEXT NOT NULL UNIQUE,
    production_commit TEXT,
    production_tree TEXT,
    artifact_sha256 TEXT,
    manifest_sha256 TEXT,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE (campaign_id, pack_id, generation),
    CHECK (repair_of_generation IS NULL OR repair_of_generation >= 1),
    CHECK (
        repair_of_generation IS NULL
        OR generation = repair_of_generation + 1
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS factory_messages_single_superseder_idx
ON factory_messages(supersedes_message_id)
WHERE supersedes_message_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS factory_messages_route_idx
ON factory_messages(campaign_id, pack_id, sequence);
CREATE INDEX IF NOT EXISTS factory_messages_type_idx
ON factory_messages(campaign_id, message_type, sequence);
CREATE INDEX IF NOT EXISTS factory_messages_parent_idx
ON factory_messages(parent_message_id);
CREATE INDEX IF NOT EXISTS factory_candidates_pack_idx
ON factory_candidates(campaign_id, pack_id, generation);
CREATE INDEX IF NOT EXISTS factory_candidates_message_idx
ON factory_candidates(source_message_id);

CREATE TRIGGER IF NOT EXISTS factory_messages_no_update
BEFORE UPDATE ON factory_messages
BEGIN
    SELECT RAISE(ABORT, 'factory_messages is append-only');
END;

CREATE TRIGGER IF NOT EXISTS factory_messages_no_delete
BEFORE DELETE ON factory_messages
BEGIN
    SELECT RAISE(ABORT, 'factory_messages is append-only');
END;

CREATE TRIGGER IF NOT EXISTS factory_candidates_no_update
BEFORE UPDATE ON factory_candidates
BEGIN
    SELECT RAISE(ABORT, 'factory_candidates is immutable');
END;

CREATE TRIGGER IF NOT EXISTS factory_candidates_no_delete
BEFORE DELETE ON factory_candidates
BEGIN
    SELECT RAISE(ABORT, 'factory_candidates is immutable');
END;
"""


class MailboxError(RuntimeError):
    """Raised when a mailbox append would violate durable factory authority."""


class _StoreBackend(Protocol):
    path: Path

    def _connect(self) -> sqlite3.Connection: ...

    def _transaction(self) -> Iterator[sqlite3.Connection]: ...


def _canonical_json(value: dict[str, Any]) -> str:
    if not isinstance(value, dict):
        raise MailboxError("payload must be an object")
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise MailboxError(f"payload is not canonical JSON: {exc}") from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MailboxError(f"{name} is required")
    return value


class FactoryMailbox:
    """Append-only factory mail and immutable candidate-generation ledger.

    The mailbox can share an :class:`OrchestrationStore` database or own a
    standalone SQLite path. All publication decisions are made inside
    ``BEGIN IMMEDIATE`` transactions so concurrent workers cannot allocate the
    same candidate generation or create competing supersession branches.
    """

    def __init__(self, store_or_path: _StoreBackend | str | Path):
        if hasattr(store_or_path, "_connect") and hasattr(
            store_or_path, "_transaction"
        ):
            self._backend: _StoreBackend | None = store_or_path  # type: ignore[assignment]
            self.path = Path(store_or_path.path).expanduser().resolve()  # type: ignore[union-attr]
        else:
            self._backend = None
            self.path = Path(store_or_path).expanduser().resolve()  # type: ignore[arg-type]

    def _connect(self) -> sqlite3.Connection:
        if self._backend is not None:
            return self._backend._connect()
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        if self._backend is not None:
            with self._backend._transaction() as connection:
                yield connection
            return
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(MAILBOX_SCHEMA)

    @staticmethod
    def _message_from_row(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result

    @staticmethod
    def _candidate_from_row(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result

    @staticmethod
    def _message_by_id(
        connection: sqlite3.Connection, message_id: str
    ) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM factory_messages WHERE message_id = ?", (message_id,)
        ).fetchone()

    @staticmethod
    def _candidate_by_generation(
        connection: sqlite3.Connection,
        campaign_id: str,
        pack_id: str,
        generation: int,
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT * FROM factory_candidates
            WHERE campaign_id = ? AND pack_id = ? AND generation = ?
            """,
            (campaign_id, pack_id, generation),
        ).fetchone()

    def append_message(
        self,
        *,
        campaign_id: str,
        pack_id: str,
        message_type: str,
        sender_role: str,
        payload: dict[str, Any],
        idempotency_key: str,
        message_id: str | None = None,
        recipient_role: str | None = None,
        candidate_generation: int | None = None,
        parent_message_id: str | None = None,
        supersedes_message_id: str | None = None,
        created_at: float | None = None,
    ) -> dict[str, Any]:
        campaign_id = _required_text(campaign_id, "campaign_id")
        pack_id = _required_text(pack_id, "pack_id")
        message_type = _required_text(message_type, "message_type")
        sender_role = _required_text(sender_role, "sender_role")
        idempotency_key = _required_text(idempotency_key, "idempotency_key")
        if recipient_role is not None:
            _required_text(recipient_role, "recipient_role")
        if candidate_generation is not None and (
            not isinstance(candidate_generation, int)
            or isinstance(candidate_generation, bool)
            or candidate_generation < 1
        ):
            raise MailboxError("candidate_generation must be a positive integer")
        encoded = _canonical_json(payload)
        payload_sha256 = _sha256_text(encoded)
        message_id = message_id or (
            "msg-"
            + hashlib.sha256(
                f"{campaign_id}\0{pack_id}\0{idempotency_key}".encode("utf-8")
            ).hexdigest()[:32]
        )
        _required_text(message_id, "message_id")
        now = time.time() if created_at is None else float(created_at)

        semantic = {
            "campaign_id": campaign_id,
            "pack_id": pack_id,
            "message_type": message_type,
            "sender_role": sender_role,
            "recipient_role": recipient_role,
            "candidate_generation": candidate_generation,
            "parent_message_id": parent_message_id,
            "supersedes_message_id": supersedes_message_id,
            "payload_sha256": payload_sha256,
        }
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM factory_messages WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                observed = {name: existing[name] for name in semantic}
                if observed != semantic or existing["message_id"] != message_id:
                    raise MailboxError(
                        "idempotency key already names a different message: "
                        f"{idempotency_key}"
                    )
                return self._message_from_row(existing)

            duplicate_id = self._message_by_id(connection, message_id)
            if duplicate_id is not None:
                raise MailboxError(f"message id already exists: {message_id}")

            parent = None
            if parent_message_id is not None:
                parent = self._message_by_id(connection, parent_message_id)
                if parent is None:
                    raise MailboxError(f"unknown parent message: {parent_message_id}")
                if (parent["campaign_id"], parent["pack_id"]) != (
                    campaign_id,
                    pack_id,
                ):
                    raise MailboxError("parent message must belong to the same pack")

            if supersedes_message_id is not None:
                superseded = self._message_by_id(connection, supersedes_message_id)
                if superseded is None:
                    raise MailboxError(
                        f"unknown superseded message: {supersedes_message_id}"
                    )
                if (superseded["campaign_id"], superseded["pack_id"]) != (
                    campaign_id,
                    pack_id,
                ):
                    raise MailboxError(
                        "superseded message must belong to the same pack"
                    )
                if connection.execute(
                    """
                    SELECT 1 FROM factory_messages
                    WHERE supersedes_message_id = ?
                    """,
                    (supersedes_message_id,),
                ).fetchone() is not None:
                    raise MailboxError(
                        "message already has an authoritative superseder: "
                        f"{supersedes_message_id}"
                    )
            connection.execute(
                """
                INSERT INTO factory_messages(
                    message_id, campaign_id, pack_id, message_type,
                    sender_role, recipient_role, candidate_generation,
                    parent_message_id, supersedes_message_id,
                    idempotency_key, payload_json, payload_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    campaign_id,
                    pack_id,
                    message_type,
                    sender_role,
                    recipient_role,
                    candidate_generation,
                    parent_message_id,
                    supersedes_message_id,
                    idempotency_key,
                    encoded,
                    payload_sha256,
                    now,
                ),
            )
            row = self._message_by_id(connection, message_id)
            assert row is not None
            return self._message_from_row(row)

    def get_message(self, message_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = self._message_by_id(connection, message_id)
        if row is None:
            raise MailboxError(f"unknown message: {message_id}")
        return self._message_from_row(row)

    def get_message_by_idempotency_key(
        self, idempotency_key: str
    ) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM factory_messages WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
        if row is None:
            raise MailboxError(
                f"unknown message idempotency key: {idempotency_key}"
            )
        return self._message_from_row(row)

    def list_messages(
        self,
        *,
        campaign_id: str | None = None,
        pack_id: str | None = None,
        message_type: str | None = None,
        after_sequence: int = 0,
        limit: int = 200,
        include_superseded: bool = True,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise MailboxError("limit must be at least 1")
        clauses = ["m.sequence > ?"]
        values: list[Any] = [after_sequence]
        for column, value in (
            ("campaign_id", campaign_id),
            ("pack_id", pack_id),
            ("message_type", message_type),
        ):
            if value is not None:
                clauses.append(f"m.{column} = ?")
                values.append(value)
        if not include_superseded:
            clauses.append(
                "NOT EXISTS (SELECT 1 FROM factory_messages newer "
                "WHERE newer.supersedes_message_id = m.message_id)"
            )
        values.append(limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT m.* FROM factory_messages m
                WHERE {' AND '.join(clauses)}
                ORDER BY m.sequence
                LIMIT ?
                """,
                values,
            ).fetchall()
        return [self._message_from_row(row) for row in rows]

    def latest_message(
        self,
        *,
        campaign_id: str,
        pack_id: str,
        message_type: str | None = None,
        include_superseded: bool = False,
    ) -> dict[str, Any] | None:
        clauses = ["m.campaign_id = ?", "m.pack_id = ?"]
        values: list[Any] = [campaign_id, pack_id]
        if message_type is not None:
            clauses.append("m.message_type = ?")
            values.append(message_type)
        if not include_superseded:
            clauses.append(
                "NOT EXISTS (SELECT 1 FROM factory_messages newer "
                "WHERE newer.supersedes_message_id = m.message_id)"
            )
        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT m.* FROM factory_messages m
                WHERE {' AND '.join(clauses)}
                ORDER BY m.sequence DESC LIMIT 1
                """,
                values,
            ).fetchone()
        return self._message_from_row(row) if row is not None else None

    def message_superseder(self, message_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            if self._message_by_id(connection, message_id) is None:
                raise MailboxError(f"unknown message: {message_id}")
            row = connection.execute(
                "SELECT * FROM factory_messages WHERE supersedes_message_id = ?",
                (message_id,),
            ).fetchone()
        return self._message_from_row(row) if row is not None else None

    def is_message_superseded(self, message_id: str) -> bool:
        return self.message_superseder(message_id) is not None

    def authoritative_message(self, message_id: str) -> dict[str, Any]:
        """Resolve a message through its append-only supersession chain."""

        current = self.get_message(message_id)
        seen = {message_id}
        while True:
            newer = self.message_superseder(current["message_id"])
            if newer is None:
                return current
            if newer["message_id"] in seen:
                raise MailboxError("message supersession cycle detected")
            seen.add(newer["message_id"])
            current = newer

    def publish_candidate(
        self,
        *,
        campaign_id: str,
        pack_id: str,
        generation: int,
        payload: dict[str, Any],
        idempotency_key: str,
        candidate_id: str | None = None,
        source_message_id: str | None = None,
        repair_of_generation: int | None = None,
        production_commit: str | None = None,
        production_tree: str | None = None,
        artifact_sha256: str | None = None,
        manifest_sha256: str | None = None,
        created_at: float | None = None,
    ) -> dict[str, Any]:
        campaign_id = _required_text(campaign_id, "campaign_id")
        pack_id = _required_text(pack_id, "pack_id")
        idempotency_key = _required_text(idempotency_key, "idempotency_key")
        if (
            not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation < 1
        ):
            raise MailboxError("generation must be a positive integer")
        if repair_of_generation is not None and (
            not isinstance(repair_of_generation, int)
            or isinstance(repair_of_generation, bool)
            or repair_of_generation < 1
        ):
            raise MailboxError("repair_of_generation must be a positive integer")
        encoded = _canonical_json(payload)
        payload_sha256 = _sha256_text(encoded)
        candidate_id = candidate_id or (
            f"candidate-{pack_id}-g{generation:06d}-{payload_sha256[:12]}"
        )
        _required_text(candidate_id, "candidate_id")
        now = time.time() if created_at is None else float(created_at)

        semantic = {
            "campaign_id": campaign_id,
            "pack_id": pack_id,
            "generation": generation,
            "repair_of_generation": repair_of_generation,
            "source_message_id": source_message_id,
            "production_commit": production_commit,
            "production_tree": production_tree,
            "artifact_sha256": artifact_sha256,
            "manifest_sha256": manifest_sha256,
            "payload_sha256": payload_sha256,
        }
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM factory_candidates WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                observed = {name: existing[name] for name in semantic}
                if observed != semantic or existing["candidate_id"] != candidate_id:
                    raise MailboxError(
                        "idempotency key already names a different candidate: "
                        f"{idempotency_key}"
                    )
                return self._candidate_from_row(existing)

            if connection.execute(
                "SELECT 1 FROM factory_candidates WHERE candidate_id = ?",
                (candidate_id,),
            ).fetchone() is not None:
                raise MailboxError(f"candidate id already exists: {candidate_id}")

            latest = connection.execute(
                """
                SELECT * FROM factory_candidates
                WHERE campaign_id = ? AND pack_id = ?
                ORDER BY generation DESC LIMIT 1
                """,
                (campaign_id, pack_id),
            ).fetchone()
            expected_generation = 1 if latest is None else latest["generation"] + 1
            if generation != expected_generation:
                raise MailboxError(
                    f"candidate generation must be exactly {expected_generation}; "
                    f"received {generation}"
                )
            if repair_of_generation is not None:
                if latest is None or latest["generation"] != repair_of_generation:
                    raise MailboxError(
                        "repair must target the latest immutable candidate generation"
                    )
                if generation != repair_of_generation + 1:
                    raise MailboxError(
                        "repair replacement generation must equal rejected generation + 1"
                    )

            if source_message_id is not None:
                source = self._message_by_id(connection, source_message_id)
                if source is None:
                    raise MailboxError(f"unknown source message: {source_message_id}")
                if (source["campaign_id"], source["pack_id"]) != (
                    campaign_id,
                    pack_id,
                ):
                    raise MailboxError("source message must belong to the same pack")
                source_generation = source["candidate_generation"]
                if source_generation is not None and source_generation != generation:
                    raise MailboxError(
                        "source message candidate generation does not match publication"
                    )
                if connection.execute(
                    """
                    SELECT 1 FROM factory_messages
                    WHERE supersedes_message_id = ?
                    """,
                    (source_message_id,),
                ).fetchone() is not None:
                    raise MailboxError("source message has been superseded")

            connection.execute(
                """
                INSERT INTO factory_candidates(
                    candidate_id, campaign_id, pack_id, generation,
                    repair_of_generation, source_message_id, idempotency_key,
                    production_commit, production_tree, artifact_sha256,
                    manifest_sha256, payload_json, payload_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    campaign_id,
                    pack_id,
                    generation,
                    repair_of_generation,
                    source_message_id,
                    idempotency_key,
                    production_commit,
                    production_tree,
                    artifact_sha256,
                    manifest_sha256,
                    encoded,
                    payload_sha256,
                    now,
                ),
            )
            row = self._candidate_by_generation(
                connection, campaign_id, pack_id, generation
            )
            assert row is not None
            return self._candidate_from_row(row)

    def get_candidate(
        self,
        *,
        candidate_id: str | None = None,
        campaign_id: str | None = None,
        pack_id: str | None = None,
        generation: int | None = None,
    ) -> dict[str, Any]:
        with self._connect() as connection:
            if candidate_id is not None:
                row = connection.execute(
                    "SELECT * FROM factory_candidates WHERE candidate_id = ?",
                    (candidate_id,),
                ).fetchone()
            elif campaign_id is not None and pack_id is not None and generation is not None:
                row = self._candidate_by_generation(
                    connection, campaign_id, pack_id, generation
                )
            else:
                raise MailboxError(
                    "provide candidate_id or campaign_id, pack_id, and generation"
                )
        if row is None:
            raise MailboxError("unknown candidate")
        return self._candidate_from_row(row)

    def get_candidate_by_idempotency_key(
        self, idempotency_key: str
    ) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM factory_candidates WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
        if row is None:
            raise MailboxError(
                f"unknown candidate idempotency key: {idempotency_key}"
            )
        return self._candidate_from_row(row)

    def publish_repair_candidate(
        self, *, rejected_generation: int, **values: Any
    ) -> dict[str, Any]:
        """Publish the sole legal replacement for a rejected generation."""

        if "generation" in values or "repair_of_generation" in values:
            raise MailboxError(
                "publish_repair_candidate derives generation fields from "
                "rejected_generation"
            )
        return self.publish_candidate(
            generation=rejected_generation + 1,
            repair_of_generation=rejected_generation,
            **values,
        )

    def list_candidates(
        self,
        *,
        campaign_id: str | None = None,
        pack_id: str | None = None,
        after_sequence: int = 0,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            raise MailboxError("limit must be at least 1")
        clauses = ["sequence > ?"]
        values: list[Any] = [after_sequence]
        if campaign_id is not None:
            clauses.append("campaign_id = ?")
            values.append(campaign_id)
        if pack_id is not None:
            clauses.append("pack_id = ?")
            values.append(pack_id)
        values.append(limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM factory_candidates
                WHERE {' AND '.join(clauses)}
                ORDER BY sequence LIMIT ?
                """,
                values,
            ).fetchall()
        return [self._candidate_from_row(row) for row in rows]

    def latest_candidate(
        self, *, campaign_id: str, pack_id: str
    ) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM factory_candidates
                WHERE campaign_id = ? AND pack_id = ?
                ORDER BY generation DESC LIMIT 1
                """,
                (campaign_id, pack_id),
            ).fetchone()
        return self._candidate_from_row(row) if row is not None else None

    def next_generation(self, *, campaign_id: str, pack_id: str) -> int:
        latest = self.latest_candidate(campaign_id=campaign_id, pack_id=pack_id)
        return 1 if latest is None else int(latest["generation"]) + 1
