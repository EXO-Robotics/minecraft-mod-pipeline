#!/usr/bin/env python3
"""Bounded, routing-only consumer for the Crazy Craft factory mailbox.

This process never starts product workers, edits candidates, or invents semantic
messages.  It validates append-only mailbox history, maintains an ignored
operational projection, and exposes the existing canonical mailbox publisher to
an explicitly prepared semantic action.
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MESSAGE_ID = re.compile(r"^[A-Z0-9][A-Z0-9._-]{7,127}$")
UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
REQUIRED_RUNTIME_FIELDS = {
    "last_polled_mailbox_commit",
    "last_consumed_mailbox_commit",
    "unseen_message_count",
    "active_preflight",
    "tester_active",
    "tester_queued",
    "t10_active",
    "t10_queued",
    "audit_backlog",
    "repair_messages_pending",
    "integration_intake_pending",
    "last_successful_cycle_at",
    "current_cycle_started_at",
}
COMPATIBILITY_DISPOSITIONS = {
    "HISTORICAL_SUPERSEDED",
    "HISTORICAL_AUTHORITATIVE_REJECTION",
    "PACK_LOCAL_QUARANTINE_SUPERSESSION_REQUIRED",
}
MESSAGE_ROOTS = {
    "candidate_submissions",
    "tester_intake",
    "tester_results",
    "worker_repairs",
    "integration_intake",
    "final_decisions",
}
CANDIDATE_SIDECAR_HASH_FIELDS = {
    "RESTRICTED_GIT_OBJECTS_SCAN": "final_metadata_restricted_git_object_scan_sha256",
    "RESTRICTED_IDENTIFIERS_SCAN": "final_product_restricted_identifier_scan_sha256",
}
TEST_RESULT_TYPES = {
    "TEST_PASS",
    "TEST_FAIL_PRODUCT",
    "TEST_FAIL_INFRASTRUCTURE",
    "TEST_BLOCKED_CLIENT",
    "TEST_BLOCKED_PHYSICAL",
    "AUDIT_RESULT",
}
REPAIR_STATES = {
    "RESULT_AWAITING_ROUTING",
    "REPAIR_INSTRUCTION_PUBLISHED",
    "OWNER_REPLACEMENT_PENDING",
    "SUPERSEDED_BY_REPLACEMENT",
}
EXECUTABLE_ACTION_TYPES = {
    "RUN_MECHANICAL_PREFLIGHT",
    "PROMOTE_T10_QUEUED",
    "PUBLISH_CONSOLIDATED_OWNER_REPAIR",
    "ROUTE_MECHANICALLY_ADMITTED_CANDIDATE_TO_TESTER",
    "MOVE_FIRST_AUDIT_BACKLOG_ITEM_TO_QUEUED",
}


class RouterError(RuntimeError):
    pass


def utc_now() -> str:
    return time.strftime(UTC_FORMAT, time.gmtime())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RouterError(f"expected JSON object: {path}")
    return value


def run_git(repository: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["/usr/bin/git", "-C", str(repository), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        raise RouterError(
            f"git failed ({result.returncode}): {' '.join(args)}: "
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def git_object_exists(repository: Path, object_id: str) -> bool:
    result = subprocess.run(
        ["/usr/bin/git", "-C", str(repository), "cat-file", "-e", object_id],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def is_ancestor(repository: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        [
            "/usr/bin/git",
            "-C",
            str(repository),
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def config_from(path: Path) -> dict[str, Any]:
    config = load_json(path.resolve())
    required = {
        "schema_version",
        "mailbox_repository",
        "mailbox_ref",
        "initial_consumed_mailbox_commit",
        "runtime_root",
        "publisher",
        "local_tester_state",
        "poll_interval_seconds",
        "max_tester_active",
        "max_t10_active",
        "max_t10_queued",
        "allowed_tester_sender_roles",
        "allowed_t10_sender_roles",
        "initial_t10_projection",
        "allowed_message_roots",
        "compatibility_ledger",
        "compatibility_ledger_expected_entries",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise RouterError(f"config missing fields: {missing}")
    if config["schema_version"] != "crazycraft-factory-router-v1":
        raise RouterError("unsupported config schema")
    if config["poll_interval_seconds"] != 120:
        raise RouterError("router interval must be exactly 120 seconds")
    if not config["allowed_tester_sender_roles"]:
        raise RouterError("tester sender allowlist must not be empty")
    if not config["allowed_t10_sender_roles"]:
        raise RouterError("T10 sender allowlist must not be empty")
    roots = set(config["allowed_message_roots"])
    if roots != MESSAGE_ROOTS:
        raise RouterError("message-root allowlist mismatch")
    for key in (
        "mailbox_repository",
        "runtime_root",
        "publisher",
        "local_tester_state",
        "compatibility_ledger",
    ):
        config[key] = str(Path(config[key]).resolve())
    return config


def initial_state(config: dict[str, Any]) -> dict[str, Any]:
    projection = config["initial_t10_projection"]
    state = {
        "schema_version": "crazycraft-factory-router-runtime-v1",
        "record_type": "ignored_runtime_state",
        "last_polled_mailbox_commit": config["initial_consumed_mailbox_commit"],
        "last_consumed_mailbox_commit": config[
            "initial_consumed_mailbox_commit"
        ],
        "unseen_message_count": 0,
        "active_preflight": [],
        "tester_active": [],
        "tester_queued": [],
        "t10_active": projection.get("active"),
        "t10_queued": projection.get("queued"),
        "audit_backlog": list(projection.get("audit_backlog", [])),
        "repair_messages_pending": [],
        "repair_state_history": [],
        "integration_intake_pending": [],
        "pending_semantic_actions": [],
        "last_successful_cycle_at": None,
        "current_cycle_started_at": None,
        "consumed_messages": {},
        "candidate_identities": {},
        "idempotency_keys": {},
        "tester_results": {},
        "audit_results": {},
        "duplicate_observations": [],
        "protocol_defects": [],
        "compatibility_events": [],
        "blocked_packs": {},
        "quarantined_messages": [],
        "executed_semantic_actions": {},
        "consumption_definition": (
            "A mailbox message is consumed only after validation and conversion "
            "into a durable runtime result or pending semantic action. Consumption "
            "does not mean the semantic action was published or completed."
        ),
    }
    validate_runtime_state(state)
    return state


def upgrade_runtime_state(state: dict[str, Any]) -> dict[str, Any]:
    """Add derived fields without changing or upgrading mailbox authority."""
    state.setdefault("repair_state_history", [])
    state.setdefault("executed_semantic_actions", {})
    state.setdefault("compatibility_events", [])
    state.setdefault("blocked_packs", {})
    state.setdefault("quarantined_messages", [])
    for item in state.get("repair_messages_pending", []):
        if "repair_state" in item:
            continue
        item["repair_state"] = (
            "OWNER_REPLACEMENT_PENDING"
            if item.get("message_type") == "REPAIR_INSTRUCTION"
            else "RESULT_AWAITING_ROUTING"
        )
    return state


def validate_runtime_state(state: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_RUNTIME_FIELDS - state.keys())
    if missing:
        raise RouterError(f"runtime state missing fields: {missing}")
    for field in (
        "last_polled_mailbox_commit",
        "last_consumed_mailbox_commit",
    ):
        if not HEX40.fullmatch(str(state[field])):
            raise RouterError(f"invalid runtime commit field: {field}")
    if not isinstance(state["unseen_message_count"], int):
        raise RouterError("unseen_message_count must be integer")
    for field in (
        "active_preflight",
        "tester_active",
        "tester_queued",
        "audit_backlog",
        "repair_messages_pending",
        "integration_intake_pending",
        "pending_semantic_actions",
        "repair_state_history",
    ):
        if not isinstance(state[field], list):
            raise RouterError(f"{field} must be a list")
    for item in state["repair_messages_pending"]:
        repair_state = item.get("repair_state")
        if repair_state not in {
            "RESULT_AWAITING_ROUTING",
            "OWNER_REPLACEMENT_PENDING",
        }:
            raise RouterError(f"invalid pending repair state: {repair_state}")
    if not isinstance(state["compatibility_events"], list):
        raise RouterError("compatibility_events must be a list")
    if not isinstance(state["blocked_packs"], dict):
        raise RouterError("blocked_packs must be an object")
    if not isinstance(state["quarantined_messages"], list):
        raise RouterError("quarantined_messages must be a list")


def compatibility_key(commit: str, path: str, raw_sha256: str) -> str:
    return f"{commit}:{path}:{raw_sha256}"


def load_compatibility_ledger(
    path: Path, repository: Path, expected_entries: int
) -> dict[str, dict[str, Any]]:
    ledger = load_json(path)
    if ledger.get("schema_version") != "crazycraft-router-compatibility-v1":
        raise RouterError("unsupported compatibility ledger schema")
    entries = ledger.get("entries")
    if (
        not isinstance(expected_entries, int)
        or expected_entries < 0
        or not isinstance(entries, list)
        or len(entries) != expected_entries
    ):
        raise RouterError(
            f"compatibility ledger must contain exactly {expected_entries} entries"
        )
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise RouterError("compatibility ledger entry must be an object")
        required = {
            "entry_key",
            "message_id",
            "mailbox_commit",
            "message_path",
            "raw_message_sha256",
            "historical_role",
            "current_disposition",
            "pack_affected",
            "cursor_advancement_permitted",
            "superseding_authority",
            "replay_behavior",
            "exact_exemption_reason",
        }
        missing = sorted(required - entry.keys())
        if missing:
            raise RouterError(f"compatibility entry missing fields: {missing}")
        commit = str(entry["mailbox_commit"])
        relative_path = str(entry["message_path"])
        raw_sha256 = str(entry["raw_message_sha256"])
        if not HEX40.fullmatch(commit) or not HEX64.fullmatch(raw_sha256):
            raise RouterError("compatibility entry object identity is malformed")
        expected_key = compatibility_key(commit, relative_path, raw_sha256)
        if entry["entry_key"] != expected_key or expected_key in indexed:
            raise RouterError("compatibility ledger key mismatch or duplicate")
        if entry["current_disposition"] not in COMPATIBILITY_DISPOSITIONS:
            raise RouterError("compatibility disposition is not allowlisted")
        if entry["cursor_advancement_permitted"] is not True:
            raise RouterError("compatibility entry must explicitly permit advancement")
        raw = subprocess.run(
            [
                "/usr/bin/git",
                "-C",
                str(repository),
                "show",
                f"{commit}:{relative_path}",
            ],
            capture_output=True,
            check=False,
        )
        if raw.returncode:
            raise RouterError("compatibility ledger object is absent")
        if hashlib.sha256(raw.stdout).hexdigest() != raw_sha256:
            raise RouterError("compatibility ledger raw object hash mismatch")
        indexed[expected_key] = entry
    return indexed


def message_identity(message: dict[str, Any]) -> str:
    material = {
        "pack_id": message["pack_id"],
        "candidate_generation": message["candidate_generation"],
        "source_authority_commit": message["source_authority_commit"],
        "source_authority_tree": message["source_authority_tree"],
        "exact_artifact_hashes": message["exact_artifact_hashes"],
    }
    return canonical_hash(material)


def validate_message(
    raw: bytes, relative_path: str, mailbox_commit: str
) -> dict[str, Any]:
    try:
        message = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RouterError(f"invalid mailbox JSON {relative_path}: {error}") from error
    if not isinstance(message, dict):
        raise RouterError(f"message must be an object: {relative_path}")
    required = {
        "schema_version",
        "message_id",
        "message_type",
        "pack_id",
        "sender_role",
        "recipient_role",
        "created_at",
        "source_authority_commit",
        "source_authority_tree",
        "candidate_generation",
        "exact_artifact_hashes",
        "parent_message_id",
        "required_action",
        "idempotency_key",
        "proof_boundary",
    }
    missing = sorted(required - message.keys())
    if missing:
        raise RouterError(f"message missing fields {missing}: {relative_path}")
    path = PurePosixPath(relative_path)
    if (
        path.is_absolute()
        or len(path.parts) != 3
        or path.parts[0] not in MESSAGE_ROOTS
        or path.suffix != ".json"
        or any(part in {"", ".", ".."} or part.startswith(".") for part in path.parts)
    ):
        raise RouterError(f"message path rejected: {relative_path}")
    if path.parts[1] != message["pack_id"]:
        raise RouterError(f"message pack/path mismatch: {relative_path}")
    if path.stem != message["message_id"]:
        raise RouterError(f"message ID/path mismatch: {relative_path}")
    if not MESSAGE_ID.fullmatch(str(message["message_id"])):
        raise RouterError(f"invalid message ID: {relative_path}")
    if not HEX40.fullmatch(str(message["source_authority_commit"])):
        raise RouterError(f"invalid source commit: {relative_path}")
    if not HEX40.fullmatch(str(message["source_authority_tree"])):
        raise RouterError(f"invalid source tree: {relative_path}")
    if not HEX64.fullmatch(str(message["idempotency_key"])):
        raise RouterError(f"invalid idempotency key: {relative_path}")
    if (
        not isinstance(message["candidate_generation"], int)
        or message["candidate_generation"] < 0
    ):
        raise RouterError(f"invalid candidate generation: {relative_path}")
    if not isinstance(message["proof_boundary"], list):
        raise RouterError(f"invalid proof boundary: {relative_path}")
    if not isinstance(message["exact_artifact_hashes"], (dict, list)):
        raise RouterError(f"invalid artifact hashes: {relative_path}")
    return {
        "message": message,
        "record_kind": "VALID",
        "mailbox_commit": mailbox_commit,
        "mailbox_path": relative_path,
        "message_sha256": hashlib.sha256(raw).hexdigest(),
        "candidate_identity": message_identity(message),
    }


def compatibility_record(
    raw: bytes,
    relative_path: str,
    mailbox_commit: str,
    entry: dict[str, Any],
) -> dict[str, Any]:
    try:
        message = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RouterError("compatibility ledger cannot admit corrupt JSON") from error
    if not isinstance(message, dict):
        raise RouterError("compatibility ledger cannot admit a non-object message")
    if (
        message.get("message_id") != entry["message_id"]
        or message.get("pack_id") != entry["pack_affected"]
    ):
        raise RouterError("compatibility message identity does not match ledger")
    raw_sha256 = hashlib.sha256(raw).hexdigest()
    return {
        "message": message,
        "record_kind": "COMPATIBILITY",
        "compatibility_entry": entry,
        "mailbox_commit": mailbox_commit,
        "mailbox_path": relative_path,
        "message_sha256": raw_sha256,
        "candidate_identity": canonical_hash(
            {
                "compatibility_entry": entry["entry_key"],
                "message_id": message["message_id"],
                "pack_id": message["pack_id"],
            }
        ),
    }


def pack_local_invalid_record(
    raw: bytes,
    relative_path: str,
    mailbox_commit: str,
    validation_error: RouterError,
) -> dict[str, Any] | None:
    """Recognize a narrow, attributable schema defect without weakening authority.

    Only a structurally identified message whose sole known defect is a missing
    or null exact_artifact_hashes field may be quarantined pack-locally. Unknown
    invalid forms, corrupt JSON, path ambiguity, and authority-identity defects
    remain global failures.
    """
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        return None
    path = PurePosixPath(relative_path)
    if (
        not isinstance(message, dict)
        or path.is_absolute()
        or len(path.parts) != 3
        or path.parts[0] not in MESSAGE_ROOTS
        or path.suffix != ".json"
        or any(part in {"", ".", ".."} or part.startswith(".") for part in path.parts)
        or path.parts[1] != message.get("pack_id")
        or path.stem != message.get("message_id")
        or not MESSAGE_ID.fullmatch(str(message.get("message_id", "")))
        or not HEX40.fullmatch(str(message.get("source_authority_commit", "")))
        or not HEX40.fullmatch(str(message.get("source_authority_tree", "")))
        or not HEX64.fullmatch(str(message.get("idempotency_key", "")))
        or not isinstance(message.get("candidate_generation"), int)
        or message["candidate_generation"] < 0
        or not isinstance(message.get("proof_boundary"), list)
    ):
        return None
    error_text = str(validation_error)
    exact_hashes_missing = "exact_artifact_hashes" not in message
    exact_hashes_null = message.get("exact_artifact_hashes") is None
    if not (
        (
            exact_hashes_missing
            and "message missing fields ['exact_artifact_hashes']" in error_text
        )
        or (
            exact_hashes_null
            and "invalid artifact hashes" in error_text
        )
    ):
        return None
    raw_sha256 = hashlib.sha256(raw).hexdigest()
    return {
        "message": message,
        "record_kind": "PACK_LOCAL_QUARANTINE",
        "validation_error": error_text,
        "mailbox_commit": mailbox_commit,
        "mailbox_path": relative_path,
        "message_sha256": raw_sha256,
        "candidate_identity": canonical_hash(
            {
                "pack_local_invalid": raw_sha256,
                "message_id": message["message_id"],
                "pack_id": message["pack_id"],
            }
        ),
    }


def changed_paths(repository: Path, commit: str) -> list[tuple[str, str]]:
    parents = run_git(repository, "rev-list", "--parents", "-n", "1", commit).split()
    if len(parents) != 2:
        raise RouterError(f"mailbox commit is not single-parent: {commit}")
    output = run_git(
        repository, "diff-tree", "--no-commit-id", "--name-status", "-r", parents[1], commit
    )
    records: list[tuple[str, str]] = []
    for line in output.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            raise RouterError(f"unsupported mailbox diff record: {line}")
        records.append((parts[0], parts[1]))
    return records


def is_bound_candidate_sidecar(
    repository: Path,
    commit: str,
    relative_path: str,
    raw: bytes,
    added_paths: set[str],
) -> bool:
    """Accept only exact, same-commit scan artifacts bound by a candidate message."""
    path = PurePosixPath(relative_path)
    match = re.fullmatch(
        r"(?P<message_id>[A-Z0-9][A-Z0-9._-]{7,127})\."
        r"(?P<role>RESTRICTED_GIT_OBJECTS_SCAN|RESTRICTED_IDENTIFIERS_SCAN)\.json",
        path.name,
    )
    if match is None:
        return False
    message_path = path.with_name(f"{match.group('message_id')}.json").as_posix()
    if message_path not in added_paths:
        raise RouterError(
            f"candidate sidecar lacks same-commit message binding: {commit}:{relative_path}"
        )
    message_raw = subprocess.run(
        ["/usr/bin/git", "-C", str(repository), "show", f"{commit}:{message_path}"],
        capture_output=True,
        check=False,
    )
    if message_raw.returncode:
        raise RouterError(
            f"cannot read candidate sidecar message binding: {commit}:{message_path}"
        )
    try:
        message = json.loads(message_raw.stdout)
    except json.JSONDecodeError as error:
        raise RouterError(
            f"candidate sidecar message binding is invalid JSON: {commit}:{message_path}"
        ) from error
    hash_field = CANDIDATE_SIDECAR_HASH_FIELDS[match.group("role")]
    artifact_hashes = message.get("exact_artifact_hashes")
    expected_hash = artifact_hashes.get(hash_field) if isinstance(artifact_hashes, dict) else None
    observed_hash = hashlib.sha256(raw).hexdigest()
    if (
        not isinstance(message, dict)
        or message.get("message_type") != "CANDIDATE_SUBMISSION"
        or message.get("message_id") != match.group("message_id")
        or len(path.parts) != 3
        or path.parts[1] != message.get("pack_id")
        or not HEX64.fullmatch(str(expected_hash or ""))
        or expected_hash != observed_hash
    ):
        raise RouterError(
            f"candidate sidecar authority binding failed: {commit}:{relative_path}"
        )
    return True


def discover_messages(
    repository: Path,
    cursor: str,
    head: str,
    compatibility_entries: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if not git_object_exists(repository, cursor):
        raise RouterError(f"mailbox cursor does not exist: {cursor}")
    if not is_ancestor(repository, cursor, head):
        raise RouterError("mailbox cursor is not an ancestor of authority HEAD")
    commits = run_git(repository, "rev-list", "--reverse", f"{cursor}..{head}")
    discovered: list[dict[str, Any]] = []
    for commit in commits.splitlines():
        commit_paths = changed_paths(repository, commit)
        added_paths = {path for status, path in commit_paths if status == "A"}
        for status, path in commit_paths:
            root = PurePosixPath(path).parts[0] if PurePosixPath(path).parts else ""
            if root not in MESSAGE_ROOTS:
                continue
            if status != "A":
                raise RouterError(
                    f"mailbox history is not append-only: {commit} {status} {path}"
                )
            raw = subprocess.run(
                ["/usr/bin/git", "-C", str(repository), "show", f"{commit}:{path}"],
                capture_output=True,
                check=False,
            )
            if raw.returncode:
                raise RouterError(f"cannot read mailbox message: {commit}:{path}")
            if is_bound_candidate_sidecar(
                repository, commit, path, raw.stdout, added_paths
            ):
                continue
            raw_sha256 = hashlib.sha256(raw.stdout).hexdigest()
            entry = (compatibility_entries or {}).get(
                compatibility_key(commit, path, raw_sha256)
            )
            if entry:
                discovered.append(
                    compatibility_record(raw.stdout, path, commit, entry)
                )
                continue
            try:
                discovered.append(validate_message(raw.stdout, path, commit))
            except RouterError as error:
                quarantined = pack_local_invalid_record(
                    raw.stdout, path, commit, error
                )
                if quarantined is None:
                    raise
                discovered.append(quarantined)
    return discovered


def mailbox_root_commit(repository: Path, head: str) -> str:
    roots = run_git(repository, "rev-list", "--max-parents=0", head).splitlines()
    if len(roots) != 1 or not HEX40.fullmatch(roots[0]):
        raise RouterError("mailbox history does not have exactly one root")
    return roots[0]


def replay_state(
    config: dict[str, Any],
    *,
    head: str,
    recovery_anchor: str,
    cursor: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reconstruct state from immutable mailbox authority without publishing.

    Current-cursor mode first reconstructs the cursor baseline from authority
    rather than trusting ignored runtime state, then consumes cursor..HEAD.
    Full-history mode consumes root..HEAD in one pass.  Both therefore validate
    the same complete authority while exercising different restart boundaries.
    """
    repository = Path(config["mailbox_repository"])
    if not is_ancestor(repository, recovery_anchor, head):
        raise RouterError("recovery anchor is not an ancestor of replay HEAD")
    if cursor is not None and not is_ancestor(repository, recovery_anchor, cursor):
        raise RouterError("replay cursor precedes recovery anchor")
    compatibility_entries = load_compatibility_ledger(
        Path(config["compatibility_ledger"]),
        repository,
        config["compatibility_ledger_expected_entries"],
    )
    replay_config = copy.deepcopy(config)
    replay_config["initial_t10_projection"] = {
        "active": None,
        "queued": None,
        "audit_backlog": [],
    }
    state = initial_state(replay_config)
    root = mailbox_root_commit(repository, head)
    ranges: list[tuple[str, str]]
    mode: str
    if cursor is None:
        mode = "FULL_HISTORY"
        ranges = [(root, head)]
    else:
        mode = "CURRENT_CURSOR"
        ranges = [(root, cursor), (cursor, head)]
    record_count = 0
    compatibility_count = 0
    quarantine_count = 0
    phase_counts: list[dict[str, Any]] = []
    for start, end in ranges:
        records = discover_messages(
            repository, start, end, compatibility_entries
        )
        for record in records:
            consume_record(state, record, replay_config)
        record_count += len(records)
        compatibility_count += sum(
            record.get("record_kind") == "COMPATIBILITY" for record in records
        )
        quarantine_count += sum(
            record.get("record_kind") == "PACK_LOCAL_QUARANTINE"
            for record in records
        )
        phase_counts.append(
            {
                "start_exclusive": start,
                "end_inclusive": end,
                "record_count": len(records),
            }
        )
    derive_deterministic_actions(state, repository, head)
    state["last_polled_mailbox_commit"] = head
    state["last_consumed_mailbox_commit"] = head
    state["unseen_message_count"] = 0
    projection = canonical_authority_projection(state)
    report = {
        "schema_version": "crazycraft-router-replay-v1",
        "mode": mode,
        "mailbox_repository": str(repository),
        "mailbox_ref": config["mailbox_ref"],
        "root_commit": root,
        "recovery_anchor": recovery_anchor,
        "cursor": cursor,
        "head": head,
        "phases": phase_counts,
        "record_count": record_count,
        "compatibility_entry_count": compatibility_count,
        "pack_local_quarantine_count": quarantine_count,
        "blocked_packs": sorted(state["blocked_packs"]),
        "projection_sha256": canonical_hash(projection),
        "projection": projection,
    }
    return state, report


