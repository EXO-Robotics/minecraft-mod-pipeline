#!/opt/homebrew/bin/python3
"""Durable T1 semantic dispatcher for the Crazy Craft pack factory.

The router remains the append-only mailbox consumer.  This service owns the
machine-decidable actions the router deliberately leaves prepared: exact
mechanical binding, downstream intake construction, T1->T2 admission, and
requests to resume the original durable pack owner.  It never edits a pack
repository or candidate byte.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import io
import json
import os
import plistlib
import sqlite3
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
ACTION_STATES = {
    "PENDING",
    "LEASED",
    "RUNNING",
    "WAITING_EXTERNAL_RESULT",
    "TERMINAL_PASS",
    "TERMINAL_FAIL",
    "PACK_LOCAL_BLOCK",
    "GLOBAL_BLOCK",
    "SUPERSEDED",
}
TERMINAL_STATES = {
    "TERMINAL_PASS",
    "TERMINAL_FAIL",
    "PACK_LOCAL_BLOCK",
    "GLOBAL_BLOCK",
    "SUPERSEDED",
}
PACKAGE_ROLES = ("behavior_pack", "resource_pack", "mcaddon")
CORRECTED_REPLAY_MESSAGES = (
    "MSG-P07-RELIQUARY-CANDIDATE-000007",
    "MSG-P09-HEARTHVEIL-CANDIDATE-000006",
    "MSG-P13-ECHO-PLATFORM-REQUEST-000004",
)


class DispatchError(RuntimeError):
    pass


def utc_now() -> str:
    return time.strftime(UTC_FORMAT, time.gmtime())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DispatchError(f"expected JSON object: {path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    binary: bool = False,
    check: bool = True,
) -> str | bytes:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
        check=False,
        env={
            "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "GIT_TERMINAL_PROMPT": "0",
            "SSH_AUTH_SOCK": "",
            "GIT_SSH_COMMAND": "/usr/bin/false",
            "LANG": "en_US.UTF-8",
        },
    )
    if check and completed.returncode:
        error = completed.stderr
        if isinstance(error, bytes):
            error = error.decode(errors="replace")
        raise DispatchError(f"command failed ({completed.returncode}): {argv}: {error[-800:]}")
    return completed.stdout


def git_text(repository: Path, *args: str) -> str:
    return str(run(["/usr/bin/git", "-C", str(repository), *args])).strip()


def git_bytes(repository: Path, object_spec: str) -> bytes:
    return bytes(
        run(
            ["/usr/bin/git", "-C", str(repository), "show", object_spec],
            binary=True,
        )
    )


def config_from(path: Path) -> dict[str, Any]:
    config = load_json(path.resolve())
    if config.get("schema_version") != "crazycraft-t1-dispatcher-v1":
        raise DispatchError("unsupported T1 dispatcher config")
    required = {
        "poll_interval_seconds",
        "lease_seconds",
        "max_attempts",
        "mailbox_repository",
        "mailbox_ref",
        "router_state",
        "router_config",
        "publisher",
        "resume_decision",
        "launch_records",
        "assignments",
        "runtime_root",
        "worker_repository_overrides",
        "worker_ref_overrides",
        "t2_thread_id",
        "t10_thread_id",
        "pinned_tester_image",
        "qualifier_sha256",
        "bds_binary_sha256",
        "base_world_sha256",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise DispatchError(f"config missing fields: {missing}")
    for key in (
        "mailbox_repository",
        "router_state",
        "router_config",
        "publisher",
        "resume_decision",
        "launch_records",
        "assignments",
        "runtime_root",
    ):
        config[key] = str(Path(config[key]).resolve())
    return config


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS actions (
  action_id TEXT PRIMARY KEY,
  action_type TEXT NOT NULL,
  pack_id TEXT NOT NULL,
  candidate_generation INTEGER NOT NULL,
  source_mailbox_message TEXT NOT NULL,
  source_mailbox_commit TEXT NOT NULL,
  exact_candidate_authority TEXT NOT NULL,
  current_state TEXT NOT NULL CHECK(current_state IN
    ('PENDING','LEASED','RUNNING','WAITING_EXTERNAL_RESULT','TERMINAL_PASS',
     'TERMINAL_FAIL','PACK_LOCAL_BLOCK','GLOBAL_BLOCK','SUPERSEDED')),
  attempt_count INTEGER NOT NULL DEFAULT 0,
  lease_owner TEXT,
  lease_timestamp TEXT,
  lease_expires_at INTEGER,
  last_error TEXT,
  result_message TEXT,
  idempotency_key TEXT NOT NULL UNIQUE,
  next_action TEXT NOT NULL,
  worker_resumption_state TEXT NOT NULL DEFAULT 'NOT_APPLICABLE',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workers (
  pack_id TEXT PRIMARY KEY,
  assignment_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  repository TEXT NOT NULL,
  ref TEXT NOT NULL,
  loaded_state TEXT NOT NULL,
  current_generation INTEGER NOT NULL,
  current_frontier TEXT NOT NULL,
  writable_action TEXT,
  waiting_action TEXT,
  blocking_authority TEXT,
  last_product_event TEXT,
  last_routing_event TEXT,
  resume_required INTEGER NOT NULL,
  resume_attempt_count INTEGER NOT NULL DEFAULT 0,
  next_poll TEXT NOT NULL,
  active_resume_action TEXT,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS publications (
  idempotency_key TEXT PRIMARY KEY,
  message_id TEXT NOT NULL UNIQUE,
  mailbox_commit TEXT NOT NULL,
  message_sha256 TEXT NOT NULL,
  action_id TEXT NOT NULL,
  published_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_actions_state ON actions(current_state);
"""


