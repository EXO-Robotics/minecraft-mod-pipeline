#!/usr/bin/env python3
"""Fail-closed committed-mailbox consumer for exact-package BDS jobs."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REMOTE_ROOT = HERE.parents[2] / "remote-execution"
sys.path.insert(0, str(REMOTE_ROOT))
sys.path.insert(0, str(REMOTE_ROOT / "studio"))

from remote_job_lib import (  # noqa: E402
    ValidationError,
    canonical_bytes,
    payload_hash,
    sha256_bytes,
    sha256_file,
    validate_request,
    validate_safe_relative_path,
    write_json,
)

IMAGE_V2 = (
    "crazycraft-exact-package-qualifier@sha256:"
    "c3adfe3f7cad7c174d23db52dd14da6937901b1df7f9be853c65167086ed811f"
)
ARTIFACT_ROLES = ("behavior_pack", "resource_pack", "mcaddon")
MESSAGE_FIELDS = {
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
    "qualification_request",
    "artifact_sources",
}
RESULT_TYPES = {"TEST_PASS", "TEST_FAIL_PRODUCT", "TEST_FAIL_INFRASTRUCTURE"}
PUBLICATION_RETRY_ATTEMPTS = 120
PUBLICATION_RETRY_DELAY_SECONDS = 0.25
COMPATIBILITY_LEDGER_PATH = HERE / "compatibility" / "EXACT_TESTER_INTAKE_COMPATIBILITY_LEDGER.json"
COMPATIBILITY_KEY_FIELDS = ("mailbox_commit", "message_path", "raw_message_sha256")


def run(argv: list[str], *, cwd: Path | None = None, binary: bool = False) -> Any:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
    )
    if completed.returncode:
        error = completed.stderr
        if isinstance(error, bytes):
            error = error.decode(errors="replace")
        raise ValidationError(f"command failed: {argv[0]}: {error[-500:]}")
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


def message_add_commit(repository: Path, head: str, path: str) -> str:
    commit = git_text(
        repository,
        "log",
        "--diff-filter=A",
        "-1",
        "--format=%H",
        head,
        "--",
        path,
    )
    if len(commit) != 40:
        raise ValidationError(f"message add commit unavailable: {path}")
    return commit


def within(path: Path, roots: list[Path]) -> bool:
    resolved = path.resolve()
    return any(
        resolved == root.resolve() or root.resolve() in resolved.parents
        for root in roots
    )


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text())
    required = {
        "schema_version",
        "mailbox_repository",
        "mailbox_ref",
        "runtime_root",
        "allowed_candidate_roots",
        "allowed_tester_images",
        "max_active_jobs",
        "max_active_per_pack",
        "poll_seconds",
    }
    if set(config) != required or config["schema_version"] != "crazycraft-local-tester-v1":
        raise ValidationError("invalid local tester configuration")
    if config["max_active_jobs"] != 2 or config["max_active_per_pack"] != 1:
        raise ValidationError("tester concurrency policy mismatch")
    if config["allowed_tester_images"] != [IMAGE_V2]:
        raise ValidationError("tester image allowlist mismatch")
    return config


def compatibility_key(commit: str, path: str, raw_sha256: str) -> str:
    return "|".join((commit, path, raw_sha256))


def load_compatibility_ledger(path: Path | None = None) -> dict[str, dict[str, Any]]:
    ledger_path = path or COMPATIBILITY_LEDGER_PATH
    value = json.loads(ledger_path.read_text())
    if set(value) != {
        "schema_version",
        "authority_scope",
        "entries",
        "proof_boundary",
    }:
        raise ValidationError("tester compatibility ledger fields mismatch")
    if (
        value["schema_version"] != "crazycraft-exact-tester-compatibility-v1"
        or value["authority_scope"] != "EXACT_HISTORICAL_TESTER_INTAKE_ONLY"
        or not isinstance(value["entries"], list)
    ):
        raise ValidationError("tester compatibility ledger rejected")
    allowed_entry_fields = {
        "compatibility_key",
        "message_id",
        "mailbox_commit",
        "message_path",
        "raw_message_sha256",
        "historical_role",
        "current_disposition",
        "pack_id",
        "candidate_identity",
        "cursor_advancement_permitted",
        "superseding_authority",
        "terminal_historical_result",
        "replay_behavior",
        "reason_exact_not_general",
    }
    entries: dict[str, dict[str, Any]] = {}
    for entry in value["entries"]:
        if set(entry) != allowed_entry_fields:
            raise ValidationError("tester compatibility entry fields mismatch")
        key = compatibility_key(*(entry[name] for name in COMPATIBILITY_KEY_FIELDS))
        if entry["compatibility_key"] != key or key in entries:
            raise ValidationError("tester compatibility key mismatch")
        if (
            entry["current_disposition"] != "INVALID_SUPERSEDED_TERMINAL"
            or entry["replay_behavior"] != "NEVER_EXECUTE_ADVANCE_DISCOVERY"
            or entry["cursor_advancement_permitted"] is not True
            or len(entry["raw_message_sha256"]) != 64
        ):
            raise ValidationError("tester compatibility disposition rejected")
        entries[key] = entry
    return entries


def verify_bound_mailbox_authority(
    repository: Path,
    head: str,
    authority: dict[str, Any],
) -> dict[str, Any]:
    required = {"message_id", "mailbox_commit", "message_path", "raw_message_sha256"}
    if not required.issubset(authority):
        raise ValidationError("bound tester mailbox authority fields missing")
    raw = git_bytes(repository, f"{head}:{authority['message_path']}")
    if (
        message_add_commit(repository, head, authority["message_path"])
        != authority["mailbox_commit"]
        or sha256_bytes(raw) != authority["raw_message_sha256"]
    ):
        raise ValidationError("bound tester mailbox authority mismatch")
    value = json.loads(raw)
    for name in ("message_id", "parent_message_id", "result"):
        if name in authority and value.get(name) != authority[name]:
            raise ValidationError(f"bound tester mailbox {name} mismatch")
    return value


def verify_exact_compatibility_entry(
    repository: Path,
    head: str,
    entry: dict[str, Any],
    raw: bytes,
) -> None:
    original = json.loads(raw)
    if (
        original.get("message_id") != entry["message_id"]
        or original.get("pack_id") != entry["pack_id"]
        or original.get("candidate_generation")
        != entry["candidate_identity"]["candidate_generation"]
    ):
        raise ValidationError("exact tester compatibility envelope mismatch")
    request = original.get("qualification_request", {})
    bds = request.get("bds", {}) if isinstance(request, dict) else {}
    identity = entry["candidate_identity"]
    comparisons = {
        "repository": bds.get("candidate_repository"),
        "ref": bds.get("candidate_ref"),
        "content_commit": bds.get("content_commit"),
        "content_tree": bds.get("content_tree"),
        "metadata_commit": bds.get("metadata_commit"),
        "metadata_tree": bds.get("metadata_tree"),
        "behavior_pack_sha256": bds.get("behavior_pack_sha256"),
        "resource_pack_sha256": bds.get("resource_pack_sha256"),
        "mcaddon_sha256": bds.get("mcaddon_sha256"),
    }
    if any(identity.get(name) != observed for name, observed in comparisons.items()):
        raise ValidationError("exact tester compatibility candidate mismatch")
    superseding = entry["superseding_authority"]
    verify_bound_mailbox_authority(repository, head, superseding)
    verify_bound_mailbox_authority(
        repository, head, superseding["terminal_result"]
    )
    verify_bound_mailbox_authority(
        repository, head, entry["terminal_historical_result"]
    )


def committed_mailbox_snapshot(
    config: dict[str, Any],
    *,
    compatibility_path: Path | None = None,
) -> dict[str, Any]:
    """Reconstruct tester intake state exclusively from committed mailbox bytes."""

    repository = Path(config["mailbox_repository"]).resolve()
    head = git_text(repository, "rev-parse", config["mailbox_ref"])
    compatibility = load_compatibility_ledger(compatibility_path)
    result_names = git_text(
        repository,
        "ls-tree",
        "-r",
        "--name-only",
        head,
        "--",
        "tester_results",
    ).splitlines()
    results_by_parent: dict[str, dict[str, Any]] = {}
    for name in sorted(value for value in result_names if value.endswith(".json")):
        raw = git_bytes(repository, f"{head}:{name}")
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"committed tester result is malformed: {name}") from exc
        parent = record.get("parent_message_id")
        if not isinstance(parent, str):
            continue
        observed = {
            "message_id": record.get("message_id"),
            "message_type": record.get("message_type"),
            "path": name,
            "add_commit": message_add_commit(repository, head, name),
            "raw_sha256": sha256_bytes(raw),
            "record": record,
        }
        previous = results_by_parent.get(parent)
        if previous is not None and previous["raw_sha256"] != observed["raw_sha256"]:
            raise ValidationError(f"conflicting tester results for intake: {parent}")
        results_by_parent[parent] = observed

    names = git_text(
        repository,
        "ls-tree",
        "-r",
        "--name-only",
        head,
        "--",
        "tester_intake",
    ).splitlines()
    executable: list[dict[str, Any]] = []
    dispositions: list[dict[str, Any]] = []
    pack_local_invalid: list[dict[str, Any]] = []
    terminal_jobs: dict[str, dict[str, Any]] = {}
    observed_job_ids: dict[str, str] = {}
    for name in sorted(value for value in names if value.endswith(".json")):
        raw = git_bytes(repository, f"{head}:{name}")
        raw_sha = sha256_bytes(raw)
        add_commit = message_add_commit(repository, head, name)
        key = compatibility_key(add_commit, name, raw_sha)
        exact_disposition = compatibility.get(key)
        if exact_disposition is not None:
            verify_exact_compatibility_entry(
                repository, head, exact_disposition, raw
            )
            dispositions.append(deepcopy(exact_disposition))
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            pack_local_invalid.append(
                {
                    "rejection_key": key,
                    "message_id": None,
                    "pack_id": Path(name).parent.name,
                    "path": name,
                    "mailbox_commit": add_commit,
                    "raw_message_sha256": raw_sha,
                    "failure": "MALFORMED_JSON",
                    "disposition": "PACK_LOCAL_REJECTION",
                }
            )
            continue
        if "qualification_request" not in record:
            continue
        message_id = record.get("message_id")
        pack_id = record.get("pack_id") or Path(name).parent.name
        if not isinstance(message_id, str):
            executable.append(
                {
                    "path": name,
                    "message": record,
                    "mailbox_commit": add_commit,
                    "raw_message_sha256": raw_sha,
                }
            )
            continue
        request = record.get("qualification_request")
        job_id = request.get("job_id") if isinstance(request, dict) else None
        terminal = results_by_parent.get(message_id)
        if terminal is not None:
            terminal_type = terminal["message_type"]
            terminal_jobs[message_id] = {
                "state": "FAILED"
                if terminal_type == "TEST_FAIL_INFRASTRUCTURE"
                else "COMPLETED",
                "pack_id": pack_id,
                "job_id": job_id,
                "source": "COMMITTED_MAILBOX_RESULT",
                "intake_path": name,
                "intake_commit": add_commit,
                "intake_raw_sha256": raw_sha,
                "result_message_id": terminal["message_id"],
                "result_path": terminal["path"],
                "result_commit": terminal["add_commit"],
                "result_raw_sha256": terminal["raw_sha256"],
            }
            if isinstance(job_id, str):
                prior = observed_job_ids.get(job_id)
                if prior is not None and prior != message_id:
                    raise ValidationError(f"conflicting terminal tester job id: {job_id}")
                observed_job_ids[job_id] = message_id
            continue
        executable.append(
            {
                "path": name,
                "message": record,
                "mailbox_commit": add_commit,
                "raw_message_sha256": raw_sha,
            }
        )
    return {
        "mailbox_head": head,
        "executable": executable,
        "compatibility_dispositions": dispositions,
        "pack_local_invalid": pack_local_invalid,
        "terminal_jobs": terminal_jobs,
    }


def committed_messages(
    config: dict[str, Any],
) -> tuple[str, list[tuple[str, dict[str, Any]]]]:
    snapshot = committed_mailbox_snapshot(config)
    return snapshot["mailbox_head"], [
        (value["path"], value["message"]) for value in snapshot["executable"]
    ]


def validate_intake(config: dict[str, Any], message: dict[str, Any]) -> dict[str, Any]:
    if set(message) != MESSAGE_FIELDS:
        raise ValidationError("tester intake fields mismatch")
    if (
        message["schema_version"] != "1.0.0"
        or message["message_type"] != "TESTER_INTAKE"
        or message["recipient_role"] != "PERSISTENT_TESTER"
    ):
        raise ValidationError("tester intake envelope rejected")
    request = message["qualification_request"]
    validate_request(request, expected_role="T1")
    if request["job_type"] != "BDS_QUALIFICATION":
        raise ValidationError("local tester accepts BDS qualification only")
    if request["campaign_id"] != message["pack_id"]:
        raise ValidationError("intake pack/request mismatch")
    if request["bds"]["image_digest"] not in config["allowed_tester_images"]:
        raise ValidationError("tester image not allowlisted")
    if "candidate_profile" not in request["bds"]:
        raise ValidationError("tester intake requires candidate profile")
    hashes = message["exact_artifact_hashes"]
    sources = message["artifact_sources"]
    if set(hashes) != set(ARTIFACT_ROLES) or set(sources) != set(ARTIFACT_ROLES):
        raise ValidationError("artifact roles mismatch")
    for role in ARTIFACT_ROLES:
        if hashes[role] != request["bds"][f"{role}_sha256"]:
            raise ValidationError("intake/request artifact hash mismatch")
    repository = Path(request["bds"]["candidate_repository"]).resolve()
    roots = [Path(value) for value in config["allowed_candidate_roots"]]
    if not within(repository, roots):
        raise ValidationError("candidate repository outside allowlisted roots")
    if git_text(repository, "rev-parse", "--is-inside-work-tree") != "true":
        raise ValidationError("candidate repository unavailable")
    for role in ARTIFACT_ROLES:
        source = sources[role]
        if set(source) != {"authority_commit", "git_path"}:
            raise ValidationError("artifact source fields mismatch")
        if source["authority_commit"] not in {
            request["bds"]["content_commit"],
            request["bds"]["metadata_commit"],
        }:
            raise ValidationError("artifact source commit not candidate-bound")
        validate_safe_relative_path(source["git_path"])
    for commit_field, tree_field in (
        ("content_commit", "content_tree"),
        ("metadata_commit", "metadata_tree"),
    ):
        observed = git_text(
            repository, "rev-parse", f"{request['bds'][commit_field]}^{{tree}}"
        )
        if observed != request["bds"][tree_field]:
            raise ValidationError("candidate commit/tree mismatch")
    expected_key = sha256_bytes(
        canonical_bytes(
            {
                "message_id": message["message_id"],
                "pack_id": message["pack_id"],
                "candidate_generation": message["candidate_generation"],
                "request_payload_sha256": request["request_payload_sha256"],
            }
        )
    )
    if message["idempotency_key"] != expected_key:
        raise ValidationError("tester intake idempotency mismatch")
    return request


def stage_job(
    config: dict[str, Any],
    mailbox_head: str,
    mailbox_path: str,
    message: dict[str, Any],
) -> Path:
    request = validate_intake(config, message)
    runtime = Path(config["runtime_root"]).resolve()
    job_root = runtime / "jobs" / request["job_id"]
    if job_root.exists():
        raise ValidationError("duplicate local tester job")
    (job_root / "inputs").mkdir(parents=True, mode=0o700)
    (job_root / "artifacts").mkdir(mode=0o700)
    (job_root / "logs").mkdir(mode=0o700)
    repository = Path(request["bds"]["candidate_repository"]).resolve()
    entries = []
    for role in ARTIFACT_ROLES:
        source = message["artifact_sources"][role]
        git_path = str(validate_safe_relative_path(source["git_path"]))
        data = git_bytes(repository, f"{source['authority_commit']}:{git_path}")
        relative = request["bds"][f"{role}_path"]
        destination = job_root / "inputs" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        os.chmod(destination, 0o400)
        expected_hash = request["bds"][f"{role}_sha256"]
        expected_size = request["bds"][f"{role}_size"]
        if sha256_file(destination) != expected_hash or destination.stat().st_size != expected_size:
            raise ValidationError("committed artifact authority mismatch")
        entries.append(
            {
                "relative_path": relative,
                "sha256": expected_hash,
                "size_bytes": expected_size,
                "content_role": role.upper(),
            }
        )
    write_json(job_root / "request.json", request)
    (job_root / "request.sha256").write_text(
        sha256_file(job_root / "request.json") + "\n"
    )
    manifest = {
        "schema_version": "crazycraft-remote-v1",
        "job_id": request["job_id"],
        "entries": entries,
        "manifest_payload_sha256": "",
    }
    manifest["manifest_payload_sha256"] = payload_hash(
        manifest, "manifest_payload_sha256"
    )
    write_json(job_root / "input-manifest.json", manifest)
    write_json(
        job_root / "intake-binding.json",
        {
            "mailbox_commit": mailbox_head,
            "mailbox_path": mailbox_path,
            "message": message,
        },
    )
    return job_root


def select_dispatchable(
    messages: list[tuple[str, dict[str, Any]]],
    state: dict[str, Any],
    max_jobs: int = 2,
) -> list[tuple[str, dict[str, Any]]]:
    active = [
        value
        for value in state.get("jobs", {}).values()
        if value.get("state") == "DISPATCHED"
    ]
    slots = max(0, max_jobs - len(active))
    active_packs = {value["pack_id"] for value in active}
    consumed = set(state.get("jobs", {}))
    terminal_job_ids = {
        value.get("job_id")
        for value in state.get("jobs", {}).values()
        if value.get("state") in {"COMPLETED", "FAILED"}
        and isinstance(value.get("job_id"), str)
    }
    selected = []
    for path, message in messages:
        request = message.get("qualification_request", {})
        if (
            message["message_id"] in consumed
            or message["pack_id"] in active_packs
            or request.get("job_id") in terminal_job_ids
        ):
            continue
        selected.append((path, message))
        active_packs.add(message["pack_id"])
        if len(selected) == slots:
            break
    return selected


def result_message(job_root: Path) -> dict[str, Any]:
    binding = json.loads((job_root / "intake-binding.json").read_text())
    intake = binding["message"]
    request = intake["qualification_request"]
    result = json.loads((job_root / "result.json").read_text())
    if result.get("result_payload_sha256") and result["result_payload_sha256"] != payload_hash(
        result, "result_payload_sha256"
    ):
        raise ValidationError("qualification result payload hash mismatch")
    detailed_path = job_root / "artifacts" / "qualification-result.json"
    detailed = json.loads(detailed_path.read_text()) if detailed_path.is_file() else {}
    if detailed and detailed.get("result_payload_sha256") != payload_hash(
        detailed, "result_payload_sha256"
    ):
        raise ValidationError("detailed qualification result payload hash mismatch")
    classification = detailed.get("result_classification") or result.get(
        "result_classification"
    )
    if classification is None and result.get("failure_class") == "TEST_FAIL_INFRASTRUCTURE":
        classification = "TEST_FAIL_INFRASTRUCTURE"
    if classification not in RESULT_TYPES:
        raise ValidationError("unsupported tester result classification")
    for role in ARTIFACT_ROLES:
        path = job_root / "inputs" / request["bds"][f"{role}_path"]
        if (
            sha256_file(path) != request["bds"][f"{role}_sha256"]
            or path.stat().st_size != request["bds"][f"{role}_size"]
        ):
            raise ValidationError("candidate changed during qualification")
    receipt = {
        "schema_version": "crazycraft-local-tester-v1",
        "job_id": request["job_id"],
        "tester_image": request["bds"]["image_digest"],
        "request_sha256": sha256_file(job_root / "request.json"),
        "result_sha256": sha256_file(job_root / "result.json"),
        "artifact_outputs": [],
        "candidate_unchanged": True,
        "cleanup": "CONTAINER_REMOVED_BY_FIXED_RUNNER",
        "receipt_payload_sha256": "",
    }
    for path in sorted((job_root / "artifacts").rglob("*")):
        if path.is_file():
            receipt["artifact_outputs"].append(
                {
                    "path": path.relative_to(job_root).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    receipt["receipt_payload_sha256"] = payload_hash(
        receipt, "receipt_payload_sha256"
    )
    write_json(job_root / "service-receipt.json", receipt)
    findings = [
        {
            "finding_id": value,
            "abstract_defect": "Exact-package qualification gate failed.",
        }
        for value in result.get("opaque_finding_ids", [])
    ]
    message_id = (
        "MSG-TESTER-"
        + request["job_id"].removeprefix("JOB-")
        + "-"
        + classification.replace("TEST_", "")
    )
    message = {
        "schema_version": "1.0.0",
        "message_id": message_id,
        "message_type": classification,
        "pack_id": intake["pack_id"],
        "sender_role": "PERSISTENT_TESTER",
        "recipient_role": "T1_PORTFOLIO_SUPERVISOR",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_authority_commit": request["bds"]["content_commit"],
        "source_authority_tree": request["bds"]["content_tree"],
        "candidate_generation": intake["candidate_generation"],
        "exact_artifact_hashes": intake["exact_artifact_hashes"],
        "parent_message_id": intake["message_id"],
        "required_action": "REGISTER_TEST_PASS"
        if classification == "TEST_PASS"
        else "ROUTE_BOUNDED_PRODUCT_REPAIR"
        if classification == "TEST_FAIL_PRODUCT"
        else "REPAIR_TEST_INFRASTRUCTURE_WITHOUT_PRODUCT_MUTATION",
        "idempotency_key": sha256_bytes(
            canonical_bytes(
                {
                    "parent": intake["message_id"],
                    "job_id": request["job_id"],
                    "result": classification,
                    "receipt": receipt["receipt_payload_sha256"],
                }
            )
        ),
        "proof_boundary": [
            result.get("proof_boundary", "EXACT_PACKAGE_QUALIFICATION_ONLY"),
            *[
                f"{gate}_NOT_RUN"
                for gate in result.get("external_gates_not_run", [])
            ],
        ],
        "result": classification,
        "candidate_hash": request["bds"]["mcaddon_sha256"],
        "findings": findings,
        "qualification_receipts": [
            {
                "job_id": request["job_id"],
                "service_receipt_sha256": sha256_file(
                    job_root / "service-receipt.json"
                ),
                "qualifier_receipt_sha256": next(
                    (
                        value["sha256"]
                        for value in receipt["artifact_outputs"]
                        if value["path"].endswith("qualifier-receipt.json")
                    ),
                    None,
                ),
            }
        ],
    }
    return message


def publish_result(config: dict[str, Any], job_root: Path) -> tuple[str, str]:
    mailbox = Path(config["mailbox_repository"]).resolve()
    message = result_message(job_root)
    binding = json.loads((job_root / "intake-binding.json").read_text())
    target = (
        mailbox
        / "tester_results"
        / message["pack_id"]
        / f"{message['message_id']}.json"
    )
    lock_path = Path(git_text(mailbox, "rev-parse", "--git-dir")) / "tester-publish.lock"
    if not lock_path.is_absolute():
        lock_path = mailbox / lock_path
    expected = target.relative_to(mailbox).as_posix()
    expected_bytes = canonical_bytes(message) + b"\n"
    last_dirty = ""
    for attempt in range(PUBLICATION_RETRY_ATTEMPTS):
        with lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current_head = git_text(mailbox, "rev-parse", "HEAD")
            authority_head = git_text(mailbox, "rev-parse", config["mailbox_ref"])
            if current_head != authority_head:
                raise ValidationError("mailbox checkout is not the authority ref")
            run(
                [
                    "/usr/bin/git",
                    "-C",
                    str(mailbox),
                    "merge-base",
                    "--is-ancestor",
                    binding["mailbox_commit"],
                    current_head,
                ]
            )

            # Publication is idempotent across a crash after commit but before
            # status.json. A byte-identical committed result is the same event.
            committed_names = git_text(
                mailbox, "ls-tree", "-r", "--name-only", current_head, "--", expected
            ).splitlines()
            if committed_names:
                committed = git_bytes(mailbox, f"{current_head}:{expected}")
                committed_record = json.loads(committed)
                if isinstance(committed_record.get("created_at"), str):
                    message["created_at"] = committed_record["created_at"]
                    expected_bytes = canonical_bytes(message) + b"\n"
                if committed != expected_bytes:
                    raise ValidationError("append-only tester result conflicts")
                commit = git_text(
                    mailbox, "log", "-1", "--format=%H", "--", expected
                )
                tree = git_text(mailbox, "rev-parse", f"{commit}^{{tree}}")
                return commit, tree

            dirty = git_text(mailbox, "status", "--porcelain")
            if dirty:
                last_dirty = dirty
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                write_json(target, message)
                run(["/usr/bin/git", "-C", str(mailbox), "add", "--", str(target)])
                staged = git_text(mailbox, "diff", "--cached", "--name-only")
                if staged != expected:
                    target.unlink(missing_ok=True)
                    run(
                        [
                            "/usr/bin/git",
                            "-C",
                            str(mailbox),
                            "reset",
                            "-q",
                            "--",
                            expected,
                        ]
                    )
                    raise ValidationError("mailbox publication scope mismatch")
                run(
                    [
                        "/usr/bin/git",
                        "-C",
                        str(mailbox),
                        "commit",
                        "-m",
                        f"test: publish {message['pack_id']} {message['result']}",
                    ]
                )
                commit = git_text(mailbox, "rev-parse", "HEAD")
                tree = git_text(mailbox, "rev-parse", "HEAD^{tree}")
                return commit, tree
        if attempt + 1 < PUBLICATION_RETRY_ATTEMPTS:
            time.sleep(PUBLICATION_RETRY_DELAY_SECONDS)
    raise ValidationError(
        "mailbox worktree remained dirty during bounded publication retry: "
        + last_dirty[-500:]
    )


def execute_one(config: dict[str, Any], job_root: Path) -> int:
    from remote_job_entrypoint import _execute_bds_live

    request = json.loads((job_root / "request.json").read_text())
    validate_request(request, expected_role="T1")
    try:
        result, report, _, containers = _execute_bds_live(request, job_root)
        write_json(job_root / "result.json", result)
        (job_root / "report.md").write_text(report)
        state = "COMPLETED"
        exit_code = 0
    except Exception as exc:
        write_json(
            job_root / "result.json",
            {
                "schema_version": "crazycraft-local-tester-v1",
                "job_id": request["job_id"],
                "failure_class": "TEST_FAIL_INFRASTRUCTURE",
                "error_class": type(exc).__name__,
                "error": str(exc),
            },
        )
        containers = []
        state = "FAILED"
        exit_code = 1
    commit, tree = publish_result(config, job_root)
    write_json(
        job_root / "status.json",
        {
            "state": state,
            "job_id": request["job_id"],
            "container_ids": containers,
            "mailbox_result_commit": commit,
            "mailbox_result_tree": tree,
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    )
    return exit_code


def reconcile(
    state: dict[str, Any], config: dict[str, Any] | None = None
) -> None:
    for job in state.get("jobs", {}).values():
        # Terminal jobs reconstructed from immutable mailbox results have no
        # local execution directory.  Their committed result is the terminal
        # authority, so local process reconciliation must never reinterpret
        # them as recoverable/failed worker processes.
        if job.get("source") == "COMMITTED_MAILBOX_RESULT":
            if job.get("state") not in {"COMPLETED", "FAILED"}:
                raise ValidationError(
                    "committed mailbox result has nonterminal tester state"
                )
            continue
        if job.get("state") not in {"DISPATCHED", "FAILED"}:
            continue
        job_root = Path(job["job_root"])
        status = job_root / "status.json"
        if status.is_file():
            terminal_state = json.loads(status.read_text()).get("state")
            if terminal_state not in {"COMPLETED", "FAILED"}:
                terminal_state = "FAILED"
            job["state"] = terminal_state
            try:
                os.waitpid(job["pid"], os.WNOHANG)
            except (ChildProcessError, ProcessLookupError, TypeError):
                pass
            continue
        completed_outputs = all(
            (job_root / name).is_file()
            for name in ("result.json", "service-receipt.json", "intake-binding.json")
        )
        if completed_outputs and config is not None:
            try:
                result = result_message(job_root)
                commit, tree = publish_result(config, job_root)
                terminal_state = (
                    "FAILED"
                    if result["result"] == "TEST_FAIL_INFRASTRUCTURE"
                    else "COMPLETED"
                )
                write_json(
                    status,
                    {
                        "state": terminal_state,
                        "job_id": job["job_id"],
                        "container_ids": [],
                        "mailbox_result_commit": commit,
                        "mailbox_result_tree": tree,
                        "recovered_publication": True,
                        "finished_at": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                        ),
                    },
                )
                job["state"] = terminal_state
                job.pop("publication_error", None)
                continue
            except ValidationError as exc:
                # Preserve the completed execution for another publication
                # attempt. Do not rerun BDS and do not free the candidate slot.
                job["state"] = "DISPATCHED"
                job["publication_error"] = str(exc)
                continue
        try:
            os.kill(job["pid"], 0)
        except (ProcessLookupError, TypeError):
            job["state"] = "FAILED"


def dispatch(
    config_path: Path,
    config: dict[str, Any],
    mailbox_head: str,
    path: str,
    message: dict[str, Any],
    state: dict[str, Any],
) -> None:
    job_root = stage_job(config, mailbox_head, path, message)
    process = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--execute-one",
            "--config",
            str(config_path.resolve()),
            "--job-root",
            str(job_root),
        ],
        stdin=subprocess.DEVNULL,
        stdout=(job_root / "logs" / "worker.stdout").open("wb"),
        stderr=(job_root / "logs" / "worker.stderr").open("wb"),
        start_new_session=True,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
    )
    state.setdefault("jobs", {})[message["message_id"]] = {
        "state": "DISPATCHED",
        "pid": process.pid,
        "pack_id": message["pack_id"],
        "job_id": message["qualification_request"]["job_id"],
        "job_root": str(job_root),
    }


def rebuild_runtime_state(
    previous: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Merge ignored process observations with committed terminal authority."""

    state = deepcopy(previous)
    jobs = state.setdefault("jobs", {})
    for disposition in snapshot["compatibility_dispositions"]:
        jobs.pop(disposition["message_id"], None)
    for message_id, terminal in snapshot["terminal_jobs"].items():
        jobs[message_id] = deepcopy(terminal)
    state["intake_dispositions"] = {
        value["message_id"]: value
        for value in snapshot["compatibility_dispositions"]
    }
    existing_invalid = {
        value.get("rejection_key"): value
        for value in state.get("pack_local_rejections", [])
        if isinstance(value, dict) and isinstance(value.get("rejection_key"), str)
    }
    for value in snapshot["pack_local_invalid"]:
        existing_invalid[value["rejection_key"]] = value
    state["pack_local_rejections"] = [
        existing_invalid[key] for key in sorted(existing_invalid)
    ]
    return state