def canonical_authority_projection(state: dict[str, Any]) -> dict[str, Any]:
    """Return the order-stable semantic projection used for replay comparison."""

    def normalized_items(
        items: list[dict[str, Any]], fields: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        output = [
            {field: item.get(field) for field in fields if field in item}
            for item in items
        ]
        return sorted(output, key=canonical_bytes)

    return {
        "active_preflight": normalized_items(
            state["active_preflight"],
            (
                "message_id",
                "pack_id",
                "candidate_generation",
                "candidate_identity",
                "message_sha256",
            ),
        ),
        "tester_active": normalized_items(
            state["tester_active"],
            ("message_id", "pack_id", "candidate_generation", "message_sha256"),
        ),
        "tester_queued": normalized_items(
            state["tester_queued"],
            ("message_id", "pack_id", "candidate_generation", "message_sha256"),
        ),
        "t10_active": state.get("t10_active"),
        "t10_queued": state.get("t10_queued"),
        "audit_backlog": normalized_items(
            state["audit_backlog"],
            ("source_message_id", "pack_id", "candidate_generation"),
        ),
        "repair_messages_pending": normalized_items(
            state["repair_messages_pending"],
            (
                "repair_message_id",
                "source_result_id",
                "pack_id",
                "failed_generation",
                "required_replacement_generation",
                "repair_state",
            ),
        ),
        "integration_intake_pending": normalized_items(
            state["integration_intake_pending"],
            ("message_id", "candidate_key", "pack_id", "candidate_generation"),
        ),
        "pending_semantic_actions": normalized_items(
            state["pending_semantic_actions"],
            (
                "action_type",
                "source_message_id",
                "pack_id",
                "candidate_generation",
                "candidate_identity",
                "state",
            ),
        ),
        "compatibility_events": normalized_items(
            state["compatibility_events"],
            (
                "entry_key",
                "message_id",
                "pack_id",
                "disposition",
                "message_sha256",
            ),
        ),
        "blocked_packs": {
            pack_id: {
                key: block.get(key)
                for key in ("message_id", "message_sha256", "reason")
            }
            for pack_id, block in sorted(state["blocked_packs"].items())
        },
        "tester_results": {
            key: value.get("message_id")
            for key, value in sorted(state["tester_results"].items())
        },
        "audit_results": {
            key: value.get("message_id")
            for key, value in sorted(state["audit_results"].items())
        },
    }


def candidate_key(message: dict[str, Any]) -> str:
    return f"{message['pack_id']}:{message['candidate_generation']}"


def append_unique(items: list[dict[str, Any]], value: dict[str, Any], key: str) -> None:
    if not any(item.get(key) == value.get(key) for item in items):
        items.append(value)


def record_repair_transition(
    state: dict[str, Any],
    *,
    pack_id: str,
    failed_generation: int,
    repair_state: str,
    source_result_id: str | None,
    repair_message_id: str | None = None,
    replacement_message_id: str | None = None,
) -> None:
    if repair_state not in REPAIR_STATES:
        raise RouterError(f"unsupported repair transition: {repair_state}")
    transition = {
        "transition_id": canonical_hash(
            {
                "pack_id": pack_id,
                "failed_generation": failed_generation,
                "repair_state": repair_state,
                "source_result_id": source_result_id,
                "repair_message_id": repair_message_id,
                "replacement_message_id": replacement_message_id,
            }
        ),
        "pack_id": pack_id,
        "failed_generation": failed_generation,
        "repair_state": repair_state,
        "source_result_id": source_result_id,
        "repair_message_id": repair_message_id,
        "replacement_message_id": replacement_message_id,
    }
    append_unique(state["repair_state_history"], transition, "transition_id")


def mark_result_awaiting_routing(
    state: dict[str, Any], result: dict[str, Any]
) -> None:
    pending = {
        **result,
        "failed_generation": result["candidate_generation"],
        "source_result_id": result["message_id"],
        "repair_state": "RESULT_AWAITING_ROUTING",
    }
    # One immutable result is one pending repair, even if it is observed again.
    append_unique(state["repair_messages_pending"], pending, "source_result_id")
    record_repair_transition(
        state,
        pack_id=result["pack_id"],
        failed_generation=result["candidate_generation"],
        repair_state="RESULT_AWAITING_ROUTING",
        source_result_id=result["message_id"],
    )


def mark_repair_instruction_published(
    state: dict[str, Any], message: dict[str, Any]
) -> None:
    parent_id = message.get("parent_message_id")
    failed_generation = message.get(
        "failed_candidate_generation", message["candidate_generation"]
    )
    source_result_id = parent_id
    matching = [
        item
        for item in state["repair_messages_pending"]
        if item.get("source_result_id") == parent_id
    ]
    if matching:
        failed_generation = matching[0].get(
            "failed_generation", matching[0]["candidate_generation"]
        )
        source_result_id = matching[0].get("source_result_id")
    state["repair_messages_pending"] = [
        item
        for item in state["repair_messages_pending"]
        if item.get("source_result_id") != parent_id
    ]
    record_repair_transition(
        state,
        pack_id=message["pack_id"],
        failed_generation=failed_generation,
        repair_state="REPAIR_INSTRUCTION_PUBLISHED",
        source_result_id=source_result_id,
        repair_message_id=message["message_id"],
    )
    replacement_generation = message.get(
        "required_replacement_generation",
        (
            message["candidate_generation"]
            if message["candidate_generation"] > failed_generation
            else failed_generation + 1
        ),
    )
    pending = {
        "message_id": message["message_id"],
        "pack_id": message["pack_id"],
        "candidate_generation": failed_generation,
        "failed_generation": failed_generation,
        "required_replacement_generation": replacement_generation,
        "source_result_id": source_result_id,
        "repair_message_id": message["message_id"],
        "repair_state": "OWNER_REPLACEMENT_PENDING",
    }
    append_unique(state["repair_messages_pending"], pending, "repair_message_id")
    record_repair_transition(
        state,
        pack_id=message["pack_id"],
        failed_generation=failed_generation,
        repair_state="OWNER_REPLACEMENT_PENDING",
        source_result_id=source_result_id,
        repair_message_id=message["message_id"],
    )


def supersede_repairs_with_replacement(
    state: dict[str, Any], message: dict[str, Any]
) -> None:
    retained: list[dict[str, Any]] = []
    for item in state["repair_messages_pending"]:
        direct_replacement = (
            item.get("repair_message_id") == message.get("parent_message_id")
        )
        if (
            item.get("pack_id") == message["pack_id"]
            and (
                direct_replacement
                or item.get(
                    "failed_generation", item.get("candidate_generation", -1)
                )
                < message["candidate_generation"]
            )
        ):
            record_repair_transition(
                state,
                pack_id=message["pack_id"],
                failed_generation=item.get(
                    "failed_generation", item.get("candidate_generation", -1)
                ),
                repair_state="SUPERSEDED_BY_REPLACEMENT",
                source_result_id=item.get("source_result_id"),
                repair_message_id=item.get("repair_message_id"),
                replacement_message_id=message["message_id"],
            )
            continue
        retained.append(item)
    state["repair_messages_pending"] = retained


def pending_action(
    state: dict[str, Any],
    record: dict[str, Any],
    action_type: str,
    *,
    reason: str,
) -> None:
    message = record["message"]
    value = {
        "action_id": canonical_hash(
            {
                "action_type": action_type,
                "source_message_id": message["message_id"],
                "candidate_identity": record["candidate_identity"],
            }
        ),
        "action_type": action_type,
        "source_message_id": message["message_id"],
        "source_mailbox_commit": record["mailbox_commit"],
        "source_message_sha256": record["message_sha256"],
        "pack_id": message["pack_id"],
        "candidate_generation": message["candidate_generation"],
        "candidate_identity": record["candidate_identity"],
        "reason": reason,
        "created_at": utc_now(),
        "state": "AWAITING_EXACT_PREPARED_SEMANTIC_INPUT",
    }
    append_unique(state["pending_semantic_actions"], value, "action_id")


def queue_record(record: dict[str, Any]) -> dict[str, Any]:
    message = record["message"]
    return {
        "message_id": message["message_id"],
        "pack_id": message["pack_id"],
        "candidate_generation": message["candidate_generation"],
        "candidate_identity": record["candidate_identity"],
        "mailbox_commit": record["mailbox_commit"],
        "mailbox_path": record["mailbox_path"],
        "message_sha256": record["message_sha256"],
    }


def result_role(message: dict[str, Any], config: dict[str, Any]) -> str:
    sender = message.get("sender_role")
    if sender in config["allowed_t10_sender_roles"]:
        return "T10"
    if sender in config["allowed_tester_sender_roles"]:
        return "TESTER"
    raise RouterError(
        f"result sender is not authorized: {message.get('message_id')} {sender}"
    )


def consume_compatibility_record(
    state: dict[str, Any], record: dict[str, Any]
) -> None:
    entry = record["compatibility_entry"]
    message = record["message"]
    message_id = message["message_id"]
    existing = state["consumed_messages"].get(message_id)
    if existing:
        if existing["message_sha256"] != record["message_sha256"]:
            raise RouterError(
                f"compatibility message ID reused with different content: {message_id}"
            )
        return
    event = {
        "entry_key": entry["entry_key"],
        "message_id": message_id,
        "pack_id": entry["pack_affected"],
        "mailbox_commit": record["mailbox_commit"],
        "mailbox_path": record["mailbox_path"],
        "message_sha256": record["message_sha256"],
        "disposition": entry["current_disposition"],
        "replay_behavior": entry["replay_behavior"],
    }
    append_unique(state["compatibility_events"], event, "entry_key")
    state["consumed_messages"][message_id] = {
        "message_sha256": record["message_sha256"],
        "mailbox_commit": record["mailbox_commit"],
        "candidate_identity": record["candidate_identity"],
        "duplicate": False,
        "compatibility_entry_key": entry["entry_key"],
    }
    canonical_key = entry.get("canonical_recomputed_idempotency_key")
    if canonical_key:
        prior = state["idempotency_keys"].get(canonical_key)
        if prior and prior != record["message_sha256"]:
            raise RouterError("conflicting semantic idempotency keys")
        state["idempotency_keys"][canonical_key] = record["message_sha256"]
    if (
        entry["current_disposition"]
        == "PACK_LOCAL_QUARANTINE_SUPERSESSION_REQUIRED"
    ):
        block = {
            "pack_id": entry["pack_affected"],
            "message_id": message_id,
            "message_sha256": record["message_sha256"],
            "mailbox_commit": record["mailbox_commit"],
            "reason": "PACK_LOCAL_INVALID_MESSAGE_REQUIRES_EXACT_SUPERSESSION",
        }
        state["blocked_packs"][entry["pack_affected"]] = block
        append_unique(state["quarantined_messages"], block, "message_sha256")


def consume_pack_local_quarantine(
    state: dict[str, Any], record: dict[str, Any]
) -> None:
    message = record["message"]
    message_id = message["message_id"]
    existing = state["consumed_messages"].get(message_id)
    if existing:
        if existing["message_sha256"] != record["message_sha256"]:
            raise RouterError(
                f"pack-local invalid message ID reused: {message_id}"
            )
        return
    prior = state["idempotency_keys"].get(message["idempotency_key"])
    if prior and prior != record["message_sha256"]:
        raise RouterError("conflicting semantic idempotency keys")
    state["idempotency_keys"][message["idempotency_key"]] = record[
        "message_sha256"
    ]
    block = {
        "pack_id": message["pack_id"],
        "message_id": message_id,
        "message_sha256": record["message_sha256"],
        "mailbox_commit": record["mailbox_commit"],
        "reason": "PACK_LOCAL_SCHEMA_DEFECT",
        "validation_error": record["validation_error"],
    }
    state["blocked_packs"][message["pack_id"]] = block
    append_unique(state["quarantined_messages"], block, "message_sha256")
    state["consumed_messages"][message_id] = {
        "message_sha256": record["message_sha256"],
        "mailbox_commit": record["mailbox_commit"],
        "candidate_identity": record["candidate_identity"],
        "duplicate": False,
        "pack_local_quarantine": True,
    }


def consume_record(
    state: dict[str, Any], record: dict[str, Any], config: dict[str, Any]
) -> None:
    record_kind = record.get("record_kind", "VALID")
    if record_kind == "COMPATIBILITY":
        consume_compatibility_record(state, record)
        return
    if record_kind == "PACK_LOCAL_QUARANTINE":
        consume_pack_local_quarantine(state, record)
        return
    if record_kind != "VALID":
        raise RouterError(f"unknown mailbox record kind: {record_kind}")
    message = record["message"]
    message_id = message["message_id"]
    existing = state["consumed_messages"].get(message_id)
    if existing:
        if existing["message_sha256"] != record["message_sha256"]:
            raise RouterError(f"message ID reused with different content: {message_id}")
        return
    prior_key = state["idempotency_keys"].get(message["idempotency_key"])
    if prior_key and prior_key != record["message_sha256"]:
        raise RouterError("conflicting semantic idempotency keys")
    state["idempotency_keys"][message["idempotency_key"]] = record[
        "message_sha256"
    ]
    state["consumed_messages"][message_id] = {
        "message_sha256": record["message_sha256"],
        "mailbox_commit": record["mailbox_commit"],
        "candidate_identity": record["candidate_identity"],
        "duplicate": False,
    }
    blocked = state["blocked_packs"].get(message["pack_id"])
    if (
        blocked
        and message.get("parent_message_id") == blocked.get("message_id")
        and isinstance(message.get("exact_artifact_hashes"), (dict, list))
    ):
        del state["blocked_packs"][message["pack_id"]]
    if message["message_type"] == "CANDIDATE_SUBMISSION":
        prior_candidate = state["candidate_identities"].get(record["candidate_identity"])
        if prior_candidate and prior_candidate != message_id:
            state["duplicate_observations"].append(
                {
                    "message_id": message_id,
                    "reason": "CANDIDATE_IDENTITY_ALREADY_OBSERVED",
                    "original_message_id": prior_candidate,
                    "candidate_identity": record["candidate_identity"],
                }
            )
            return
        state["candidate_identities"][record["candidate_identity"]] = message_id
        state["active_preflight"] = [
            item
            for item in state["active_preflight"]
            if not (
                item.get("pack_id") == message["pack_id"]
                and item.get("candidate_generation", -1)
                < message["candidate_generation"]
            )
        ]
        supersede_repairs_with_replacement(state, message)
        state["pending_semantic_actions"] = [
            item
            for item in state["pending_semantic_actions"]
            if not (
                item.get("pack_id") == message["pack_id"]
                and item.get("candidate_generation", -1)
                < message["candidate_generation"]
                and item.get("action_type")
                in {
                    "RUN_MECHANICAL_PREFLIGHT",
                    "PUBLISH_CONSOLIDATED_OWNER_REPAIR",
                }
            )
        ]
        append_unique(
            state["active_preflight"], queue_record(record), "candidate_identity"
        )
        pending_action(
            state,
            record,
            "RUN_MECHANICAL_PREFLIGHT",
            reason=(
                "Candidate publication is a routing event. Exact deterministic "
                "mechanical admission remains required before BDS or T10."
            ),
        )
        return
    if message["message_type"] == "MECHANICAL_PREFLIGHT_RESULT":
        status = message.get("mechanical_status")
        candidate_message_id = message.get("parent_message_id")
        state["active_preflight"] = [
            item
            for item in state["active_preflight"]
            if item.get("message_id") != candidate_message_id
        ]
        state["pending_semantic_actions"] = [
            item
            for item in state["pending_semantic_actions"]
            if not (
                item.get("source_message_id") == candidate_message_id
                and item.get("action_type") == "RUN_MECHANICAL_PREFLIGHT"
            )
        ]
        if status == "PASS":
            pending_action(
                state,
                record,
                "ROUTE_MECHANICALLY_ADMITTED_CANDIDATE_TO_TESTER",
                reason=(
                    "Validated mechanical PASS authority requires exact prepared "
                    "tester intake; candidate bytes remain immutable."
                ),
            )
            item = {
                "pack_id": message["pack_id"],
                "candidate_generation": message["candidate_generation"],
                "source_message_id": message_id,
            }
            append_unique(state["audit_backlog"], item, "source_message_id")
        elif status == "FAIL":
            result = {
                **queue_record(record),
                "message_type": message["message_type"],
                "sender_role": message["sender_role"],
            }
            mark_result_awaiting_routing(state, result)
            pending_action(
                state,
                record,
                "PUBLISH_CONSOLIDATED_OWNER_REPAIR",
                reason=(
                    "Mechanical findings return only to the durable pack owner "
                    "and must never consume T10 capacity."
                ),
            )
        else:
            raise RouterError("mechanical preflight result status is ambiguous")
        return
    if message["message_type"] == "TESTER_INTAKE":
        state["active_preflight"] = [
            item
            for item in state["active_preflight"]
            if item.get("message_id") != message.get("parent_message_id")
        ]
        state["pending_semantic_actions"] = [
            item
            for item in state["pending_semantic_actions"]
            if not (
                (
                    item.get("source_message_id") == message.get("parent_message_id")
                    and item.get("action_type")
                    in {
                        "RUN_MECHANICAL_PREFLIGHT",
                        "REPAIR_TESTER_INFRASTRUCTURE_AND_RETRY_UNCHANGED_CANDIDATE",
                    }
                )
                or (
                    item.get("pack_id") == message["pack_id"]
                    and item.get("candidate_generation")
                    == message["candidate_generation"]
                    and item.get("action_type")
                    == "REPAIR_TESTER_INFRASTRUCTURE_AND_RETRY_UNCHANGED_CANDIDATE"
                )
            )
        ]
        append_unique(state["tester_queued"], queue_record(record), "message_id")
        return
    if message["message_type"] in TEST_RESULT_TYPES:
        key = candidate_key(message)
        result = {
            **queue_record(record),
            "message_type": message["message_type"],
            "sender_role": message["sender_role"],
        }
        role = result_role(message, config)
        if role == "T10":
            state["audit_results"][key] = result
            current = state.get("t10_active")
            matches_active = (
                current
                and current.get("pack_id") == message["pack_id"]
                and current.get("candidate_generation")
                == message["candidate_generation"]
            )
            if matches_active:
                state["t10_active"] = None
            else:
                state["protocol_defects"].append(
                    {
                        "message_id": message_id,
                        "defect": "T10_RESULT_DOES_NOT_MATCH_ACTIVE_PROJECTION",
                        "observed_pack_id": message["pack_id"],
                        "observed_generation": message["candidate_generation"],
                        "active_projection": current,
                    }
                )
            if message["message_type"] not in {"TEST_PASS"}:
                mark_result_awaiting_routing(state, result)
                pending_action(
                    state,
                    record,
                    "PUBLISH_CONSOLIDATED_OWNER_REPAIR",
                    reason=(
                        "T10 returned a substantive non-pass. The original durable "
                        "owner requires one exact consolidated repair message."
                    ),
                )
        else:
            state["tester_results"][key] = result
            state["tester_active"] = [
                item
                for item in state["tester_active"]
                if not (
                    item.get("pack_id") == message["pack_id"]
                    and item.get("candidate_generation")
                    == message["candidate_generation"]
                )
            ]
            state["tester_queued"] = [
                item
                for item in state["tester_queued"]
                if not (
                    item.get("pack_id") == message["pack_id"]
                    and item.get("candidate_generation")
                    == message["candidate_generation"]
                )
            ]
            if message["message_type"] == "TEST_FAIL_PRODUCT":
                state["audit_backlog"] = [
                    item
                    for item in state["audit_backlog"]
                    if not (
                        item.get("pack_id") == message["pack_id"]
                        and item.get("candidate_generation")
                        == message["candidate_generation"]
                    )
                ]
                queued = state.get("t10_queued")
                if (
                    queued
                    and queued.get("pack_id") == message["pack_id"]
                    and queued.get("candidate_generation")
                    == message["candidate_generation"]
                ):
                    state["t10_queued"] = None
                mark_result_awaiting_routing(state, result)
                pending_action(
                    state,
                    record,
                    "PUBLISH_CONSOLIDATED_OWNER_REPAIR",
                    reason=(
                        "The tester reported a product defect. The frozen candidate "
                        "must remain immutable and the original owner must receive "
                        "one exact repair message."
                    ),
                )
            elif message["message_type"] == "TEST_FAIL_INFRASTRUCTURE":
                pending_action(
                    state,
                    record,
                    "REPAIR_TESTER_INFRASTRUCTURE_AND_RETRY_UNCHANGED_CANDIDATE",
                    reason=(
                        "Tester infrastructure failed independently of product "
                        "behavior; preserve candidate identity."
                    ),
                )
        tester = state["tester_results"].get(key, {}).get("message_type")
        audit = state["audit_results"].get(key, {}).get("message_type")
        if tester == "TEST_PASS" and audit == "TEST_PASS":
            append_unique(
                state["integration_intake_pending"],
                {
                    "pack_id": message["pack_id"],
                    "candidate_generation": message["candidate_generation"],
                    "candidate_key": key,
                },
                "candidate_key",
            )
            pending_action(
                state,
                record,
                "PUBLISH_INTEGRATION_INTAKE",
                reason=(
                    "Exact candidate has both tester and T10 TEST_PASS projections; "
                    "integration still requires an immutable prepared intake."
                ),
            )
        return
    if message["message_type"] == "REPAIR_INSTRUCTION":
        state["active_preflight"] = [
            item
            for item in state["active_preflight"]
            if item.get("message_id") != message.get("parent_message_id")
        ]
        state["pending_semantic_actions"] = [
            item
            for item in state["pending_semantic_actions"]
            if not (
                item.get("source_message_id") == message.get("parent_message_id")
                and item.get("action_type")
                in {
                    "RUN_MECHANICAL_PREFLIGHT",
                    "PUBLISH_CONSOLIDATED_OWNER_REPAIR",
                }
            )
        ]
        mark_repair_instruction_published(state, message)
        return
    if message["message_type"] == "INTEGRATION_INTAKE":
        append_unique(
            state["integration_intake_pending"], queue_record(record), "message_id"
        )
        return
    if message["message_type"] in {"AUDIT_INTAKE", "AUDIT_QUEUE_DECISION"}:
        # Prose is never machine authority. Accept the current routing_state
        # field and the established explicit audit_slot field only.
        routing_state = message.get("routing_state", message.get("audit_slot"))
        item = {
            "pack_id": message["pack_id"],
            "candidate_generation": message["candidate_generation"],
            "source_message_id": message_id,
        }
        if routing_state == "ACTIVE":
            state["pending_semantic_actions"] = [
                entry
                for entry in state["pending_semantic_actions"]
                if entry.get("action_type") != "PROMOTE_T10_QUEUED"
            ]
            state["audit_backlog"] = [
                entry
                for entry in state["audit_backlog"]
                if not (
                    entry.get("pack_id") == item["pack_id"]
                    and entry.get("candidate_generation")
                    == item["candidate_generation"]
                )
            ]
            queued = state.get("t10_queued")
            if (
                queued
                and queued.get("pack_id") == item["pack_id"]
                and queued.get("candidate_generation") == item["candidate_generation"]
            ):
                state["t10_queued"] = None
            if state.get("t10_active") not in (None, item):
                raise RouterError("T10 active slot already occupied")
            state["t10_active"] = item
        elif routing_state == "QUEUED":
            state["audit_backlog"] = [
                entry
                for entry in state["audit_backlog"]
                if not (
                    entry.get("pack_id") == item["pack_id"]
                    and entry.get("candidate_generation")
                    == item["candidate_generation"]
                )
            ]
            active = state.get("t10_active")
            if (
                active
                and active.get("pack_id") == item["pack_id"]
                and active.get("candidate_generation") == item["candidate_generation"]
            ):
                return
            if state.get("t10_queued") not in (None, item):
                raise RouterError("T10 queued slot already occupied")
            state["t10_queued"] = item
        elif routing_state == "BACKLOG":
            append_unique(state["audit_backlog"], item, "source_message_id")
        else:
            state["protocol_defects"].append(
                {
                    "message_id": message_id,
                    "defect": "AUDIT_ROUTE_MISSING_STRUCTURED_ROUTING_STATE",
                }
            )
            pending_action(
                state,
                record,
                "RESOLVE_T10_ROUTE_STATE",
                reason=(
                    "Audit routing prose is not machine-decidable. An exact "
                    "structured ACTIVE, QUEUED, or BACKLOG decision is required."
                ),
            )
        return
    if message["message_type"] in {
        "GLOBAL_ALLOCATION_CONFLICT",
        "GLOBAL_AUTHORITY_FAILURE",
    }:
        raise RouterError(
            f"global authority halt requested by {message['message_id']}"
        )
    if message["message_type"] in {
        "GLOBAL_HARD_STOP",
        "AUTHORITY_CORRUPTION",
        "CLEAN_ROOM_CONTAMINATION",
    }:
        pending_action(
            state,
            record,
            "PAUSE_AFFECTED_AUTHORITY_GRAPH",
            reason="A committed hard-stop message requires immediate T1 disposition.",
        )
        return
    if message["message_type"] in {
        "SHARED_RUNTIME_INTERFACE_AUTHORITY_REQUEST",
        "SHARED_RUNTIME_REQUEST",
    }:
        pending_action(
            state,
            record,
            "ROUTE_PLATFORM_REQUEST_TO_T2",
            reason=(
                "A current source-neutral Platform request requires an exact T1 "
                "admission assignment before the exclusive T2 writer may act."
            ),
        )
        return
    if message["message_type"] == "PLATFORM_ADMISSION_ASSIGNMENT":
        state["pending_semantic_actions"] = [
            action
            for action in state["pending_semantic_actions"]
            if not (
                action.get("action_type")
                in {"ROUTE_PLATFORM_REQUEST_TO_T2", "REVIEW_UNCLASSIFIED_MESSAGE"}
                and action.get("source_message_id")
                == message.get("parent_message_id")
            )
        ]
        state["protocol_defects"] = [
            defect
            for defect in state["protocol_defects"]
            if defect.get("message_id") != message.get("parent_message_id")
        ]
        return
    if message["message_type"] in {
        "SHARED_RUNTIME_BINDING_RESPONSE",
        "PLATFORM_ADMISSION_RESULT",
        "PLATFORM_ADMISSION_DECISION_RESULT",
        "PLATFORM_CHANGE_ACCEPTED",
        "PLATFORM_CHANGE_NOT_REQUIRED",
        "PACK_LOCAL_ADAPTER_REQUIRED",
        "PLATFORM_CHANGE_REJECTED_WITH_REASON",
    }:
        # The committed T2 result is already addressed to the durable pack
        # owner. The router records it through replay but does not reinterpret
        # or repair the Platform decision.
        return
    if message["message_type"] not in {"PACK_ACCEPTED_AND_INTEGRATED"}:
        state["protocol_defects"].append(
            {
                "message_id": message_id,
                "defect": "UNCLASSIFIED_MESSAGE_REQUIRES_EXACT_ROUTING_RULE",
                "message_type": message["message_type"],
            }
        )
        pending_action(
            state,
            record,
            "REVIEW_UNCLASSIFIED_MESSAGE",
            reason=(
                "No deterministic routing rule exists for this immutable message; "
                "do not silently treat it as complete."
            ),
        )


def reconcile_tester_projection(
    state: dict[str, Any], tester_state_path: Path
) -> None:
    if not tester_state_path.exists():
        return
    tester_state = load_json(tester_state_path)
    active = []
    for intake_id, job in tester_state.get("jobs", {}).items():
        if job.get("state") not in {"ACTIVE", "DISPATCHED", "RUNNING", "STAGED"}:
            continue
        active.append(
            {
                "message_id": intake_id,
                "job_id": job.get("job_id"),
                "pack_id": job.get("pack_id"),
                "state": job.get("state"),
            }
        )
    state["tester_active"] = active


def find_message_record(
    repository: Path, head: str, message_id: str
) -> dict[str, Any]:
    paths = [
        path
        for path in run_git(repository, "ls-tree", "-r", "--name-only", head).splitlines()
        if PurePosixPath(path).stem == message_id
        and PurePosixPath(path).parts
        and PurePosixPath(path).parts[0] in MESSAGE_ROOTS
    ]
    if len(paths) != 1:
        raise RouterError(
            f"message authority is ambiguous: {message_id} matches={len(paths)}"
        )
    path = paths[0]
    raw = subprocess.run(
        ["/usr/bin/git", "-C", str(repository), "show", f"{head}:{path}"],
        capture_output=True,
        check=False,
    )
    if raw.returncode:
        raise RouterError(f"cannot read message authority: {message_id}")
    return validate_message(raw.stdout, path, head)


def derive_deterministic_actions(
    state: dict[str, Any], repository: Path, head: str
) -> None:
    if state.get("t10_active") is None and state.get("t10_queued"):
        source_id = state["t10_queued"].get("source_message_id")
        if not source_id:
            raise RouterError("queued T10 authority lacks source message")
        pending_action(
            state,
            find_message_record(repository, head, source_id),
            "PROMOTE_T10_QUEUED",
            reason="T10 active slot is empty and the exact queued authority is valid.",
        )
    if state.get("t10_queued") is None and state["audit_backlog"]:
        source_id = state["audit_backlog"][0].get("source_message_id")
        if not source_id:
            raise RouterError("audit backlog authority lacks source message")
        pending_action(
            state,
            find_message_record(repository, head, source_id),
            "MOVE_FIRST_AUDIT_BACKLOG_ITEM_TO_QUEUED",
            reason="T10 queued slot is empty and the first immutable backlog item fits.",
        )


def semantic_message_id(action: dict[str, Any], suffix: str) -> str:
    pack = re.sub(r"[^A-Z0-9]+", "-", action["pack_id"].upper()).strip("-")[:32]
    return (
        f"MSG-T1R-{pack}-{suffix}-G{action['candidate_generation']:06d}-"
        f"{action['action_id'][:12].upper()}"
    )


def build_audit_route_message(
    action: dict[str, Any], source: dict[str, Any], slot: str
) -> tuple[dict[str, Any], str]:
    message = source["message"]
    suffix = "AUDIT-ACTIVE" if slot == "ACTIVE" else "AUDIT-QUEUED"
    output = {
        "schema_version": "1.0.0",
        "message_id": semantic_message_id(action, suffix),
        "message_type": "AUDIT_INTAKE",
        "pack_id": message["pack_id"],
        "sender_role": "T1_FACTORY_ROUTER",
        "recipient_role": "T10_INDEPENDENT_AUDIT_SERVICE",
        "created_at": action["created_at"],
        "source_authority_commit": message["source_authority_commit"],
        "source_authority_tree": message["source_authority_tree"],
        "candidate_generation": message["candidate_generation"],
        "exact_artifact_hashes": message["exact_artifact_hashes"],
        "parent_message_id": message["message_id"],
        "required_action": f"PROCESS_EXACT_IMMUTABLE_CANDIDATE_IN_{slot}_AUDIT_SLOT",
        "idempotency_key": canonical_hash(
            {"action_id": action["action_id"], "audit_slot": slot}
        ),
        "proof_boundary": list(message["proof_boundary"]),
        "audit_slot": slot,
        "source_candidate_identity": action["candidate_identity"],
        "source_message_sha256": source["message_sha256"],
    }
    target = (
        f"integration_intake/{message['pack_id']}/{output['message_id']}.json"
    )
    return output, target


def find_candidate_owner(
    repository: Path, head: str, pack_id: str, generation: int
) -> str:
    matches: list[str] = []
    for path in run_git(repository, "ls-tree", "-r", "--name-only", head).splitlines():
        posix = PurePosixPath(path)
        if not posix.parts or posix.parts[0] != "candidate_submissions":
            continue
        raw = subprocess.run(
            ["/usr/bin/git", "-C", str(repository), "show", f"{head}:{path}"],
            capture_output=True,
            check=False,
        )
        if raw.returncode:
            continue
        try:
            value = json.loads(raw.stdout)
        except json.JSONDecodeError:
            continue
        if (
            value.get("message_type") == "CANDIDATE_SUBMISSION"
            and value.get("pack_id") == pack_id
            and value.get("candidate_generation") == generation
        ):
            matches.append(str(value.get("sender_role")))
    owners = sorted(set(matches))
    if len(owners) != 1:
        raise RouterError(
            f"durable candidate owner is ambiguous: {pack_id} generation={generation}"
        )
    return owners[0]


def build_owner_repair_message(
    action: dict[str, Any], source: dict[str, Any], repository: Path, head: str
) -> tuple[dict[str, Any], str]:
    result = source["message"]
    findings = result.get("findings")
    if not isinstance(findings, list) or not findings:
        raise RouterError("repair result has no immutable findings")
    for finding in findings:
        if not isinstance(finding, dict) or not finding.get("finding_id"):
            raise RouterError("repair finding is malformed")
    owner = find_candidate_owner(
        repository,
        head,
        result["pack_id"],
        result["candidate_generation"],
    )
    output = {
        "schema_version": "1.0.0",
        "message_id": semantic_message_id(action, "OWNER-REPAIR"),
        "message_type": "REPAIR_INSTRUCTION",
        "pack_id": result["pack_id"],
        "sender_role": "T1_FACTORY_ROUTER",
        "recipient_role": owner,
        "created_at": action["created_at"],
        "source_authority_commit": result["source_authority_commit"],
        "source_authority_tree": result["source_authority_tree"],
        "candidate_generation": result["candidate_generation"] + 1,
        "failed_candidate_generation": result["candidate_generation"],
        "required_replacement_generation": result["candidate_generation"] + 1,
        "exact_artifact_hashes": result["exact_artifact_hashes"],
        "parent_message_id": result["message_id"],
        "required_action": "PRESERVE_FAILED_CANDIDATE_AND_PUBLISH_ONE_REPLACEMENT_GENERATION",
        "idempotency_key": canonical_hash(
            {
                "action_id": action["action_id"],
                "source_result_sha256": source["message_sha256"],
                "finding_ids": [item["finding_id"] for item in findings],
            }
        ),
        "proof_boundary": list(result["proof_boundary"]),
        "source_result_sha256": source["message_sha256"],
        "findings": findings,
        "finding_ids": [item["finding_id"] for item in findings],
        "allowed_repair_scope": [
            scope
            for item in findings
            for scope in item.get("allowed_repair_scope", [])
        ],
        "required_regression_gates": [
            gate
            for item in findings
            for gate in item.get("required_regression_gates", [])
        ],
        "fresh_candidate_bound_isolation_required": True,
    }
    target = f"worker_repairs/{result['pack_id']}/{output['message_id']}.json"
    return output, target


def prepared_action_message(
    config: dict[str, Any],
    action: dict[str, Any],
    source: dict[str, Any],
) -> tuple[dict[str, Any], str] | None:
    prepared = (
        Path(config["runtime_root"])
        / "prepared_semantic_messages"
        / f"{action['action_id']}.json"
    )
    if not prepared.exists():
        return None
    value = load_json(prepared)
    expected_type = {
        "RUN_MECHANICAL_PREFLIGHT": "MECHANICAL_PREFLIGHT_RESULT",
        "ROUTE_MECHANICALLY_ADMITTED_CANDIDATE_TO_TESTER": "TESTER_INTAKE",
    }[action["action_type"]]
    source_hashes = source["message"]["exact_artifact_hashes"]
    prepared_hashes = value.get(
        "candidate_exact_artifact_hashes", value.get("exact_artifact_hashes")
    )
    hash_binding_valid = prepared_hashes == source_hashes
    if expected_type == "TESTER_INTAKE":
        required_package_roles = {
            role
            for role in ("behavior_pack", "resource_pack", "mcaddon")
            if role in source_hashes
        }
        hash_binding_valid = bool(required_package_roles) and all(
            value.get("exact_artifact_hashes", {}).get(role)
            == source_hashes.get(role)
            for role in required_package_roles
        )
    if (
        value.get("message_type") != expected_type
        or value.get("pack_id") != action["pack_id"]
        or value.get("candidate_generation") != action["candidate_generation"]
        or value.get("parent_message_id") != action["source_message_id"]
        or not hash_binding_valid
        or value.get("source_message_sha256") != source["message_sha256"]
    ):
        raise RouterError("prepared semantic action binding mismatch")
    target_root = (
        "final_decisions"
        if expected_type == "MECHANICAL_PREFLIGHT_RESULT"
        else "tester_intake"
    )
    target = f"{target_root}/{value['pack_id']}/{value['message_id']}.json"
    return value, target


@contextlib.contextmanager
def singleton_lock(runtime_root: Path) -> Iterator[bool]:
    lock_path = runtime_root / "routing-cycle.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+")
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