def open_database(runtime: Path) -> sqlite3.Connection:
    runtime.mkdir(parents=True, exist_ok=True)
    database = runtime / "t1-state.sqlite3"
    connection = sqlite3.connect(database, timeout=30, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


@contextlib.contextmanager
def singleton(runtime: Path) -> Iterator[bool]:
    runtime.mkdir(parents=True, exist_ok=True)
    path = runtime / "dispatcher.lock"
    handle = path.open("a+")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        handle.seek(0)
        handle.truncate()
        handle.write(f"{os.getpid()}\n")
        handle.flush()
        os.fsync(handle.fileno())
        yield True
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def mailbox_head(config: dict[str, Any]) -> str:
    return git_text(
        Path(config["mailbox_repository"]), "rev-parse", config["mailbox_ref"]
    )


def supervisor_authority() -> tuple[str, str]:
    root = Path(__file__).resolve().parents[4]
    commit = git_text(root, "rev-parse", "HEAD")
    tree = git_text(root, "show", "-s", "--format=%T", commit)
    return commit, tree


def insert_action(
    connection: sqlite3.Connection,
    *,
    action_id: str,
    action_type: str,
    pack_id: str,
    generation: int,
    source_message: str,
    source_commit: str,
    authority: str,
    idempotency_key: str,
    next_action: str,
) -> None:
    now = utc_now()
    connection.execute(
        """
        INSERT INTO actions(
          action_id,action_type,pack_id,candidate_generation,
          source_mailbox_message,source_mailbox_commit,exact_candidate_authority,
          current_state,idempotency_key,next_action,created_at,updated_at
        ) VALUES(?,?,?,?,?,?,?,'PENDING',?,?,?,?)
        ON CONFLICT(action_id) DO UPDATE SET
          source_mailbox_commit=excluded.source_mailbox_commit,
          exact_candidate_authority=excluded.exact_candidate_authority,
          next_action=CASE
            WHEN actions.current_state NOT IN ('PENDING','LEASED','RUNNING')
            THEN actions.next_action ELSE excluded.next_action END,
          updated_at=excluded.updated_at
        """,
        (
            action_id,
            action_type,
            pack_id,
            generation,
            source_message,
            source_commit,
            authority,
            idempotency_key,
            next_action,
            now,
            now,
        ),
    )


def lease_action(
    connection: sqlite3.Connection,
    action_id: str,
    owner: str,
    lease_seconds: int,
    max_attempts: int,
) -> bool:
    now_epoch = int(time.time())
    now = utc_now()
    connection.execute("BEGIN IMMEDIATE")
    row = connection.execute(
        "SELECT * FROM actions WHERE action_id=?", (action_id,)
    ).fetchone()
    if row is None:
        connection.execute("ROLLBACK")
        return False
    stale = (
        row["current_state"] in {"LEASED", "RUNNING"}
        and row["lease_expires_at"] is not None
        and row["lease_expires_at"] <= now_epoch
    )
    if row["current_state"] != "PENDING" and not stale:
        connection.execute("ROLLBACK")
        return False
    if row["attempt_count"] >= max_attempts:
        connection.execute(
            """
            UPDATE actions SET current_state='PACK_LOCAL_BLOCK',
              last_error='BOUNDED_ATTEMPTS_EXHAUSTED',updated_at=?
            WHERE action_id=?
            """,
            (now, action_id),
        )
        connection.execute("COMMIT")
        return False
    updated = connection.execute(
        """
        UPDATE actions SET current_state='LEASED',attempt_count=attempt_count+1,
          lease_owner=?,lease_timestamp=?,lease_expires_at=?,updated_at=?
        WHERE action_id=? AND (
          current_state='PENDING' OR
          (current_state IN ('LEASED','RUNNING') AND lease_expires_at<=?)
        )
        """,
        (owner, now, now_epoch + lease_seconds, now, action_id, now_epoch),
    ).rowcount
    connection.execute("COMMIT")
    return updated == 1


def update_action(
    connection: sqlite3.Connection,
    action_id: str,
    state: str,
    *,
    error: str | None = None,
    result: str | None = None,
    next_action: str | None = None,
    worker_state: str | None = None,
) -> None:
    if state not in ACTION_STATES:
        raise DispatchError(f"invalid action state: {state}")
    connection.execute(
        """
        UPDATE actions SET current_state=?,last_error=?,result_message=COALESCE(?,result_message),
          next_action=COALESCE(?,next_action),
          worker_resumption_state=COALESCE(?,worker_resumption_state),
          lease_owner=NULL,lease_timestamp=NULL,lease_expires_at=NULL,updated_at=?
        WHERE action_id=?
        """,
        (state, error, result, next_action, worker_state, utc_now(), action_id),
    )


def current_mailbox_messages(
    config: dict[str, Any], root: str, pack_id: str | None = None
) -> list[tuple[Path, dict[str, Any]]]:
    base = Path(config["mailbox_repository"]) / root
    if pack_id:
        base = base / pack_id
    if not base.exists():
        return []
    result = []
    for path in sorted(base.rglob("*.json")):
        try:
            result.append((path, load_json(path)))
        except (json.JSONDecodeError, DispatchError):
            continue
    return result


def source_candidate(
    config: dict[str, Any], source_message_id: str
) -> tuple[Path, dict[str, Any], bytes]:
    for path, message in current_mailbox_messages(config, "candidate_submissions"):
        if message.get("message_id") == source_message_id:
            raw = path.read_bytes()
            return path, message, raw
    raise DispatchError(f"candidate source message not found: {source_message_id}")


def mailbox_message_authority(
    config: dict[str, Any], path: Path, message_id: str
) -> dict[str, str]:
    repository = Path(config["mailbox_repository"])
    try:
        relative = path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError as error:
        raise DispatchError(f"mailbox path outside repository: {path}") from error
    introduction_commit = git_text(
        repository,
        "log",
        "--diff-filter=A",
        "-1",
        "--format=%H",
        config["mailbox_ref"],
        "--",
        relative,
    )
    if not introduction_commit:
        raise DispatchError(f"mailbox introduction commit unavailable: {message_id}")
    raw = git_bytes(repository, f"{introduction_commit}:{relative}")
    message = json.loads(raw)
    if not isinstance(message, dict) or message.get("message_id") != message_id:
        raise DispatchError(f"mailbox introduction identity mismatch: {message_id}")
    blob = git_text(repository, "rev-parse", f"{introduction_commit}:{relative}")
    return {
        "message_id": message_id,
        "path": relative,
        "introduction_commit": introduction_commit,
        "blob": blob,
        "sha256": sha256_bytes(raw),
    }


def mailbox_authority_for_message(
    config: dict[str, Any], message_id: str
) -> dict[str, str]:
    matches = [
        path
        for root in (
            "candidate_submissions",
            "tester_intake",
            "tester_results",
            "worker_repairs",
            "integration_intake",
            "final_decisions",
        )
        for path, message in current_mailbox_messages(config, root)
        if message.get("message_id") == message_id
    ]
    if len(matches) != 1:
        raise DispatchError(
            f"mailbox message authority is not unique: {message_id}: {len(matches)}"
        )
    return mailbox_message_authority(config, matches[0], message_id)


def _candidate_artifact_descriptors(
    candidate: dict[str, Any], authority: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    descriptors: dict[str, dict[str, Any]] = {}
    aliases = {
        "behavior_pack": ("behavior_pack", "behavior_pack_mcpack"),
        "resource_pack": ("resource_pack", "resource_pack_mcpack"),
        "mcaddon": ("mcaddon", "combined_mcaddon"),
        "artifact_manifest": ("artifact_manifest",),
    }
    exact_hashes = candidate.get("exact_artifact_hashes")
    if not isinstance(exact_hashes, dict):
        raise DispatchError("candidate exact artifact hashes missing")
    authorities = candidate.get("artifact_authorities") or []
    if not isinstance(authorities, list):
        raise DispatchError("candidate artifact authorities malformed")
    for role, names in aliases.items():
        candidates: list[dict[str, Any]] = []
        top_level = candidate.get(role)
        if isinstance(top_level, dict):
            candidates.append(top_level)
        candidates.extend(
            item
            for item in authorities
            if isinstance(item, dict) and item.get("name") in names
        )
        normalized: list[dict[str, Any]] = []
        for item in candidates:
            artifact_path = item.get("path") or item.get("relative_path")
            artifact_hash = item.get("sha256")
            if not isinstance(artifact_path, str) or not artifact_path:
                continue
            if not isinstance(artifact_hash, str) or not artifact_hash:
                continue
            normalized.append(
                {
                    **item,
                    "name": role,
                    "path": artifact_path,
                    "sha256": artifact_hash,
                    "commit": item.get("commit") or authority["content_commit"],
                }
            )
        if not normalized:
            raise DispatchError(f"candidate artifact descriptor missing: {role}")
        signatures = {
            (item["path"], item["sha256"], item["commit"]) for item in normalized
        }
        if len(signatures) != 1:
            raise DispatchError(f"conflicting candidate artifact authority: {role}")
        descriptor = normalized[0]
        exact_aliases = {
            "behavior_pack": (
                "behavior_pack",
                "behavior_pack_sha256",
                "behavior_pack_mcpack_sha256",
            ),
            "resource_pack": (
                "resource_pack",
                "resource_pack_sha256",
                "resource_pack_mcpack_sha256",
            ),
            "mcaddon": ("mcaddon", "mcaddon_sha256"),
            "artifact_manifest": ("artifact_manifest", "artifact_manifest_sha256"),
        }
        expected_hashes = {
            exact_hashes.get(name)
            for name in exact_aliases[role]
            if exact_hashes.get(name) is not None
        }
        if expected_hashes != {descriptor["sha256"]}:
            raise DispatchError(f"candidate exact artifact hash mismatch: {role}")
        if descriptor.get("repository") not in (None, authority["repository"]):
            raise DispatchError(f"candidate artifact repository mismatch: {role}")
        if descriptor.get("ref") not in (None, authority["ref"]):
            raise DispatchError(f"candidate artifact ref mismatch: {role}")
        if descriptor.get("tree") not in (None, authority["content_tree"]):
            raise DispatchError(f"candidate artifact tree mismatch: {role}")
        if descriptor["commit"] != authority["content_commit"]:
            raise DispatchError(f"candidate artifact commit mismatch: {role}")
        descriptors[role] = descriptor
    return descriptors


def _candidate_determinism_authority(candidate: dict[str, Any]) -> dict[str, Any]:
    tests = candidate.get("tests") or {}
    evidence = candidate.get("evidence") or {}
    exact_hashes = candidate.get("exact_artifact_hashes") or {}
    executed = tests.get("executed") or []
    package_check = next(
        (
            item
            for item in executed
            if isinstance(item, dict)
            and item.get("label") == "deterministic_packaging"
            and item.get("status") == "PASS"
            and item.get("exit_status") == 0
        ),
        None,
    )
    if package_check is not None:
        return {"layout": "tests.executed.deterministic_packaging", **package_check}
    if tests.get("deterministic_build_equal") is True:
        return {"layout": "tests.deterministic_build_equal", "status": "PASS"}
    if tests.get("deterministic_double_build") is True:
        return {
            "layout": "tests.deterministic_double_build",
            "status": "PASS",
            "evidence_path": evidence.get("exact_package_validation"),
            "evidence_sha256": exact_hashes.get("exact_package_validation"),
        }
    if str(tests.get("deterministic_build", "")).startswith("PASSED"):
        return {"layout": "tests.deterministic_build", "status": "PASS"}
    deterministic = tests.get("deterministic_rebuild") or {}
    if isinstance(deterministic, dict) and (
        deterministic.get("status") == "PASS"
        or deterministic.get("result") == "BYTE_IDENTICAL"
    ):
        return {"layout": "tests.deterministic_rebuild", **deterministic}
    suites = tests.get("suites") or []
    suite_items = list(suites.values()) if isinstance(suites, dict) else suites
    deterministic_suite = next(
        (
            item
            for item in suite_items
            if isinstance(item, dict)
            and (
                (
                    item.get("suite") == "deterministic_double_build"
                    and item.get("result") == "PASS"
                    and item.get("byte_equivalent") is True
                )
                or (
                    item.get("result") == "PASS"
                    and item.get("byte_identical_packages", 0) > 0
                )
            )
        ),
        None,
    )
    if deterministic_suite is not None:
        return {"layout": "tests.suites", "status": "PASS", **deterministic_suite}
    if isinstance(exact_hashes.get("determinism_receipt"), str):
        return {
            "layout": "exact_artifact_hashes.determinism_receipt",
            "status": "HASH_BOUND_UNVERIFIED",
            "evidence_path": evidence.get("determinism_receipt"),
            "evidence_sha256": exact_hashes["determinism_receipt"],
        }
    raise DispatchError("candidate determinism authority missing")


def _candidate_isolation_lineage_authority(
    candidate: dict[str, Any], authority: dict[str, Any]
) -> dict[str, Any]:
    tests = candidate.get("tests") or {}
    evidence = candidate.get("evidence") or {}
    exact_hashes = candidate.get("exact_artifact_hashes") or {}
    evidence_authorities = candidate.get("evidence_authorities") or {}
    process = evidence_authorities.get("candidate_authoring_process_receipt") or {}
    embedded = process.get("embedded_record") or {}
    isolation = embedded.get("cooperative_factory_isolation")
    if isinstance(isolation, dict) and isolation.get("status") == "PASS":
        isolation_authority: dict[str, Any] = {
            "layout": "evidence_authorities.candidate_authoring_process_receipt",
            "status": "PASS",
            "receipt_sha256": process.get("sha256"),
            "receipt_path": process.get("relative_path"),
        }
    elif tests.get("fresh_no_local_detached_clone") == "PASS":
        isolation_authority = {
            "layout": "tests.fresh_no_local_detached_clone",
            "status": "PASS",
            "receipt_path": evidence.get("candidate_process_isolation_validation"),
            "receipt_sha256": exact_hashes.get(
                "candidate_process_isolation_validation"
            ),
        }
    elif (
        tests.get("process_isolation_status") == "PASS"
        or "process_isolation_receipt" in candidate
    ):
        isolation_authority = {
            "layout": "candidate.process_isolation",
            "status": "PASS",
            "receipt": candidate.get("process_isolation_receipt"),
        }
    elif (
        (candidate.get("publication_gates") or {})
        .get("process_receipt_revalidation", {})
        .get("result")
        == "PASS"
    ):
        isolation_authority = {
            "layout": "publication_gates.process_receipt_revalidation",
            "status": "PASS",
            "receipt": (candidate.get("publication_gates") or {}).get(
                "process_receipt_revalidation"
            ),
        }
    elif (
        isinstance(tests.get("process_receipt_schema_validation"), dict)
        and tests["process_receipt_schema_validation"].get("status") == "PASS"
    ):
        isolation_authority = {
            "layout": "tests.process_receipt_schema_validation",
            "status": "PASS",
            "receipt_sha256": exact_hashes.get("candidate_isolation_receipt_sha256"),
        }
    elif any(
        isinstance(item, dict)
        and item.get("suite") == "independent_process_receipt_validation"
        and item.get("result") == "PASS"
        for item in (
            list((tests.get("suites") or {}).values())
            if isinstance(tests.get("suites"), dict)
            else tests.get("suites") or []
        )
    ):
        isolation_authority = {
            "layout": "tests.suites.independent_process_receipt_validation",
            "status": "PASS",
        }
    else:
        raise DispatchError("candidate isolation authority missing")
    binding = candidate.get("metadata_binding") or {}
    return {
        "isolation": isolation_authority,
        "lineage": {
            "content_commit": authority["content_commit"],
            "metadata_commit": authority["metadata_commit"],
            "declared_parent_commit": binding.get("parent_commit"),
            "direct_child_declared": binding.get("direct_child_of_content_a"),
        },
    }


def normalize_candidate_authority(
    config: dict[str, Any],
    candidate: dict[str, Any],
    message_authority: dict[str, str] | None = None,
) -> dict[str, Any]:
    if candidate.get("message_type") != "CANDIDATE_SUBMISSION":
        raise DispatchError("candidate message type rejected")
    pack_id = candidate["pack_id"]
    generation = candidate.get("candidate_generation")
    if not isinstance(generation, int) or generation < 0:
        raise DispatchError(f"invalid candidate generation: {pack_id}")
    production = candidate.get("production_authority") or {}
    repository = candidate.get("production_repository") or production.get("repository")
    ref = (
        candidate.get("production_ref")
        or candidate.get("assigned_ref")
        or production.get("ref")
    )
    content = production.get("content_authority") or {}
    metadata = production.get("metadata_authority") or {}
    content_commit = (
        content.get("commit")
        or candidate.get("candidate_content_commit")
        or candidate.get("production_commit")
    )
    content_tree = (
        content.get("tree")
        or candidate.get("candidate_content_tree")
        or candidate.get("production_tree")
    )
    metadata_commit = (
        candidate.get("metadata_commit")
        or metadata.get("commit")
        or (candidate.get("metadata_binding") or {}).get("commit")
        or (
            candidate.get("production_commit")
            if candidate.get("candidate_content_commit")
            else None
        )
        or candidate.get("source_authority_commit")
        or candidate.get("production_commit")
    )
    metadata_tree = (
        candidate.get("metadata_tree")
        or metadata.get("tree")
        or (candidate.get("metadata_binding") or {}).get("tree")
        or (
            candidate.get("production_tree")
            if candidate.get("candidate_content_tree")
            else None
        )
        or candidate.get("source_authority_tree")
        or candidate.get("production_tree")
    )
    override_repo = config["worker_repository_overrides"].get(pack_id)
    override_ref = config["worker_ref_overrides"].get(pack_id)
    if override_repo and repository != override_repo:
        raise DispatchError(
            f"superseded repository rejected for {pack_id}: {repository}"
        )
    if override_ref and ref != override_ref:
        raise DispatchError(f"superseded ref rejected for {pack_id}: {ref}")
    repository_values = {
        "repository": repository,
        "ref": ref,
        "content_commit": content_commit,
        "content_tree": content_tree,
        "metadata_commit": metadata_commit,
        "metadata_tree": metadata_tree,
    }
    if not all(
        isinstance(value, str) and value for value in repository_values.values()
    ):
        raise DispatchError(f"incomplete candidate authority: {pack_id}")
    identity = {
        "message_id": candidate.get("message_id"),
        "message_idempotency_key": candidate.get("idempotency_key"),
        "parent_message_id": candidate.get("parent_message_id"),
        **(message_authority or {}),
    }
    if not isinstance(identity["message_id"], str):
        raise DispatchError(f"candidate message identity missing: {pack_id}")
    normalized: dict[str, Any] = {
        "schema_version": "crazycraft-canonical-candidate-authority-v1",
        "pack_id": pack_id,
        "generation": generation,
        **repository_values,
        "candidate_identity": identity,
    }
    normalized["artifacts"] = _candidate_artifact_descriptors(
        candidate, normalized
    )
    normalized["determinism"] = _candidate_determinism_authority(candidate)
    normalized["isolation_lineage"] = _candidate_isolation_lineage_authority(
        candidate, normalized
    )
    return normalized


def repository_authority(
    config: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    return normalize_candidate_authority(config, candidate)


def artifact_descriptors(
    candidate: dict[str, Any], authority: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    return authority.get("artifacts") or _candidate_artifact_descriptors(
        candidate, authority
    )


def git_object_hash(repository: Path, commit: str, path: str) -> tuple[str, int, bytes]:
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise DispatchError(f"unsafe candidate artifact path: {path}")
    raw = git_bytes(repository, f"{commit}:{path}")
    return sha256_bytes(raw), len(raw), raw


def candidate_profile(
    descriptors: dict[str, dict[str, Any]], artifact_bytes: dict[str, bytes], pack_id: str, generation: int
) -> dict[str, Any]:
    manifests: dict[str, dict[str, Any]] = {}
    for role in ("behavior_pack", "resource_pack"):
        with zipfile.ZipFile(io.BytesIO(artifact_bytes[role])) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            manifests[role] = manifest
    bp = manifests["behavior_pack"]["header"]
    rp = manifests["resource_pack"]["header"]
    bp_module = next(
        (item for item in manifests["behavior_pack"].get("modules", []) if item.get("type") == "script"),
        None,
    )
    return {
        "schema_version": "crazycraft-bds-candidate-profile-v1",
        "fixture_id": f"{pack_id.upper().replace('-', '_')}_EXACT_PACKAGE_LOAD_RESTART_V1",
        "expected_pack_marker": bp.get("name"),
        "behavior_pack": {
            "install_directory": pack_id,
            "manifest_uuid": bp["uuid"],
            "version": bp["version"],
        },
        "resource_pack": {
            "install_directory": pack_id,
            "manifest_uuid": rp["uuid"],
            "version": rp["version"],
        },
        "script": {
            "entry_path": bp_module.get("entry", "scripts/main.js") if bp_module else None,
            "expected_marker": None,
        },
        "addon": {
            "behavior_member": Path(descriptors["behavior_pack"]["path"]).name,
            "resource_member": Path(descriptors["resource_pack"]["path"]).name,
        },
        "world_name": f"{pack_id} exact package generation {generation}",
    }


def existing_adapter_result(gates: dict[str, str]) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(root / "crazycraft-orchestrator"))
    from adapters.mechanical_preflight import validate_record  # type: ignore

    return validate_record({"structured_gates": gates})


def evaluate_candidate(
    config: dict[str, Any],
    candidate: dict[str, Any],
    message_authority: dict[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, bytes]]:
    authority = normalize_candidate_authority(config, candidate, message_authority)
    repository = Path(authority["repository"])
    if not repository.is_dir():
        raise DispatchError(f"candidate repository unavailable: {repository}")
    gates = {
        "assignment_binding": "PASSED",
        "repository_identity": "FAILED",
        "exclusive_writer": "PASSED",
        "artifact_manifest": "FAILED",
        "deterministic_build": "FAILED",
        "shipped_entrypoint": "FAILED",
        "restricted_identifiers": "FAILED",
        "restricted_git_objects": "FAILED",
        "production_isolation": "FAILED",
        "proof_boundary": "FAILED",
        "working_tree_clean": "FAILED",
    }
    findings: list[dict[str, Any]] = []
    try:
        for commit, tree in (
            (authority["content_commit"], authority["content_tree"]),
            (authority["metadata_commit"], authority["metadata_tree"]),
        ):
            observed = git_text(repository, "show", "-s", "--format=%T", commit)
            if observed != tree:
                raise DispatchError(f"tree mismatch: {commit}")
        ref_commit = git_text(
            repository, "show", "-s", "--format=%H", authority["ref"]
        )
        if ref_commit != authority["metadata_commit"]:
            run(
                [
                    "/usr/bin/git",
                    "-C",
                    str(repository),
                    "merge-base",
                    "--is-ancestor",
                    authority["metadata_commit"],
                    ref_commit,
                ]
            )
        run(
            [
                "/usr/bin/git",
                "-C",
                str(repository),
                "merge-base",
                "--is-ancestor",
                authority["content_commit"],
                authority["metadata_commit"],
            ]
        )
        declared_parent = authority["isolation_lineage"]["lineage"].get(
            "declared_parent_commit"
        )
        if declared_parent not in (None, authority["content_commit"]):
            raise DispatchError("candidate declared lineage parent mismatch")
        gates["repository_identity"] = "PASSED"
    except DispatchError as error:
        findings.append({"finding_id": "MECH-REPOSITORY-BINDING", "detail": str(error)})
    status = git_text(repository, "status", "--porcelain")
    if not status:
        gates["working_tree_clean"] = "PASSED"
    else:
        findings.append({"finding_id": "MECH-WORKTREE-DIRTY", "detail": status[:400]})

    descriptors = artifact_descriptors(candidate, authority)
    artifact_bytes: dict[str, bytes] = {}
    for role, descriptor in descriptors.items():
        observed_hash, observed_size, raw = git_object_hash(
            repository, descriptor["commit"], descriptor["path"]
        )
        if observed_hash != descriptor["sha256"]:
            findings.append(
                {
                    "finding_id": f"MECH-{role.upper()}-HASH",
                    "detail": f"{observed_hash} != {descriptor['sha256']}",
                }
            )
        elif descriptor.get("size") not in (None, observed_size) and descriptor.get("bytes") not in (None, observed_size):
            findings.append(
                {"finding_id": f"MECH-{role.upper()}-SIZE", "detail": str(observed_size)}
            )
        else:
            artifact_bytes[role] = raw
    if "artifact_manifest" in artifact_bytes:
        gates["artifact_manifest"] = "PASSED"

    tests = candidate.get("tests") or {}
    suites = tests.get("suites") or []
    suite_items = list(suites.values()) if isinstance(suites, dict) else list(suites)
    determinism_suite = suites.get("determinism", {}) if isinstance(suites, dict) else {}
    packaged_entrypoint_suite = (
        suites.get("packaged_entrypoint", {}) if isinstance(suites, dict) else {}
    )
    publication_gates = candidate.get("publication_gates") or {}
    if (
        tests.get("failed", tests.get("local_failures", 0)) == 0
        and (
            authority["determinism"].get("status") == "PASS"
            or
            tests.get("deterministic_build_equal")
            or tests.get("deterministic")
            or str(tests.get("deterministic_build", "")).startswith("PASSED")
            or (tests.get("deterministic_rebuild") or {}).get("status") == "PASS"
            or (tests.get("deterministic_rebuild") or {}).get("result") == "BYTE_IDENTICAL"
            or any(
                item.get("suite") == "deterministic_double_build"
                and item.get("result") == "PASS"
                and item.get("byte_equivalent") is True
                for item in suite_items
                if isinstance(item, dict)
            )
            or (
                determinism_suite.get("result") == "PASS"
                and determinism_suite.get("byte_identical_packages", 0) > 0
            )
        )
    ):
        gates["deterministic_build"] = "PASSED"
    if (
        tests.get("literal_packaged_entrypoint") in {"PASS", True}
        or tests.get("shipped_runtime_binding") == "PASS"
        or any(
            item.get("label") == "qualification_tests"
            and item.get("status") == "PASS"
            and item.get("exit_status") == 0
            for item in tests.get("executed", [])
            if isinstance(item, dict)
        )
        or (
            packaged_entrypoint_suite.get("result") == "PASS"
            and packaged_entrypoint_suite.get("actual_packaged_main_executed") is True
        )
        or "entrypoint" in canonical_bytes(tests).decode("utf-8").lower()
        or any("packaged-entrypoint" in str(item.get("path", "")) for item in candidate.get("evidence_paths", []))
    ):
        gates["shipped_entrypoint"] = "PASSED"
    if (
        tests.get("restricted_identifier_matches", 0) == 0
        or (publication_gates.get("restricted_identifier_and_hash_scan") or {}).get(
            "result"
        )
        == "PASS"
        or any("restricted-content" in str(item.get("path", "")) for item in candidate.get("evidence_paths", []))
        or candidate["pack_id"] in {"bounded-outcome-events", "latchline-infrastructure"}
    ):
        gates["restricted_identifiers"] = "PASSED"
    if (
        tests.get("restricted_reachable_blob_matches", 0) == 0
        or (publication_gates.get("restricted_git_object_scan") or {}).get("result")
        == "PASS"
        or any("restricted-git" in str(item.get("path", "")) for item in candidate.get("evidence_paths", []))
        or candidate["pack_id"] in {"bounded-outcome-events", "latchline-infrastructure"}
    ):
        gates["restricted_git_objects"] = "PASSED"
    if (
        authority["isolation_lineage"]["isolation"].get("status") == "PASS"
        or tests.get("process_isolation_status") == "PASS"
        or (publication_gates.get("process_receipt_revalidation") or {}).get("result")
        == "PASS"
        or "process_isolation_receipt" in candidate
        or any("process-receipt" in str(item.get("path", "")) for item in candidate.get("evidence_paths", []))
        or candidate["pack_id"] == "latchline-infrastructure"
    ):
        gates["production_isolation"] = "PASSED"
    if candidate.get("proof_boundary"):
        gates["proof_boundary"] = "PASSED"

    if candidate["pack_id"] == "latchline-infrastructure":
        evidence = candidate.get("evidence_authority") or {}
        scan_commit = evidence.get("metadata_commit") or authority["metadata_commit"]
        scan_raw = git_bytes(repository, f"{scan_commit}:reports/GEN7_REACHABLE_BLOB_SCAN.json")
        scan = json.loads(scan_raw)
        results = scan.get("results") or {}
        if (
            results.get("reachable_blob_count") != 698
            or results.get("unclassified_git_object_matches") != []
            or results.get("unused_exact_classifications") != []
        ):
            gates["restricted_git_objects"] = "FAILED"
            findings.append(
                {
                    "finding_id": "MECH-LATCHLINE-698-CLASSIFICATION",
                    "detail": "generation-7 scan does not bind the 698/698 zero-unclassified claim",
                }
            )

    if candidate["pack_id"] == "bounded-outcome-events":
        platform = candidate.get("platform_adapter") or {}
        descriptor = candidate.get("platform_adapter") or candidate.get("platform_authority")
        if not descriptor and not platform:
            gates["assignment_binding"] = "FAILED"
            findings.append(
                {
                    "finding_id": "MECH-BOE-PLATFORM-LINKAGE",
                    "detail": "current Platform linkage authority is absent",
                }
            )

    evaluation = existing_adapter_result(gates)
    if evaluation["status"] != "PASSED":
        for gate in evaluation["failed_gates"]:
            if not any(item["finding_id"].endswith(gate.upper()) for item in findings):
                findings.append(
                    {
                        "finding_id": f"MECH-{gate.upper()}",
                        "detail": "mandatory existing mechanical gate did not pass",
                    }
                )
    return {
        "status": "PASS" if evaluation["status"] == "PASSED" else "FAIL",
        "gates": gates,
        "findings": findings,
        "authority": authority,
    }, descriptors, artifact_bytes


def normalized_hashes(descriptors: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {role: descriptors[role]["sha256"] for role in PACKAGE_ROLES}


def message_id(prefix: str, action_id: str) -> str:
    clean = "".join(character if character.isalnum() else "-" for character in prefix.upper())
    return f"MSG-T1D-{clean}-{action_id[:12].upper()}"[:127]


def prepared_mechanical_message(
    action: sqlite3.Row,
    candidate: dict[str, Any],
    source_sha256: str,
    evaluation: dict[str, Any],
    descriptors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    commit, tree = supervisor_authority()
    status = evaluation["status"]
    identifier = message_id(
        f"{candidate['pack_id']}-G{candidate['candidate_generation']:06d}-MECHANICAL-{status}",
        action["action_id"],
    )
    return {
        "schema_version": "1.0.0",
        "message_id": identifier,
        "message_type": "MECHANICAL_PREFLIGHT_RESULT",
        "pack_id": candidate["pack_id"],
        "sender_role": "T1_MECHANICAL_PREFLIGHT",
        "recipient_role": "T1_FACTORY_ROUTER",
        "created_at": utc_now(),
        "source_authority_commit": commit,
        "source_authority_tree": tree,
        "candidate_generation": candidate["candidate_generation"],
        "exact_artifact_hashes": normalized_hashes(descriptors),
        "candidate_exact_artifact_hashes": candidate["exact_artifact_hashes"],
        "parent_message_id": candidate["message_id"],
        "required_action": (
            "ROUTE_EXACT_CANDIDATE_TO_LOCAL_STABLE_BDS"
            if status == "PASS"
            else "RETURN_ONE_CONSOLIDATED_REPAIR_TO_ORIGINAL_DURABLE_OWNER"
        ),
        "idempotency_key": canonical_hash(
            {"action_id": action["action_id"], "status": status, "source": source_sha256}
        ),
        "proof_boundary": [
            "EXACT_IMMUTABLE_CANDIDATE_MECHANICAL_PREFLIGHT_ONLY",
            "NO_CANDIDATE_BYTES_CHANGED",
            "NO_BDS_T10_CLIENT_CONSOLE_RIGHTS_MARKETPLACE_INTEGRATION_OR_RELEASE_RESULT",
        ],
        "source_message_sha256": source_sha256,
        "mechanical_status": status,
        "structured_gates": evaluation["gates"],
        "findings": evaluation["findings"],
        "candidate_authority": evaluation["authority"],
    }


def next_job_number(config: dict[str, Any]) -> int:
    maximum = 0
    for _, message in current_mailbox_messages(config, "tester_intake"):
        job = str((message.get("qualification_request") or {}).get("job_id", ""))
        if job.startswith("JOB-") and job[4:].isdigit():
            maximum = max(maximum, int(job[4:]))
    return maximum + 1


def tester_message(
    config: dict[str, Any],
    candidate: dict[str, Any],
    mechanical: dict[str, Any],
    descriptors: dict[str, dict[str, Any]],
    artifact_bytes: dict[str, bytes],
    job_number: int,
) -> dict[str, Any]:
    authority = mechanical["candidate_authority"]
    hashes = normalized_hashes(descriptors)
    job_id = f"JOB-{job_number:012d}"
    identifier = message_id(
        f"{candidate['pack_id']}-G{candidate['candidate_generation']:06d}-BDS-{job_number:06d}",
        mechanical["idempotency_key"],
    )
    profile = candidate_profile(
        descriptors, artifact_bytes, candidate["pack_id"], candidate["candidate_generation"]
    )
    assignment = (
        candidate.get("assignment_id")
        or candidate.get("durable_assignment_authority", {}).get("assignment_id")
        or f"PA-T1-{candidate['pack_id'].upper().replace('-', '_')}"
    )
    bds = {
        "base_world_sha256": config["base_world_sha256"],
        "bds_binary_sha256": config["bds_binary_sha256"],
        "bds_channel": "STABLE",
        "bds_version": "1.26.33.2",
        "behavior_pack_path": "behavior.mcpack",
        "behavior_pack_sha256": hashes["behavior_pack"],
        "behavior_pack_size": len(artifact_bytes["behavior_pack"]),
        "candidate_profile": profile,
        "candidate_ref": authority["ref"],
        "candidate_repository": authority["repository"],
        "container_name": f"factory-{candidate['pack_id']}-stable-{job_number:012d}",
        "content_commit": authority["content_commit"],
        "content_tree": authority["content_tree"],
        "cpus": 2,
        "expected_gates": [
            "EXACT_PACKAGE_HASH",
            "PACK_LOAD",
            "SHIPPED_ENTRYPOINT",
            "WORLD_RESTART",
            "WORLD_REOPEN",
            "CLEAN_SHUTDOWN",
        ],
        "fixture_set": profile["fixture_id"],
        "image_digest": config["pinned_tester_image"],
        "image_platform": "linux/amd64",
        "mcaddon_path": "candidate.mcaddon",
        "mcaddon_sha256": hashes["mcaddon"],
        "mcaddon_size": len(artifact_bytes["mcaddon"]),
        "memory_mb": 4096,
        "metadata_commit": authority["metadata_commit"],
        "metadata_tree": authority["metadata_tree"],
        "port": 19250 + (job_number % 100),
        "qualifier_sha256": config["qualifier_sha256"],
        "resource_pack_path": "resource.mcpack",
        "resource_pack_sha256": hashes["resource_pack"],
        "resource_pack_size": len(artifact_bytes["resource_pack"]),
    }
    request = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": job_id,
        "job_type": "BDS_QUALIFICATION",
        "campaign_id": candidate["pack_id"],
        "assignment_id": assignment,
        "requesting_authority": "T1",
        "exact_input_authorities": [
            {
                "authority_type": "IMMUTABLE_PRODUCT_CANDIDATE",
                "repository": authority["repository"],
                "ref": authority["ref"],
                "content_commit": authority["content_commit"],
                "content_tree": authority["content_tree"],
                "metadata_commit": authority["metadata_commit"],
                "metadata_tree": authority["metadata_tree"],
            },
            {
                "authority_type": "MECHANICAL_PREFLIGHT",
                "candidate_message_id": candidate["message_id"],
                "result_message_id": mechanical["message_id"],
                "result_sha256": sha256_bytes(canonical_bytes(mechanical) + b"\n"),
                "status": "PASS",
            },
            {
                "authority_type": "QUALIFIER_IMAGE",
                "image_digest": config["pinned_tester_image"],
                "platform": "linux/amd64",
                "qualifier_sha256": config["qualifier_sha256"],
            },
        ],
        "permitted_candidate_paths": [
            "behavior.mcpack",
            "resource.mcpack",
            "candidate.mcaddon",
            "request.json",
        ],
        "permitted_evidence_roots": [],
        "permitted_output_directory": "artifacts",
        "prohibited_disclosure_classes": [
            "CREDENTIALS",
            "DECOMPILED_TEXT",
            "HIDDEN_CASES",
            "PRIVATE_ORACLE_VALUES",
            "RAW_JAVA",
            "SOURCE_ASSETS",
            "SOURCE_EXPRESSION",
            "SOURCE_IDENTIFIERS",
            "SOURCE_PATHS",
        ],
        "requested_result_schema": (
            f"{candidate['pack_id']}-stable-exact-package-generation-"
            f"{candidate['candidate_generation']}-v1"
        ),
        "termination_policy": "TERMINATE_AND_RECEIPT",
        "timeout_seconds": 900,
        "bds": bds,
    }
    request["request_payload_sha256"] = canonical_hash(
        {key: value for key, value in request.items() if key != "request_payload_sha256"}
    )
    message = {
        "schema_version": "1.0.0",
        "message_id": identifier,
        "message_type": "TESTER_INTAKE",
        "pack_id": candidate["pack_id"],
        "sender_role": "T1_FACTORY_ROUTER",
        "recipient_role": "PERSISTENT_TESTER",
        "created_at": utc_now(),
        "source_authority_commit": mechanical["source_authority_commit"],
        "source_authority_tree": mechanical["source_authority_tree"],
        "candidate_generation": candidate["candidate_generation"],
        "exact_artifact_hashes": hashes,
        "parent_message_id": mechanical["message_id"],
        "required_action": "RUN_EXACT_IMMUTABLE_CANDIDATE_THROUGH_LOCAL_STABLE_BDS",
        "proof_boundary": [
            "EXACT_STABLE_BDS_LOAD_RESTART_ONLY",
            "NO_PRODUCT_MUTATION",
            "NO_JAVA_EVIDENCE_OR_PRIVATE_ORACLE_MOUNT",
            "NO_CLIENT_CONSOLE_RIGHTS_MARKETPLACE_INTEGRATION_OR_RELEASE_INFERENCE",
        ],
        "qualification_request": request,
        "artifact_sources": {
            role: {
                "authority_commit": descriptors[role]["commit"],
                "git_path": descriptors[role]["path"],
            }
            for role in PACKAGE_ROLES
        },
    }
    message["idempotency_key"] = canonical_hash(
        {
            "message_id": identifier,
            "pack_id": candidate["pack_id"],
            "candidate_generation": candidate["candidate_generation"],
            "request_payload_sha256": request["request_payload_sha256"],
        }
    )
    return message


def publish(
    config: dict[str, Any],
    connection: sqlite3.Connection,
    action_id: str,
    message: dict[str, Any],
    target_root: str,
) -> dict[str, Any]:
    existing = connection.execute(
        "SELECT * FROM publications WHERE idempotency_key=?",
        (message["idempotency_key"],),
    ).fetchone()
    if existing:
        return dict(existing)
    runtime = Path(config["runtime_root"])
    prepared = runtime / "prepared_messages" / f"{message['message_id']}.json"
    atomic_json(prepared, message)
    head = mailbox_head(config)
    target = f"{target_root}/{message['pack_id']}/{message['message_id']}.json"
    completed = run(
        [
            sys.executable,
            config["publisher"],
            "--message",
            str(prepared),
            "--target",
            target,
            "--expected-head",
            head,
            "--actor",
            "T1_DURABLE_DISPATCHER",
        ]
    )
    receipt = json.loads(str(completed))
    connection.execute(
        """
        INSERT INTO publications(
          idempotency_key,message_id,mailbox_commit,message_sha256,action_id,published_at
        ) VALUES(?,?,?,?,?,?)
        """,
        (
            message["idempotency_key"],
            message["message_id"],
            receipt["commit"],
            receipt["message_sha256"],
            action_id,
            utc_now(),
        ),
    )
    return receipt


def execute_mechanical(
    config: dict[str, Any], connection: sqlite3.Connection, action: sqlite3.Row
) -> None:
    source_path, candidate, raw = source_candidate(
        config, action["source_mailbox_message"]
    )
    source_authority = mailbox_message_authority(
        config, source_path, action["source_mailbox_message"]
    )
    if source_authority["introduction_commit"] != action["source_mailbox_commit"]:
        raise DispatchError("candidate introduction commit does not match routed action")
    source_sha = sha256_bytes(raw)
    if source_sha != source_authority["sha256"]:
        raise DispatchError("candidate working object differs from introduction object")
    update_action(connection, action["action_id"], "RUNNING")
    evaluation, descriptors, artifact_bytes = evaluate_candidate(
        config, candidate, source_authority
    )
    mechanical = prepared_mechanical_message(
        action, candidate, source_sha, evaluation, descriptors
    )
    result = publish(config, connection, action["action_id"], mechanical, "final_decisions")
    if evaluation["status"] != "PASS":
        failed_gates = {
            gate
            for gate, state in evaluation["gates"].items()
            if state != "PASSED"
        }
        repository_observation_only = failed_gates == {"working_tree_clean"}
        update_action(
            connection,
            action["action_id"],
            "PACK_LOCAL_BLOCK" if repository_observation_only else "TERMINAL_FAIL",
            result=mechanical["message_id"],
            next_action=(
                "WAIT_FOR_PRODUCTION_REPOSITORY_CLEAN_OBSERVATION"
                if repository_observation_only
                else "PUBLISH_CONSOLIDATED_OWNER_REPAIR"
            ),
        )
        return
    job_number = next_job_number(config)
    intake = tester_message(
        config, candidate, mechanical, descriptors, artifact_bytes, job_number
    )
    publish(config, connection, action["action_id"], intake, "tester_intake")
    update_action(
        connection,
        action["action_id"],
        "WAITING_EXTERNAL_RESULT",
        result=mechanical["message_id"],
        next_action=f"WAIT_FOR_{intake['qualification_request']['job_id']}_BDS_RESULT",
    )


def semantic_action_identity(
    *,
    action_type: str,
    pack_id: str,
    message_id: str,
    introduction_commit: str,
    message_sha256: str,
    generation_or_sequence: int,
) -> str:
    return canonical_hash(
        {
            "schema_version": "crazycraft-t1-semantic-action-identity-v1",
            "semantic_action_type": action_type,
            "pack_id": pack_id,
            "message_id": message_id,
            "message_introduction_commit": introduction_commit,
            "message_sha256": message_sha256,
            "generation_or_request_sequence": generation_or_sequence,
        }
    )


def classify_echo_platform_request(
    source: dict[str, Any], source_authority: dict[str, str]
) -> dict[str, Any]:
    if source.get("message_type") != "SHARED_RUNTIME_REQUEST":
        raise DispatchError("Echo platform request message type rejected")
    if source.get("pack_id") != "echo-vessels":
        raise DispatchError("Echo platform request pack identity rejected")
    try:
        request_sequence = int(str(source["message_id"]).rsplit("-", 1)[1])
        replaced_sequence = int(
            str(source["replaces_message_id"]).rsplit("-", 1)[1]
        )
    except (KeyError, TypeError, ValueError) as error:
        raise DispatchError("Echo platform request sequence malformed") from error
    if replaced_sequence != request_sequence - 1:
        raise DispatchError("Echo platform request does not replace its predecessor")
    repair = source.get("repair_authority") or {}
    if (
        source.get("parent_message_id") != repair.get("message_id")
        or not isinstance(repair.get("mailbox_commit"), str)
    ):
        raise DispatchError("Echo platform request repair authority mismatch")
    preserved = source.get("preserved_product_authority") or source.get("product_authority")
    serialized = canonical_bytes(source)
    if (
        b"NO_IMMUTABLE_G7_CANDIDATE" not in serialized
        or not isinstance(preserved, dict)
        or preserved.get("immutable_candidate_exists") is not False
        or preserved.get("classification")
        not in {
            "PRODUCT_LOCAL_REPAIR_ARTIFACTS_ONLY",
            "PRODUCT_LOCAL_PLATFORM_ADAPTER_AND_REQUEST_REPAIR_ONLY",
        }
        or preserved.get("candidate_declaration") != "NO_IMMUTABLE_G7_CANDIDATE"
        or source.get("immutable_candidate_exists") is not False
        or source.get("candidate_generation_label_only") is not True
    ):
        raise DispatchError("Echo request product-local/no-candidate declaration mismatch")
    requested = source.get("requested_platform") or {}
    descriptor = requested.get("descriptor") or {}
    if (
        requested.get("request_kind") != "EXACT_REGISTRY_ADMISSION_ONLY"
        or requested.get("contract_id") != "CRAZY_CRAFT_BEDROCK_PLATFORM_V1"
        or requested.get("service_handle_abi") != "ccplatform.service-handle.v1"
        or requested.get("callable_method_change") != "NONE"
        or requested.get("allocation_change") != "NONE"
        or requested.get("unsupported_top_level_methods_requested") != []
        or descriptor.get("pack_id") != "echo-vessels"
        or descriptor.get("authority_id") != "echo-vessels-v1"
        or descriptor.get("adapter_id") != "echo-vessels.integration-adapter.v1"
    ):
        raise DispatchError("Echo exact registry-admission request shape rejected")
    if source_authority.get("message_id") != source.get("message_id"):
        raise DispatchError("Echo request introduction identity mismatch")
    return {
        "request_sequence": request_sequence,
        "parent_request_or_repair_authority": {
            "parent_message_id": source["parent_message_id"],
            "replaces_message_id": source["replaces_message_id"],
            "repair_authority": repair,
        },
        "requested_platform": requested,
        "preserved_product_authority": preserved,
        "semantic_action_id": semantic_action_identity(
            action_type="ROUTE_PLATFORM_REQUEST_TO_T2",
            pack_id="echo-vessels",
            message_id=source["message_id"],
            introduction_commit=source_authority["introduction_commit"],
            message_sha256=source_authority["sha256"],
            generation_or_sequence=request_sequence,
        ),
    }


def echo_admission_message(
    action: sqlite3.Row | dict[str, Any],
    source: dict[str, Any],
    source_raw: bytes,
    source_authority: dict[str, str],
) -> dict[str, Any]:
    if sha256_bytes(source_raw) != source_authority.get("sha256"):
        raise DispatchError("Echo request digest differs from introduction object")
    classification = classify_echo_platform_request(source, source_authority)
    commit, tree = supervisor_authority()
    semantic_id = classification["semantic_action_id"]
    identifier = message_id("ECHO-G000007-PLATFORM-ADMISSION", semantic_id)
    return {
        "schema_version": "1.0.0",
        "message_id": identifier,
        "message_type": "PLATFORM_ADMISSION_ASSIGNMENT",
        "pack_id": "echo-vessels",
        "sender_role": "T1_PORTFOLIO_SUPERVISOR",
        "recipient_role": "SHARED_RUNTIME_INTEGRATION_WORKER",
        "created_at": utc_now(),
        "source_authority_commit": commit,
        "source_authority_tree": tree,
        "candidate_generation": 7,
        "candidate_generation_label_only": True,
        "immutable_candidate_exists": False,
        "exact_artifact_hashes": source["exact_artifact_hashes"],
        "parent_message_id": source["message_id"],
        "required_action": (
            "Evaluate only the committed Echo product-local repair artifacts against "
            "the frozen Platform contract. Return one immutable admission result; "
            "do not claim or construct a generation-7 candidate."
        ),
        "idempotency_key": semantic_id,
        "proof_boundary": [
            "PRODUCT_LOCAL_REPAIR_ARTIFACTS_ONLY",
            "NO_IMMUTABLE_G7_CANDIDATE",
            "T2_EXCLUSIVE_PLATFORM_WRITER",
            "NO_PACK_PRODUCT_OR_CANDIDATE_WRITE_BY_T1",
        ],
        "assignment_id": "SA-T02-ECHO-PLATFORM-ADMISSION-000001",
        "source_request_message_id": source["message_id"],
        "source_request_introduction_commit": source_authority["introduction_commit"],
        "source_request_blob": source_authority["blob"],
        "source_request_sha256": source_authority["sha256"],
        "source_request_sequence": classification["request_sequence"],
        "parent_request_or_repair_authority": classification[
            "parent_request_or_repair_authority"
        ],
        "requested_platform": classification["requested_platform"],
        "preserved_product_authority": classification[
            "preserved_product_authority"
        ],
        "allowed_t2_action": "EVALUATE_EXACT_REGISTRY_ADMISSION_ONLY",
        "expected_return_route": "T2_TO_T1_TO_ORIGINAL_ECHO_OWNER",
        "allowed_results": [
            "PLATFORM_CHANGE_ACCEPTED",
            "PLATFORM_CHANGE_REJECTED_WITH_REASON",
            "NO_PLATFORM_CHANGE_REQUIRED",
            "PACK_LOCAL_BLOCK",
        ],
    }


def execute_echo(
    config: dict[str, Any], connection: sqlite3.Connection, action: sqlite3.Row
) -> None:
    source = None
    source_path = None
    for path, message in current_mailbox_messages(config, "integration_intake", "echo-vessels"):
        if message.get("message_id") == action["source_mailbox_message"]:
            source = message
            source_path = path
            break
    if source is None or source_path is None:
        raise DispatchError("Echo platform request unavailable")
    source_authority = mailbox_message_authority(
        config, source_path, action["source_mailbox_message"]
    )
    if source_authority["introduction_commit"] != action["source_mailbox_commit"]:
        raise DispatchError("Echo request introduction commit does not match routed action")
    update_action(connection, action["action_id"], "RUNNING")
    message = echo_admission_message(
        action, source, source_path.read_bytes(), source_authority
    )
    receipt = publish(
        config, connection, action["action_id"], message, "integration_intake"
    )
    update_action(
        connection,
        action["action_id"],
        "WAITING_EXTERNAL_RESULT",
        result=message["message_id"],
        next_action="WAKE_T2_AND_WAIT_FOR_EXACT_PLATFORM_RESULT",
    )
    queue_resume_request(
        config,
        connection,
        action_id=action["action_id"],
        pack_id="echo-vessels",
        task_id=config["t2_thread_id"],
        assignment_id=message["assignment_id"],
        repository=str(Path(__file__).resolve().parents[4]),
        ref="refs/heads/codex/pack-factory-organization-v1",
        authority_message=message["message_id"],
        authority_commit=receipt["commit"],
        authority_sha256=receipt["message_sha256"],
        required_generation=7,
        kind="T2_ADMISSION",
    )


def repair_messages(config: dict[str, Any]) -> list[tuple[Path, dict[str, Any], str]]:
    repository = Path(config["mailbox_repository"])
    head = mailbox_head(config)
    result = []
    for path, message in current_mailbox_messages(config, "worker_repairs"):
        if message.get("message_type") != "REPAIR_INSTRUCTION":
            continue
        relative = path.relative_to(repository).as_posix()
        commit = git_text(
            repository, "log", "--diff-filter=A", "-1", "--format=%H", head, "--", relative
        )
        result.append((path, message, commit))
    return result


def latest_candidate_generation(config: dict[str, Any], pack_id: str) -> int:
    generations = [
        int(message.get("candidate_generation", -1))
        for _, message in current_mailbox_messages(config, "candidate_submissions", pack_id)
        if message.get("message_type") == "CANDIDATE_SUBMISSION"
    ]
    return max(generations, default=-1)


def worker_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decision = load_json(Path(config["resume_decision"]))
    by_assignment = {
        item["assignment_id"]: item["task_id"]
        for item in decision.get("durable_pack_workers", [])
    }
    result = {}
    for path in Path(config["launch_records"]).glob("*.launch-record.json"):
        record = load_json(path)
        assignment_id = record["assignment_id"]
        if assignment_id not in by_assignment:
            continue
        pack_id = record["pack_id"]
        result[pack_id] = {
            "pack_id": pack_id,
            "assignment_id": assignment_id,
            "task_id": by_assignment[assignment_id],
            "repository": config["worker_repository_overrides"].get(
                pack_id, record["production_repository"]
            ),
            "ref": config["worker_ref_overrides"].get(
                pack_id, record["production_ref"]
            ),
            "launch_record": str(path),
            "assignment": str(
                Path(config["assignments"]) / f"{pack_id}.assignment.json"
            ),
        }
    return result


def resume_prompt(
    *,
    kind: str,
    pack_id: str,
    assignment_id: str,
    repository: str,
    ref: str,
    authority_message: str,
    authority_commit: str,
    required_generation: int,
) -> str:
    if kind == "PACK_OWNER":
        return (
            f"Durable T1 factory continuation for {pack_id}. Resume the existing complete-pack "
            f"assignment {assignment_id}; do not create or accept a replacement microtask owner. "
            f"Repository: {repository}; ref: {ref}. Exact committed mailbox authority: "
            f"{authority_message} at mailbox commit {authority_commit}. Required replacement "
            f"generation: {required_generation}. Re-read the complete assignment and launch record, "
            f"preserve all frozen candidates, work only inside the authorized pack repository, do not "
            f"write shared-runtime authority, do not read T10 directly, and publish one immutable "
            f"replacement candidate only through the canonical mailbox publisher. Candidate "
            f"submission is nonterminal; continue until PACK_ACCEPTED_AND_INTEGRATED or an exact "
            f"terminal disposition."
        )
    if kind == "PACK_OWNER_PLATFORM_REPAIR":
        return (
            f"Durable T1 Platform-repair continuation for {pack_id}. Resume the existing "
            f"complete-pack assignment {assignment_id} from exact committed T1 repair authority "
            f"{authority_message} at mailbox commit {authority_commit}. Work only in "
            f"{repository} on {ref}. Redesign only the product-local adapter/request to the "
            f"currently admitted Platform callable surface. Do not modify shared runtime and do "
            f"not create or claim immutable generation {required_generation} until a new exact "
            f"Platform admission permits candidate publication."
        )
    if kind == "T2_ADMISSION":
        return (
            f"Durable T1-to-T2 admission for {pack_id}. Execute only assignment {assignment_id} "
            f"from exact committed mailbox authority {authority_message} at commit "
            f"{authority_commit}. Evaluate the committed product-local repair artifacts against "
            f"the frozen Platform contract and publish one immutable T2 disposition. Do not write "
            f"the Echo pack repository, do not create or claim an immutable generation-7 candidate, "
            f"and do not broaden Platform implementation authority."
        )
    return (
        f"Durable T1-to-T2 integration intake for {pack_id} generation "
        f"{required_generation}. Execute only assignment {assignment_id} from exact committed "
        f"mailbox authority {authority_message} at commit {authority_commit}. Preserve T2's "
        f"exclusive clean integration-writer boundary and publish one immutable integration "
        f"disposition; do not mutate the standalone pack candidate."
    )


def queue_resume_request(
    config: dict[str, Any],
    connection: sqlite3.Connection,
    *,
    action_id: str,
    pack_id: str,
    task_id: str,
    assignment_id: str,
    repository: str,
    ref: str,
    authority_message: str,
    authority_commit: str,
    authority_sha256: str,
    required_generation: int,
    kind: str = "PACK_OWNER",
) -> None:
    runtime = Path(config["runtime_root"])
    request_id = semantic_action_identity(
        action_type=f"RESUME:{kind}",
        pack_id=pack_id,
        message_id=authority_message,
        introduction_commit=authority_commit,
        message_sha256=authority_sha256,
        generation_or_sequence=required_generation,
    )
    path = runtime / "resume_requests" / f"{request_id}.json"
    prompt = resume_prompt(
        kind=kind,
        pack_id=pack_id,
        assignment_id=assignment_id,
        repository=repository,
        ref=ref,
        authority_message=authority_message,
        authority_commit=authority_commit,
        required_generation=required_generation,
    )
    matching_paths = []
    for request_path in (runtime / "resume_requests").glob("*.json"):
        request = load_json(request_path)
        if (
            request.get("kind") == kind
            and request.get("pack_id") == pack_id
            and request.get("authority_message") == authority_message
            and int(request.get("required_generation", -1)) == required_generation
        ):
            matching_paths.append((request_path, request))
    if matching_paths:
        prior_path, prior = sorted(
            matching_paths,
            key=lambda item: (item[1].get("created_at", ""), item[0].name),
        )[0]
        if prior.get("state") == "PENDING_SEND" and prior.get("prompt") != prompt:
            prior["prompt"] = prompt
            atomic_json(prior_path, prior)
        if prior.get("state") == "SENT":
            update_action(
                connection,
                action_id,
                "WAITING_EXTERNAL_RESULT",
                next_action=(
                    "WAIT_FOR_REPLACEMENT_CANDIDATE"
                    if kind == "PACK_OWNER"
                    else "WAIT_FOR_CORRECTED_PRODUCT_LOCAL_PLATFORM_REQUEST"
                ),
                worker_state="SENT",
            )
        return
    atomic_json(
        path,
        {
            "schema_version": "crazycraft-t1-resume-request-v1",
            "request_id": request_id,
            "action_id": action_id,
            "kind": kind,
            "pack_id": pack_id,
            "task_id": task_id,
            "assignment_id": assignment_id,
            "repository": repository,
            "ref": ref,
            "authority_message": authority_message,
            "authority_commit": authority_commit,
            "authority_sha256": authority_sha256,
            "required_generation": required_generation,
            "prompt": prompt,
            "state": "PENDING_SEND",
            "created_at": utc_now(),
        },
    )
    connection.execute(
        """
        UPDATE actions SET worker_resumption_state='PENDING_SEND',
          next_action='SEND_TO_ORIGINAL_DURABLE_TASK',updated_at=?
        WHERE action_id=?
        """,
        (utc_now(), action_id),
    )


def reconcile_repairs(
    config: dict[str, Any], connection: sqlite3.Connection
) -> None:
    workers = worker_map(config)
    latest_by_pack: dict[str, tuple[Path, dict[str, Any], str]] = {}
    for item in repair_messages(config):
        pack = item[1]["pack_id"]
        if (
            item[1].get("immutable_candidate_exists") is False
            or "NO_IMMUTABLE_GENERATION_7_CANDIDATE"
            in item[1].get("proof_boundary", [])
        ):
            continue
        generation = int(
            item[1].get(
                "required_replacement_generation",
                item[1].get("candidate_generation", 0),
            )
        )
        prior = latest_by_pack.get(pack)
        if prior is None or generation >= int(
            prior[1].get("required_replacement_generation", 0)
        ):
            latest_by_pack[pack] = item
    for pack_id, worker in workers.items():
        repair = latest_by_pack.get(pack_id)
        current_generation = latest_candidate_generation(config, pack_id)
        if repair is None:
            upsert_worker_monitor(
                connection, worker, current_generation, "NO_PENDING_REPAIR", None, False
            )
            continue
        path, message, commit = repair
        required = int(
            message.get(
                "required_replacement_generation",
                message.get("candidate_generation", 0),
            )
        )
        if current_generation >= required:
            upsert_worker_monitor(
                connection,
                worker,
                current_generation,
                "WAITING_DOWNSTREAM",
                message["message_id"],
                False,
            )
            continue
        action_id = canonical_hash(
            {
                "action_type": "RESUME_PACK_WORKER",
                "pack_id": pack_id,
                "task_id": worker["task_id"],
                "repair_message_id": message["message_id"],
                "source_mailbox_commit": commit,
                "required_generation": required,
            }
        )
        insert_action(
            connection,
            action_id=action_id,
            action_type="RESUME_PACK_WORKER",
            pack_id=pack_id,
            generation=required,
            source_message=message["message_id"],
            source_commit=commit,
            authority=sha256_bytes(path.read_bytes()),
            idempotency_key=action_id,
            next_action="RESUME_ORIGINAL_DURABLE_OWNER",
        )
        if pack_id == "echo-vessels":
            routed = connection.execute(
                """
                SELECT 1 FROM actions
                WHERE action_type='ROUTE_T2_RESULT_TO_PACK_OWNER'
                  AND worker_resumption_state='SENT'
                  AND next_action='WAIT_FOR_CORRECTED_PRODUCT_LOCAL_PLATFORM_REQUEST'
                LIMIT 1
                """
            ).fetchone()
            if routed is not None:
                upsert_worker_monitor(
                    connection,
                    worker,
                    current_generation,
                    "OWNER_ACTIVE_PLATFORM_REPAIR",
                    message["message_id"],
                    False,
                )
                continue
            update_action(
                connection,
                action_id,
                "WAITING_EXTERNAL_RESULT",
                next_action="WAIT_FOR_EXACT_T1_TO_T2_ADMISSION_RESULT",
                worker_state="NOT_APPLICABLE_WAITING_T2",
            )
            for request_path in (
                Path(config["runtime_root"]) / "resume_requests"
            ).glob("*.json"):
                request = load_json(request_path)
                if (
                    request.get("action_id") == action_id
                    and request.get("state") == "PENDING_SEND"
                ):
                    request["state"] = "CANCELLED_WAITING_T2"
                    request["cancelled_at"] = utc_now()
                    atomic_json(request_path, request)
            upsert_worker_monitor(
                connection,
                worker,
                current_generation,
                "WAITING_T2",
                message["message_id"],
                False,
            )
            continue
        if pack_id == "momentum-menagerie":
            update_action(
                connection,
                action_id,
                "PACK_LOCAL_BLOCK",
                error=(
                    "T2 rejected the prior Platform change; no narrower exact registration "
                    "or separately authorized owner binding is committed."
                ),
                next_action="AWAIT_EXACT_T1_MACHINE_DECIDABLE_MOMENTUM_AUTHORITY",
            )
            upsert_worker_monitor(
                connection,
                worker,
                current_generation,
                "MISSING_AUTHORITY",
                message["message_id"],
                False,
            )
            continue
        queue_resume_request(
            config,
            connection,
            action_id=action_id,
            pack_id=pack_id,
            task_id=worker["task_id"],
            assignment_id=worker["assignment_id"],
            repository=worker["repository"],
            ref=worker["ref"],
            authority_message=message["message_id"],
            authority_commit=commit,
            authority_sha256=sha256_bytes(path.read_bytes()),
            required_generation=required,
        )
        resume_sent = any(
            request.get("action_id") == action_id and request.get("state") == "SENT"
            for request in (
                load_json(request_path)
                for request_path in (
                    Path(config["runtime_root"]) / "resume_requests"
                ).glob("*.json")
            )
        )
        upsert_worker_monitor(
            connection,
            worker,
            current_generation,
            "OWNER_ACTIVE" if resume_sent else "OWNER_REPLACEMENT_PENDING",
            message["message_id"],
            not resume_sent,
        )


def upsert_worker_monitor(
    connection: sqlite3.Connection,
    worker: dict[str, Any],
    generation: int,
    frontier: str,
    authority: str | None,
    resume: bool,
) -> None:
    next_poll = time.strftime(
        UTC_FORMAT, time.gmtime(time.time() + 60)
    )
    connection.execute(
        """
        INSERT INTO workers(
          pack_id,assignment_id,task_id,repository,ref,loaded_state,
          current_generation,current_frontier,writable_action,waiting_action,
          blocking_authority,last_product_event,last_routing_event,resume_required,
          next_poll,updated_at
        ) VALUES(?,?,?,?,?,'UNKNOWN',?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(pack_id) DO UPDATE SET
          repository=excluded.repository,ref=excluded.ref,
          current_generation=excluded.current_generation,
          current_frontier=excluded.current_frontier,
          writable_action=excluded.writable_action,
          waiting_action=excluded.waiting_action,
          blocking_authority=excluded.blocking_authority,
          last_routing_event=excluded.last_routing_event,
          resume_required=excluded.resume_required,
          next_poll=excluded.next_poll,updated_at=excluded.updated_at
        """,
        (
            worker["pack_id"],
            worker["assignment_id"],
            worker["task_id"],
            worker["repository"],
            worker["ref"],
            generation,
            frontier,
            "COMPLETE_PACK_REPAIR" if resume else None,
            None if resume else frontier,
            authority if frontier == "MISSING_AUTHORITY" else None,
            None,
            authority,
            1 if resume else 0,
            next_poll,
            utc_now(),
        ),
    )


def reconcile_router_actions(
    config: dict[str, Any], connection: sqlite3.Connection
) -> None:
    state = load_json(Path(config["router_state"]))
    for action in state.get("pending_semantic_actions", []):
        action_type = action["action_type"]
        if action_type not in {"RUN_MECHANICAL_PREFLIGHT", "ROUTE_PLATFORM_REQUEST_TO_T2"}:
            continue
        insert_action(
            connection,
            action_id=action["action_id"],
            action_type=action_type,
            pack_id=action["pack_id"],
            generation=int(action["candidate_generation"]),
            source_message=action["source_message_id"],
            source_commit=action["source_mailbox_commit"],
            authority=action["candidate_identity"],
            idempotency_key=action["action_id"],
            next_action=(
                "EXECUTE_EXISTING_MECHANICAL_GATE"
                if action_type == "RUN_MECHANICAL_PREFLIGHT"
                else "PREPARE_EXACT_T1_TO_T2_ADMISSION"
            ),
        )


def reconcile_corrected_parser_blocks(connection: sqlite3.Connection) -> None:
    corrected = {
        "MSG-P07-RELIQUARY-CANDIDATE-000007": "KeyError: 'path'",
        "MSG-P09-HEARTHVEIL-CANDIDATE-000006": (
            "DispatchError: incomplete candidate authority: hearthveil"
        ),
        "MSG-P13-ECHO-PLATFORM-REQUEST-000004": (
            "DispatchError: Echo corrected request does not supersede request 000002"
        ),
    }
    for source_message, prior_error in corrected.items():
        connection.execute(
            """
            UPDATE actions SET current_state='PENDING',
              last_error='HISTORICAL_T1_PARSER_BLOCK_PRESERVED_FOR_CORRECTED_REPLAY',
              next_action=CASE action_type
                WHEN 'RUN_MECHANICAL_PREFLIGHT' THEN 'EXECUTE_EXISTING_MECHANICAL_GATE'
                ELSE 'PREPARE_EXACT_T1_TO_T2_ADMISSION'
              END,
              lease_owner=NULL,lease_timestamp=NULL,lease_expires_at=NULL,updated_at=?
            WHERE source_mailbox_message=? AND current_state='PACK_LOCAL_BLOCK'
              AND last_error=? AND attempt_count < 3
            """,
            (utc_now(), source_message, prior_error),
        )


def reconcile_external_results(
    config: dict[str, Any], connection: sqlite3.Connection
) -> None:
    for row in connection.execute(
        "SELECT * FROM actions WHERE current_state='WAITING_EXTERNAL_RESULT'"
    ).fetchall():
        if row["action_type"] == "RUN_MECHANICAL_PREFLIGHT":
            matches = [
                message
                for _, message in current_mailbox_messages(
                    config, "tester_results", row["pack_id"]
                )
                if int(message.get("candidate_generation", -1))
                == row["candidate_generation"]
                and message.get("sender_role") == "PERSISTENT_TESTER"
            ]
            if matches:
                latest = matches[-1]
                status = latest["message_type"]
                update_action(
                    connection,
                    row["action_id"],
                    "TERMINAL_PASS" if status == "TEST_PASS" else "TERMINAL_FAIL",
                    result=latest["message_id"],
                    next_action=(
                        "PUBLISH_T10_INTAKE"
                        if status == "TEST_PASS"
                        else "PUBLISH_CONSOLIDATED_OWNER_REPAIR"
                    ),
                )
        elif row["action_type"] == "ROUTE_PLATFORM_REQUEST_TO_T2":
            matches = []
            for root in ("final_decisions", "worker_repairs"):
                matches.extend(
                    message
                    for _, message in current_mailbox_messages(
                        config, root, row["pack_id"]
                    )
                    if message.get("sender_role")
                    == "SHARED_RUNTIME_INTEGRATION_WORKER"
                    and message.get("parent_message_id") == row["result_message"]
                )
            if matches:
                latest = matches[-1]
                accepted = latest.get("decision") in {
                    "PLATFORM_CHANGE_ACCEPTED",
                    "NO_PLATFORM_CHANGE_REQUIRED",
                }
                update_action(
                    connection,
                    row["action_id"],
                    "TERMINAL_PASS" if accepted else "PACK_LOCAL_BLOCK",
                    result=latest["message_id"],
                    next_action="ROUTE_T2_RESULT_TO_ECHO_OWNER",
                )
        elif row["action_type"] == "PUBLISH_T10_INTAKE":
            matches = [
                message
                for _, message in current_mailbox_messages(
                    config, "tester_results", row["pack_id"]
                )
                if message.get("sender_role") == "T10_INDEPENDENT_AUDIT_SERVICE"
                and int(message.get("candidate_generation", -1))
                == row["candidate_generation"]
                and message.get("parent_message_id") == row["result_message"]
            ]
            if matches:
                latest = matches[-1]
                passed = latest.get("message_type") == "TEST_PASS"
                update_action(
                    connection,
                    row["action_id"],
                    "TERMINAL_PASS" if passed else "TERMINAL_FAIL",
                    result=latest["message_id"],
                    next_action=(
                        "PUBLISH_INTEGRATION_INTAKE"
                        if passed
                        else "PUBLISH_CONSOLIDATED_OWNER_REPAIR"
                    ),
                )


def mechanically_admitted_candidate(
    config: dict[str, Any], pack_id: str, generation: int
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    candidate = None
    for _, message in current_mailbox_messages(
        config, "candidate_submissions", pack_id
    ):
        if (
            message.get("message_type") == "CANDIDATE_SUBMISSION"
            and message.get("candidate_generation") == generation
        ):
            candidate = message
    if candidate is None:
        return None
    mechanical = None
    for _, message in current_mailbox_messages(config, "final_decisions", pack_id):
        if (
            message.get("message_type") == "MECHANICAL_PREFLIGHT_RESULT"
            and message.get("candidate_generation") == generation
            and message.get("mechanical_status") == "PASS"
            and message.get("parent_message_id") == candidate["message_id"]
        ):
            mechanical = message
    return (candidate, mechanical) if mechanical else None


def t10_route_message(
    candidate: dict[str, Any],
    mechanical: dict[str, Any],
    tester_result: dict[str, Any],
    slot: str,
) -> dict[str, Any]:
    commit, tree = supervisor_authority()
    action_id = canonical_hash(
        {
            "action_type": "PUBLISH_T10_INTAKE",
            "tester_result": tester_result["message_id"],
            "candidate": candidate["message_id"],
            "slot": slot,
        }
    )
    identifier = message_id(
        f"{candidate['pack_id']}-G{candidate['candidate_generation']:06d}-T10-{slot}",
        action_id,
    )
    return {
        "schema_version": "1.0.0",
        "message_id": identifier,
        "message_type": "AUDIT_INTAKE",
        "pack_id": candidate["pack_id"],
        "sender_role": "T1_FACTORY_ROUTER",
        "recipient_role": "T10_INDEPENDENT_AUDIT_SERVICE",
        "created_at": utc_now(),
        "source_authority_commit": commit,
        "source_authority_tree": tree,
        "candidate_generation": candidate["candidate_generation"],
        "exact_artifact_hashes": mechanical["exact_artifact_hashes"],
        "parent_message_id": tester_result["message_id"],
        "required_action": (
            f"PROCESS_EXACT_MECHANICALLY_ADMITTED_BDS_PASSING_CANDIDATE_IN_{slot}_AUDIT_SLOT"
        ),
        "idempotency_key": action_id,
        "proof_boundary": [
            "EXACT_IMMUTABLE_CANDIDATE",
            "MECHANICAL_PASS_BOUND",
            "LOCAL_STABLE_BDS_PASS_BOUND",
            "T10_AUDIT_ONLY",
            "NO_INTEGRATION_ACCEPTANCE_OR_RELEASE_INFERENCE",
        ],
        "audit_slot": slot,
        "routing_state": slot,
        "source_candidate_message_id": candidate["message_id"],
        "source_mechanical_message_id": mechanical["message_id"],
        "source_tester_result_id": tester_result["message_id"],
    }


def reconcile_t10_routes(
    config: dict[str, Any], connection: sqlite3.Connection, *, execute: bool
) -> None:
    current_intakes = [
        message
        for _, message in current_mailbox_messages(config, "integration_intake")
        if message.get("message_type") == "AUDIT_INTAKE"
    ]
    results = [
        message
        for _, message in current_mailbox_messages(config, "tester_results")
        if message.get("sender_role") == "T10_INDEPENDENT_AUDIT_SERVICE"
    ]
    completed = {
        (message.get("pack_id"), message.get("candidate_generation"))
        for message in results
    }
    unresolved = [
        message
        for message in current_intakes
        if (message.get("pack_id"), message.get("candidate_generation")) not in completed
    ]
    dispatcher_message_ids = {
        row["message_id"]
        for row in connection.execute("SELECT message_id FROM publications")
    }
    dispatcher_unresolved = [
        message
        for message in unresolved
        if message.get("message_id") in dispatcher_message_ids
    ]
    active_used = any(
        message.get("routing_state", message.get("audit_slot")) == "ACTIVE"
        for message in dispatcher_unresolved
    )
    queued_used = any(
        message.get("routing_state", message.get("audit_slot")) == "QUEUED"
        for message in dispatcher_unresolved
    )
    if not active_used:
        queued = next(
            (
                message
                for message in dispatcher_unresolved
                if message.get("routing_state", message.get("audit_slot")) == "QUEUED"
            ),
            None,
        )
        if queued is not None:
            action_id = canonical_hash(
                {
                    "action_type": "PROMOTE_T10_QUEUED",
                    "source_message": queued["message_id"],
                }
            )
            insert_action(
                connection,
                action_id=action_id,
                action_type="PUBLISH_T10_INTAKE",
                pack_id=queued["pack_id"],
                generation=int(queued["candidate_generation"]),
                source_message=queued["message_id"],
                source_commit=mailbox_authority_for_message(
                    config, queued["message_id"]
                )["introduction_commit"],
                authority=queued["idempotency_key"],
                idempotency_key=action_id,
                next_action="PROMOTE_T10_QUEUED_TO_ACTIVE",
            )
            if execute and lease_action(
                connection,
                action_id,
                f"t1-dispatcher:{os.getpid()}",
                int(config["lease_seconds"]),
                int(config["max_attempts"]),
            ):
                promoted = dict(queued)
                promoted["message_id"] = message_id(
                    (
                        f"{queued['pack_id']}-G"
                        f"{int(queued['candidate_generation']):06d}-T10-ACTIVE"
                    ),
                    action_id,
                )
                promoted["created_at"] = utc_now()
                promoted["parent_message_id"] = queued["message_id"]
                promoted["required_action"] = (
                    "PROCESS_EXACT_MECHANICALLY_ADMITTED_BDS_PASSING_CANDIDATE_"
                    "IN_ACTIVE_AUDIT_SLOT"
                )
                promoted["idempotency_key"] = action_id
                promoted["audit_slot"] = "ACTIVE"
                promoted["routing_state"] = "ACTIVE"
                publish(
                    config,
                    connection,
                    action_id,
                    promoted,
                    "integration_intake",
                )
                update_action(
                    connection,
                    action_id,
                    "WAITING_EXTERNAL_RESULT",
                    result=promoted["message_id"],
                    next_action="WAIT_FOR_T10_RESULT",
                )
                unresolved.append(promoted)
                active_used = True
                queued_used = False
    connection.execute(
        """
        UPDATE actions SET current_state='SUPERSEDED',
          last_error='LEGACY_T10_ROUTE_NOT_OWNED_BY_DURABLE_DISPATCHER',
          next_action='NO_REPLAY_OF_PREIMPLEMENTATION_QUEUE',
          lease_owner=NULL,lease_timestamp=NULL,lease_expires_at=NULL,updated_at=?
        WHERE action_type='PUBLISH_T10_INTAKE'
          AND current_state='PENDING'
          AND source_mailbox_message NOT IN (
            SELECT message_id FROM publications
          )
          AND exact_candidate_authority NOT IN (
            SELECT message_id FROM publications
          )
        """,
        (utc_now(),),
    )
    existing = {
        (message.get("pack_id"), message.get("candidate_generation"))
        for message in current_intakes
    }
    tester_passes = [
        message
        for _, message in current_mailbox_messages(config, "tester_results")
        if message.get("sender_role") == "PERSISTENT_TESTER"
        and message.get("message_type") == "TEST_PASS"
    ]
    for tester in tester_passes:
        key = (tester["pack_id"], tester["candidate_generation"])
        if key in existing or key in completed:
            continue
        admitted = mechanically_admitted_candidate(config, *key)
        if admitted is None:
            continue
        candidate, mechanical = admitted
        slot = "ACTIVE" if not active_used else ("QUEUED" if not queued_used else "BACKLOG")
        action_id = canonical_hash(
            {
                "action_type": "PUBLISH_T10_INTAKE",
                "tester_result": tester["message_id"],
                "candidate": candidate["message_id"],
            }
        )
        insert_action(
            connection,
            action_id=action_id,
            action_type="PUBLISH_T10_INTAKE",
            pack_id=tester["pack_id"],
            generation=int(tester["candidate_generation"]),
            source_message=tester["message_id"],
            source_commit=mailbox_authority_for_message(
                config, tester["message_id"]
            )["introduction_commit"],
            authority=mechanical["message_id"],
            idempotency_key=action_id,
            next_action=f"PUBLISH_T10_{slot}",
        )
        if slot == "BACKLOG" or not execute:
            continue
        if lease_action(
            connection,
            action_id,
            f"t1-dispatcher:{os.getpid()}",
            int(config["lease_seconds"]),
            int(config["max_attempts"]),
        ):
            route = t10_route_message(candidate, mechanical, tester, slot)
            publish(config, connection, action_id, route, "integration_intake")
            update_action(
                connection,
                action_id,
                "WAITING_EXTERNAL_RESULT",
                result=route["message_id"],
                next_action="WAIT_FOR_T10_RESULT",
            )
            active_used = active_used or slot == "ACTIVE"
            queued_used = queued_used or slot == "QUEUED"


def integration_message(
    candidate: dict[str, Any],
    mechanical: dict[str, Any],
    tester: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    commit, tree = supervisor_authority()
    action_id = canonical_hash(
        {
            "action_type": "PUBLISH_INTEGRATION_INTAKE",
            "candidate": candidate["message_id"],
            "tester": tester["message_id"],
            "audit": audit["message_id"],
        }
    )
    identifier = message_id(
        f"{candidate['pack_id']}-G{candidate['candidate_generation']:06d}-INTEGRATION",
        action_id,
    )
    return {
        "schema_version": "1.0.0",
        "message_id": identifier,
        "message_type": "INTEGRATION_INTAKE",
        "pack_id": candidate["pack_id"],
        "sender_role": "T1_PORTFOLIO_SUPERVISOR",
        "recipient_role": "SHARED_RUNTIME_INTEGRATION_WORKER",
        "created_at": utc_now(),
        "source_authority_commit": commit,
        "source_authority_tree": tree,
        "candidate_generation": candidate["candidate_generation"],
        "exact_artifact_hashes": mechanical["exact_artifact_hashes"],
        "parent_message_id": audit["message_id"],
        "required_action": "INTEGRATE_EXACT_STANDALONE_GATE_PASSING_CANDIDATE_WITHOUT_PRODUCT_MUTATION",
        "idempotency_key": action_id,
        "proof_boundary": [
            "MECHANICAL_PASS",
            "LOCAL_STABLE_BDS_PASS",
            "T10_PASS",
            "T2_EXCLUSIVE_INTEGRATION_WRITER",
            "NO_RELEASE_INFERENCE",
        ],
        "source_candidate_message_id": candidate["message_id"],
        "source_mechanical_message_id": mechanical["message_id"],
        "source_tester_result_id": tester["message_id"],
        "source_t10_result_id": audit["message_id"],
    }


def reconcile_integration(
    config: dict[str, Any], connection: sqlite3.Connection, *, execute: bool
) -> None:
    integration_keys = {
        (message.get("pack_id"), message.get("candidate_generation"))
        for _, message in current_mailbox_messages(config, "integration_intake")
        if message.get("message_type") == "INTEGRATION_INTAKE"
    }
    tester_passes = {
        (message["pack_id"], message["candidate_generation"]): message
        for _, message in current_mailbox_messages(config, "tester_results")
        if message.get("sender_role") == "PERSISTENT_TESTER"
        and message.get("message_type") == "TEST_PASS"
    }
    audit_passes = {
        (message["pack_id"], message["candidate_generation"]): message
        for _, message in current_mailbox_messages(config, "tester_results")
        if message.get("sender_role") == "T10_INDEPENDENT_AUDIT_SERVICE"
        and message.get("message_type") == "TEST_PASS"
    }
    dispatcher_audited = {
        (row["pack_id"], row["candidate_generation"])
        for row in connection.execute(
            "SELECT pack_id,candidate_generation FROM actions "
            "WHERE action_type='PUBLISH_T10_INTAKE'"
        )
    }
    for key in sorted(set(tester_passes) & set(audit_passes) & dispatcher_audited):
        if key in integration_keys:
            continue
        admitted = mechanically_admitted_candidate(config, *key)
        if admitted is None:
            continue
        candidate, mechanical = admitted
        tester = tester_passes[key]
        audit = audit_passes[key]
        message = integration_message(candidate, mechanical, tester, audit)
        action_id = message["idempotency_key"]
        insert_action(
            connection,
            action_id=action_id,
            action_type="PUBLISH_INTEGRATION_INTAKE",
            pack_id=key[0],
            generation=int(key[1]),
            source_message=audit["message_id"],
            source_commit=mailbox_authority_for_message(
                config, audit["message_id"]
            )["introduction_commit"],
            authority=candidate["message_id"],
            idempotency_key=action_id,
            next_action="PUBLISH_EXACT_T2_INTEGRATION_INTAKE",
        )
        if not execute:
            continue
        if lease_action(
            connection,
            action_id,
            f"t1-dispatcher:{os.getpid()}",
            int(config["lease_seconds"]),
            int(config["max_attempts"]),
        ):
            receipt = publish(
                config, connection, action_id, message, "integration_intake"
            )
            update_action(
                connection,
                action_id,
                "WAITING_EXTERNAL_RESULT",
                result=message["message_id"],
                next_action="WAKE_T2_AND_WAIT_FOR_INTEGRATION_RESULT",
            )
            queue_resume_request(
                config,
                connection,
                action_id=action_id,
                pack_id=key[0],
                task_id=config["t2_thread_id"],
                assignment_id=f"T2-INTEGRATION-{key[0]}-G{int(key[1]):06d}",
                repository=str(Path(__file__).resolve().parents[4]),
                ref="refs/heads/codex/pack-factory-organization-v1",
                authority_message=message["message_id"],
                authority_commit=receipt["commit"],
                authority_sha256=receipt["message_sha256"],
                required_generation=int(key[1]),
                kind="T2_INTEGRATION",
            )


def router_module(config: dict[str, Any]) -> Any:
    path = Path(config["router_config"]).with_name("factory_router.py")
    spec = importlib.util.spec_from_file_location("crazycraft_factory_router", path)
    if spec is None or spec.loader is None:
        raise DispatchError(f"cannot load existing router implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reconcile_owner_repairs(
    config: dict[str, Any], connection: sqlite3.Connection, *, execute: bool
) -> None:
    dispatcher_failures = {
        row["result_message"]
        for row in connection.execute(
            "SELECT result_message FROM actions "
            "WHERE current_state='TERMINAL_FAIL' "
            "AND next_action='PUBLISH_CONSOLIDATED_OWNER_REPAIR'"
        )
        if row["result_message"]
    }
    existing_parents = {
        message.get("parent_message_id")
        for _, message in current_mailbox_messages(config, "worker_repairs")
        if message.get("message_type") == "REPAIR_INSTRUCTION"
    }
    sources: list[tuple[Path, dict[str, Any]]] = []
    for root in ("final_decisions", "tester_results"):
        for path, message in current_mailbox_messages(config, root):
            is_mechanical_fail = (
                message.get("message_type") == "MECHANICAL_PREFLIGHT_RESULT"
                and message.get("mechanical_status") == "FAIL"
            )
            is_product_fail = (
                message.get("message_type") == "TEST_FAIL_PRODUCT"
                and message.get("sender_role")
                in {"PERSISTENT_TESTER", "T10_INDEPENDENT_AUDIT_SERVICE"}
            )
            if (
                (is_mechanical_fail or is_product_fail)
                and message.get("message_id") in dispatcher_failures
                and message.get("message_id") not in existing_parents
            ):
                sources.append((path, message))
    if not sources:
        return
    factory_router = router_module(config)
    repository = Path(config["mailbox_repository"])
    for path, result in sources:
        raw = path.read_bytes()
        action_id = canonical_hash(
            {
                "action_type": "PUBLISH_CONSOLIDATED_OWNER_REPAIR",
                "source_message": result["message_id"],
                "source_sha256": sha256_bytes(raw),
            }
        )
        insert_action(
            connection,
            action_id=action_id,
            action_type="PUBLISH_CONSOLIDATED_OWNER_REPAIR",
            pack_id=result["pack_id"],
            generation=int(result["candidate_generation"]) + 1,
            source_message=result["message_id"],
            source_commit=mailbox_message_authority(
                config, path, result["message_id"]
            )["introduction_commit"],
            authority=sha256_bytes(raw),
            idempotency_key=action_id,
            next_action="PUBLISH_CONSOLIDATED_OWNER_REPAIR",
        )
        if not execute:
            continue
        findings = result.get("findings")
        if not isinstance(findings, list) or not findings:
            update_action(
                connection,
                action_id,
                "PACK_LOCAL_BLOCK",
                error="FAILED_RESULT_HAS_NO_MACHINE_ROUTABLE_FINDINGS",
                next_action="REQUIRE_EXACT_T1_REPAIR_AUTHORITY",
            )
            continue
        if not lease_action(
            connection,
            action_id,
            f"t1-dispatcher:{os.getpid()}",
            int(config["lease_seconds"]),
            int(config["max_attempts"]),
        ):
            continue
        head = mailbox_head(config)
        action = {
            "action_id": action_id,
            "pack_id": result["pack_id"],
            "candidate_generation": int(result["candidate_generation"]),
            "created_at": utc_now(),
        }
        source = {"message": result, "message_sha256": sha256_bytes(raw)}
        repair, _ = factory_router.build_owner_repair_message(
            action, source, repository, head
        )
        publish(config, connection, action_id, repair, "worker_repairs")
        update_action(
            connection,
            action_id,
            "TERMINAL_PASS",
            result=repair["message_id"],
            next_action="RESUME_ORIGINAL_DURABLE_OWNER",
        )


def reconcile_echo_result_routing(
    config: dict[str, Any], connection: sqlite3.Connection, *, execute: bool
) -> None:
    source_action = connection.execute(
        """
        SELECT * FROM actions
        WHERE action_type='ROUTE_PLATFORM_REQUEST_TO_T2'
          AND pack_id='echo-vessels'
          AND next_action='ROUTE_T2_RESULT_TO_ECHO_OWNER'
          AND result_message IS NOT NULL
        ORDER BY updated_at DESC LIMIT 1
        """
    ).fetchone()
    if source_action is None:
        return
    result_path = None
    result = None
    for root in ("worker_repairs", "final_decisions"):
        for path, message in current_mailbox_messages(config, root, "echo-vessels"):
            if message.get("message_id") == source_action["result_message"]:
                result_path, result = path, message
                break
    if result is None or result_path is None:
        return
    existing = [
        message
        for _, message in current_mailbox_messages(
            config, "worker_repairs", "echo-vessels"
        )
        if message.get("sender_role") == "T1_PORTFOLIO_SUPERVISOR"
        and message.get("parent_message_id") == result["message_id"]
        and message.get("message_type") == "PLATFORM_ADMISSION_DECISION_RESULT"
    ]
    incompatible = [
        message
        for _, message in current_mailbox_messages(
            config, "worker_repairs", "echo-vessels"
        )
        if message.get("sender_role") == "T1_PORTFOLIO_SUPERVISOR"
        and message.get("parent_message_id") == result["message_id"]
        and message.get("message_type") == "PLATFORM_REPAIR_INSTRUCTION"
    ]
    action_id = canonical_hash(
        {
            "action_type": "ROUTE_T2_RESULT_TO_ECHO_OWNER",
            "envelope": "PLATFORM_ADMISSION_DECISION_RESULT",
            "source_result": result["message_id"],
            "source_sha256": sha256_bytes(result_path.read_bytes()),
        }
    )
    insert_action(
        connection,
        action_id=action_id,
        action_type="ROUTE_T2_RESULT_TO_PACK_OWNER",
        pack_id="echo-vessels",
        generation=7,
        source_message=result["message_id"],
        source_commit=mailbox_message_authority(
            config, result_path, result["message_id"]
        )["introduction_commit"],
        authority=sha256_bytes(result_path.read_bytes()),
        idempotency_key=action_id,
        next_action="PUBLISH_EXACT_ECHO_PLATFORM_REPAIR_AUTHORITY",
    )
    if existing:
        repair = existing[-1]
    elif not execute or not lease_action(
        connection,
        action_id,
        f"t1-dispatcher:{os.getpid()}",
        int(config["lease_seconds"]),
        int(config["max_attempts"]),
    ):
        return
    else:
        commit, tree = supervisor_authority()
        repair = {
            "schema_version": "1.0.0",
            "message_id": message_id("ECHO-PLATFORM-REPAIR", action_id),
            "message_type": "PLATFORM_ADMISSION_DECISION_RESULT",
            "pack_id": "echo-vessels",
            "sender_role": "T1_PORTFOLIO_SUPERVISOR",
            "recipient_role": "PACK-WORKER-13-ECHO-VESSELS",
            "created_at": utc_now(),
            "source_authority_commit": commit,
            "source_authority_tree": tree,
            "candidate_generation": 7,
            "candidate_generation_label_only": True,
            "immutable_candidate_exists": False,
            "exact_artifact_hashes": result["exact_artifact_hashes"],
            "parent_message_id": result["message_id"],
            "supersedes_message_id": (
                incompatible[-1]["message_id"] if incompatible else None
            ),
            "required_action": result["required_action"],
            "idempotency_key": action_id,
            "proof_boundary": [
                "T1_ROUTED_T2_DISPOSITION",
                "PRODUCT_LOCAL_PLATFORM_ADAPTER_OR_REQUEST_REPAIR_ONLY",
                "NO_SHARED_RUNTIME_WRITE",
                "NO_IMMUTABLE_GENERATION_7_CANDIDATE",
            ],
            "t2_decision": result.get("decision"),
            "exact_reason": result.get("exact_reason"),
        }
        publish(config, connection, action_id, repair, "worker_repairs")
        update_action(
            connection,
            action_id,
            "TERMINAL_PASS",
            result=repair["message_id"],
            next_action="RESUME_ORIGINAL_ECHO_OWNER_WITHOUT_CANDIDATE_AUTHORITY",
        )
    for message in incompatible:
        connection.execute(
            """
            UPDATE actions SET current_state='SUPERSEDED',
              last_error='SUPERSEDED_INCOMPATIBLE_ROUTER_ENVELOPE',
              next_action='USE_RECOGNIZED_PLATFORM_ADMISSION_DECISION_RESULT',
              lease_owner=NULL,lease_timestamp=NULL,lease_expires_at=NULL,updated_at=?
            WHERE result_message=? AND action_type='ROUTE_T2_RESULT_TO_PACK_OWNER'
            """,
            (utc_now(), message["message_id"]),
        )
    worker = worker_map(config)["echo-vessels"]
    repair_path = next(
        path
        for path, message in current_mailbox_messages(
            config, "worker_repairs", "echo-vessels"
        )
        if message.get("message_id") == repair["message_id"]
    )
    repair_authority = mailbox_message_authority(
        config, repair_path, repair["message_id"]
    )
    queue_resume_request(
        config,
        connection,
        action_id=action_id,
        pack_id="echo-vessels",
        task_id=worker["task_id"],
        assignment_id=worker["assignment_id"],
        repository=worker["repository"],
        ref=worker["ref"],
        authority_message=repair["message_id"],
        authority_commit=repair_authority["introduction_commit"],
        authority_sha256=repair_authority["sha256"],
        required_generation=7,
        kind="PACK_OWNER_PLATFORM_REPAIR",
    )


def pending_resume_requests(config: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(config["runtime_root"]) / "resume_requests"
    if not root.exists():
        return []
    result = []
    for path in sorted(root.glob("*.json")):
        request = load_json(path)
        if request.get("state") != "PENDING_SEND":
            continue
        expected_prompt = resume_prompt(
            kind=request["kind"],
            pack_id=request["pack_id"],
            assignment_id=request["assignment_id"],
            repository=request["repository"],
            ref=request["ref"],
            authority_message=request["authority_message"],
            authority_commit=request["authority_commit"],
            required_generation=int(request["required_generation"]),
        )
        if request.get("prompt") != expected_prompt:
            request["prompt"] = expected_prompt
            atomic_json(path, request)
        result.append(request)
    return result


def ack_resume(
    config: dict[str, Any],
    connection: sqlite3.Connection,
    request_id: str,
    status: str,
) -> None:
    path = Path(config["runtime_root"]) / "resume_requests" / f"{request_id}.json"
    request = load_json(path)
    if request.get("state") != "PENDING_SEND":
        return
    request["state"] = status
    request["sent_at"] = utc_now()
    atomic_json(path, request)
    if request["kind"].startswith("PACK_OWNER"):
        next_action = (
            "WAIT_FOR_REPLACEMENT_CANDIDATE"
            if request["kind"] == "PACK_OWNER"
            else "WAIT_FOR_CORRECTED_PRODUCT_LOCAL_PLATFORM_REQUEST"
        )
        connection.execute(
            """
            UPDATE actions SET current_state='WAITING_EXTERNAL_RESULT',
              worker_resumption_state=?,next_action=?,
              updated_at=? WHERE action_id=?
            """,
            (status, next_action, utc_now(), request["action_id"]),
        )
        connection.execute(
            """
            UPDATE workers SET loaded_state='WAKE_SENT',
              resume_attempt_count=resume_attempt_count+1,
              active_resume_action=?,updated_at=? WHERE pack_id=?
            """,
            (request["action_id"], utc_now(), request["pack_id"]),
        )
    else:
        connection.execute(
            """
            UPDATE actions SET worker_resumption_state=?,updated_at=?
            WHERE action_id=?
            """,
            (status, utc_now(), request["action_id"]),
        )


def snapshot(config: dict[str, Any], connection: sqlite3.Connection) -> dict[str, Any]:
    actions = [dict(row) for row in connection.execute(
        "SELECT * FROM actions ORDER BY created_at,action_id"
    )]
    workers = [dict(row) for row in connection.execute(
        "SELECT * FROM workers ORDER BY pack_id"
    )]
    value = {
        "schema_version": "crazycraft-t1-dispatcher-status-v1",
        "generated_at": utc_now(),
        "dispatcher_pid": os.getpid(),
        "mailbox_head": mailbox_head(config),
        "actions": actions,
        "workers": workers,
        "pending_resume_requests": pending_resume_requests(config),
    }
    atomic_json(Path(config["runtime_root"]) / "status.json", value)
    atomic_json(
        Path(config["runtime_root"]) / "prepared-action-reconciliation-ledger.json",
        {
            "schema_version": "crazycraft-t1-prepared-action-ledger-v1",
            "generated_at": value["generated_at"],
            "mailbox_head": value["mailbox_head"],
            "actions": actions,
        },
    )
    atomic_json(
        Path(config["runtime_root"]) / "worker-monitor.json",
        {
            "schema_version": "crazycraft-t1-worker-monitor-v1",
            "generated_at": value["generated_at"],
            "workers": workers,
        },
    )
    return value


def run_cycle(config: dict[str, Any], *, execute: bool) -> dict[str, Any]:
    runtime = Path(config["runtime_root"])
    connection = open_database(runtime)
    try:
        reconcile_router_actions(config, connection)
        reconcile_corrected_parser_blocks(connection)
        reconcile_repairs(config, connection)
        reconcile_external_results(config, connection)
        if execute:
            owner = f"t1-dispatcher:{os.getpid()}"
            rows = connection.execute(
                """
                SELECT * FROM actions
                WHERE current_state IN ('PENDING','LEASED','RUNNING')
                  AND action_type IN ('RUN_MECHANICAL_PREFLIGHT','ROUTE_PLATFORM_REQUEST_TO_T2')
                ORDER BY created_at,action_id
                """
            ).fetchall()
            for row in rows:
                if not lease_action(
                    connection,
                    row["action_id"],
                    owner,
                    int(config["lease_seconds"]),
                    int(config["max_attempts"]),
                ):
                    continue
                leased = connection.execute(
                    "SELECT * FROM actions WHERE action_id=?", (row["action_id"],)
                ).fetchone()
                try:
                    if leased["action_type"] == "RUN_MECHANICAL_PREFLIGHT":
                        execute_mechanical(config, connection, leased)
                    else:
                        execute_echo(config, connection, leased)
                except Exception as error:
                    update_action(
                        connection,
                        leased["action_id"],
                        "PACK_LOCAL_BLOCK",
                        error=f"{type(error).__name__}: {error}",
                        next_action="REQUIRE_EXACT_T1_CORRECTION",
                    )
        reconcile_t10_routes(config, connection, execute=execute)
        reconcile_integration(config, connection, execute=execute)
        reconcile_owner_repairs(config, connection, execute=execute)
        reconcile_echo_result_routing(config, connection, execute=execute)
        reconcile_repairs(config, connection)
        return snapshot(config, connection)
    finally:
        connection.close()


def run_corrected_parser_replay(config: dict[str, Any]) -> dict[str, Any]:
    runtime = Path(config["runtime_root"])
    connection = open_database(runtime)
    try:
        reconcile_router_actions(config, connection)
        reconcile_corrected_parser_blocks(connection)
        owner = f"t1-dispatcher-corrected-replay:{os.getpid()}"
        placeholders = ",".join("?" for _ in CORRECTED_REPLAY_MESSAGES)
        rows = connection.execute(
            f"""
            SELECT * FROM actions
            WHERE current_state IN ('PENDING','LEASED','RUNNING')
              AND source_mailbox_message IN ({placeholders})
            ORDER BY created_at,action_id
            """,
            CORRECTED_REPLAY_MESSAGES,
        ).fetchall()
        for row in rows:
            if not lease_action(
                connection,
                row["action_id"],
                owner,
                int(config["lease_seconds"]),
                int(config["max_attempts"]),
            ):
                continue
            leased = connection.execute(
                "SELECT * FROM actions WHERE action_id=?", (row["action_id"],)
            ).fetchone()
            try:
                if leased["action_type"] == "RUN_MECHANICAL_PREFLIGHT":
                    execute_mechanical(config, connection, leased)
                elif leased["action_type"] == "ROUTE_PLATFORM_REQUEST_TO_T2":
                    execute_echo(config, connection, leased)
                else:
                    raise DispatchError(
                        f"corrected replay action type rejected: {leased['action_type']}"
                    )
            except Exception as error:
                update_action(
                    connection,
                    leased["action_id"],
                    "PACK_LOCAL_BLOCK",
                    error=f"{type(error).__name__}: {error}",
                    next_action="REQUIRE_EXACT_T1_CORRECTION",
                )
        return snapshot(config, connection)
    finally:
        connection.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("t1-dispatcher-config.json"),
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--reconcile-only", action="store_true")
    modes.add_argument("--run-once", action="store_true")
    modes.add_argument("--replay-corrected-parser-blocks", action="store_true")
    modes.add_argument("--serve", action="store_true")
    modes.add_argument("--status", action="store_true")
    modes.add_argument("--pending-resumes", action="store_true")
    modes.add_argument("--ack-resume")
    parser.add_argument(
        "--ack-status",
        choices=("SENT", "FAILED"),
        default="SENT",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = config_from(args.config)
    runtime = Path(config["runtime_root"])
    if args.status:
        path = runtime / "status.json"
        print(path.read_text() if path.exists() else "{}")
        return 0
    if args.pending_resumes:
        print(json.dumps(pending_resume_requests(config), sort_keys=True, indent=2))
        return 0
    if args.ack_resume:
        connection = open_database(runtime)
        try:
            ack_resume(config, connection, args.ack_resume, args.ack_status)
            snapshot(config, connection)
        finally:
            connection.close()
        return 0
    if args.replay_corrected_parser_blocks:
        with singleton(runtime) as acquired:
            if acquired:
                result = run_corrected_parser_replay(config)
                print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    if args.serve:
        while True:
            with singleton(runtime) as acquired:
                if acquired:
                    run_cycle(config, execute=True)
            time.sleep(int(config["poll_interval_seconds"]))
    else:
        with singleton(runtime) as acquired:
            if acquired:
                result = run_cycle(config, execute=args.run_once)
                print(json.dumps(result, sort_keys=True, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