def record_pack_local_rejection(
    state: dict[str, Any],
    observation: dict[str, Any],
    error: ValidationError,
) -> None:
    record = {
        "rejection_key": compatibility_key(
            observation["mailbox_commit"],
            observation["path"],
            observation["raw_message_sha256"],
        ),
        "message_id": observation["message"].get("message_id"),
        "pack_id": observation["message"].get("pack_id")
        or Path(observation["path"]).parent.name,
        "path": observation["path"],
        "mailbox_commit": observation["mailbox_commit"],
        "raw_message_sha256": observation["raw_message_sha256"],
        "failure": str(error),
        "disposition": "PACK_LOCAL_REJECTION",
    }
    existing = {
        value.get("rejection_key"): value
        for value in state.get("pack_local_rejections", [])
        if isinstance(value, dict) and isinstance(value.get("rejection_key"), str)
    }
    existing[record["rejection_key"]] = record
    state["pack_local_rejections"] = [existing[key] for key in sorted(existing)]


def poll_once(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    runtime = Path(config["runtime_root"]).resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    state_path = runtime / "state.json"
    previous = json.loads(state_path.read_text()) if state_path.is_file() else {"jobs": {}}
    snapshot = committed_mailbox_snapshot(config)
    state = rebuild_runtime_state(previous, snapshot)
    reconcile(state, config)
    validated: list[tuple[str, dict[str, Any]]] = []
    rejected_keys = {
        value.get("rejection_key")
        for value in state.get("pack_local_rejections", [])
    }
    for observation in snapshot["executable"]:
        observation_key = compatibility_key(
            observation["mailbox_commit"],
            observation["path"],
            observation["raw_message_sha256"],
        )
        if observation_key in rejected_keys:
            continue
        try:
            validate_intake(config, observation["message"])
        except ValidationError as exc:
            record_pack_local_rejection(state, observation, exc)
            continue
        validated.append((observation["path"], observation["message"]))
    for path, message in select_dispatchable(
        validated, state, config["max_active_jobs"]
    ):
        dispatch(
            config_path,
            config,
            snapshot["mailbox_head"],
            path,
            message,
            state,
        )
    state["mailbox_head"] = snapshot["mailbox_head"]
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_json(state_path, state)
    return state


def serve(config_path: Path) -> int:
    config = load_config(config_path)
    runtime = Path(config["runtime_root"]).resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    with (runtime / "service.lock").open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValidationError("local tester already running") from exc
        stopping = False

        def stop(_signal: int, _frame: Any) -> None:
            nonlocal stopping
            stopping = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        while not stopping:
            poll_once(config_path)
            time.sleep(config["poll_seconds"])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--execute-one", action="store_true")
    parser.add_argument("--job-root", type=Path)
    args = parser.parse_args()
    if sum((args.run_once, args.serve, args.execute_one)) != 1:
        raise ValidationError("select exactly one fixed tester operation")
    config = load_config(args.config.resolve())
    if args.execute_one:
        if args.job_root is None:
            raise ValidationError("execute-one requires job root")
        return execute_one(config, args.job_root.resolve())
    if args.job_root is not None:
        raise ValidationError("job root valid only for execute-one")
    if args.run_once:
        poll_once(args.config.resolve())
        return 0
    return serve(args.config.resolve())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"LOCAL_TESTER_FAIL_CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