def publish_semantic_message(
    config: dict[str, Any],
    *,
    message_path: Path,
    target: str,
    expected_head: str,
    actor: str,
) -> dict[str, Any]:
    """Publish an already-prepared message; never construct semantic content."""
    publisher = Path(config["publisher"])
    if not publisher.is_file():
        raise RouterError("canonical mailbox publisher is unavailable")
    prepared_root = Path(config["runtime_root"]) / "prepared_semantic_messages"
    resolved_message = message_path.resolve()
    if prepared_root.resolve() not in resolved_message.parents:
        raise RouterError("semantic message is outside prepared runtime root")
    target_root = PurePosixPath(target).parts[0] if PurePosixPath(target).parts else ""
    if target_root not in {
        "tester_intake",
        "worker_repairs",
        "integration_intake",
        "final_decisions",
    }:
        raise RouterError("router semantic target is not permitted")
    if actor != "T1_FACTORY_ROUTER":
        raise RouterError("router semantic actor rejected")
    result = subprocess.run(
        [
            sys.executable,
            str(publisher),
            "--message",
            str(message_path.resolve()),
            "--target",
            target,
            "--expected-head",
            expected_head,
            "--actor",
            actor,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RouterError(f"semantic publication failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RouterError("publisher returned malformed receipt") from error


def execute_one_semantic_action(
    state: dict[str, Any],
    config: dict[str, Any],
    repository: Path,
    head: str,
) -> tuple[str, bool]:
    """Publish at most one deterministic action, preserving mailbox ordering."""
    for action in list(state["pending_semantic_actions"]):
        if action["action_type"] not in EXECUTABLE_ACTION_TYPES:
            continue
        if action["action_id"] in state["executed_semantic_actions"]:
            state["pending_semantic_actions"].remove(action)
            continue
        source = find_message_record(
            repository, head, action["source_message_id"]
        )
        if (
            source["message_sha256"] != action["source_message_sha256"]
            or source["candidate_identity"] != action["candidate_identity"]
        ):
            raise RouterError("semantic action source authority changed")
        action_type = action["action_type"]
        prepared: tuple[dict[str, Any], str] | None = None
        if action_type in {
            "RUN_MECHANICAL_PREFLIGHT",
            "ROUTE_MECHANICALLY_ADMITTED_CANDIDATE_TO_TESTER",
        }:
            prepared = prepared_action_message(config, action, source)
            if prepared is None:
                continue
            output, target = prepared
        elif action_type == "PROMOTE_T10_QUEUED":
            if state.get("t10_active") is not None:
                state["pending_semantic_actions"].remove(action)
                continue
            output, target = build_audit_route_message(action, source, "ACTIVE")
        elif action_type == "MOVE_FIRST_AUDIT_BACKLOG_ITEM_TO_QUEUED":
            if state.get("t10_queued") is not None:
                state["pending_semantic_actions"].remove(action)
                continue
            if (
                not state["audit_backlog"]
                or state["audit_backlog"][0].get("source_message_id")
                != action["source_message_id"]
            ):
                raise RouterError("audit backlog order changed during queued promotion")
            output, target = build_audit_route_message(action, source, "QUEUED")
        elif action_type == "PUBLISH_CONSOLIDATED_OWNER_REPAIR":
            output, target = build_owner_repair_message(
                action, source, repository, head
            )
        else:
            continue
        prepared_root = Path(config["runtime_root"]) / "prepared_semantic_messages"
        prepared_path = prepared_root / f"{action['action_id']}.json"
        atomic_write_json(prepared_path, output)
        receipt = publish_semantic_message(
            config,
            message_path=prepared_path,
            target=target,
            expected_head=head,
            actor="T1_FACTORY_ROUTER",
        )
        new_head = receipt.get("commit")
        if not HEX40.fullmatch(str(new_head)):
            raise RouterError("semantic publisher returned invalid commit")
        published = find_message_record(repository, new_head, output["message_id"])
        if published["message_sha256"] != receipt.get("message_sha256"):
            raise RouterError("published semantic message receipt mismatch")
        state["executed_semantic_actions"][action["action_id"]] = receipt
        state["pending_semantic_actions"] = [
            item
            for item in state["pending_semantic_actions"]
            if item["action_id"] != action["action_id"]
        ]
        consume_record(state, published, config)
        return new_head, True
    return head, False


def run_cycle(config: dict[str, Any]) -> dict[str, Any]:
    runtime = Path(config["runtime_root"])
    runtime.mkdir(parents=True, exist_ok=True)
    state_path = runtime / "routing_state.json"
    state = (
        upgrade_runtime_state(load_json(state_path))
        if state_path.exists()
        else initial_state(config)
    )
    validate_runtime_state(state)
    repository = Path(config["mailbox_repository"])
    if not repository.is_dir():
        raise RouterError("mailbox repository is unavailable")
    head = run_git(repository, "rev-parse", config["mailbox_ref"])
    if not HEX40.fullmatch(head):
        raise RouterError("invalid mailbox authority HEAD")
    compatibility_entries = load_compatibility_ledger(
        Path(config["compatibility_ledger"]),
        repository,
        config["compatibility_ledger_expected_entries"],
    )
    cursor = state["last_consumed_mailbox_commit"]
    started = utc_now()
    state["current_cycle_started_at"] = started
    state["last_polled_mailbox_commit"] = head
    records = discover_messages(
        repository, cursor, head, compatibility_entries
    )
    state["unseen_message_count"] = len(records)
    for record in records:
        consume_record(state, record, config)
    derive_deterministic_actions(state, repository, head)
    published_count = 0
    if config.get("semantic_executor_enabled", False):
        for _ in range(16):
            head, published = execute_one_semantic_action(
                state, config, repository, head
            )
            if not published:
                break
            published_count += 1
            derive_deterministic_actions(state, repository, head)
        else:
            raise RouterError("semantic executor exceeded bounded transition limit")
    reconcile_tester_projection(state, Path(config["local_tester_state"]))
    if len(state["tester_active"]) > config["max_tester_active"]:
        raise RouterError("tester active capacity exceeded")
    active_count = 1 if state.get("t10_active") else 0
    queued_count = 1 if state.get("t10_queued") else 0
    if active_count > config["max_t10_active"] or queued_count > config["max_t10_queued"]:
        raise RouterError("T10 active/queued capacity exceeded")
    state["last_polled_mailbox_commit"] = head
    state["last_consumed_mailbox_commit"] = head
    state["last_successful_cycle_at"] = utc_now()
    state["current_cycle_started_at"] = None
    state["unseen_message_count"] = 0
    validate_runtime_state(state)
    atomic_write_json(state_path, state)
    return {
        "status": "CONSUMED" if records or published_count else "NO_CHANGE",
        "message_count": len(records) + published_count,
        "published_count": published_count,
        "mailbox_head": head,
    }


def status(config: dict[str, Any]) -> dict[str, Any]:
    state_path = Path(config["runtime_root"]) / "routing_state.json"
    state = (
        upgrade_runtime_state(load_json(state_path))
        if state_path.exists()
        else initial_state(config)
    )
    validate_runtime_state(state)
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="crazycraft-factory-router")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("factory-router-config.json"),
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--run-once", action="store_true")
    modes.add_argument("--status", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = config_from(args.config)
        if args.status:
            print(json.dumps(status(config), sort_keys=True, indent=2))
            return 0
        runtime = Path(config["runtime_root"])
        with singleton_lock(runtime) as acquired:
            if not acquired:
                return 0
            run_cycle(config)
        return 0
    except RouterError as error:
        print(f"factory-router: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
