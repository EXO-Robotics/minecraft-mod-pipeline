from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ACTIVATION_TYPES = {
    "NEW_PACK",
    "CONTINUE_NONTERMINAL",
    "REPAIR_REQUIRED",
    "T2_ADAPTER_REPAIR",
    "RECOVERY_AFTER_INTERRUPTION",
}
LANES = {"EVIDENCE", "CONTROL", "PRODUCTION", "INTEGRATION", "AUDIT", "QUALIFICATION"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
STOP_CODES = {
    "AUTHORITY_MISSING",
    "AUTHORITY_HASH_MISMATCH",
    "AUTHORITY_CONFLICT",
    "AUTHORITY_SUPERSEDED",
    "REPOSITORY_IDENTITY_MISMATCH",
    "WRITER_LEASE_CONFLICT",
    "SANITIZED_CONTRACT_MISSING",
    "REQUIRED_LOCAL_TOOLCHAIN_UNAVAILABLE",
    "CLEANROOM_BOUNDARY_VIOLATION",
    "STABLE_API_IMPOSSIBLE",
    "PUBLICATION_INTEGRITY_FAILURE",
    "RECOVERY_STATE_AMBIGUOUS",
    "SHARED_RUNTIME_AUTHORITY_MISSING",
}


class ActivationError(ValueError):
    pass


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def activation_digest(value: dict[str, Any]) -> str:
    normalized = json.loads(json.dumps(value))
    integrity = normalized.get("integrity")
    if isinstance(integrity, dict):
        integrity.pop("canonical_payload_sha256", None)
    return hashlib.sha256(canonical_bytes(normalized)).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ActivationError(message)


def _absolute_path(value: object, field: str) -> Path:
    _require(isinstance(value, str) and bool(value), f"{field} must be a non-empty path")
    path = Path(value).expanduser()
    _require(path.is_absolute(), f"{field} must be absolute")
    return path


def _sha(value: object, field: str) -> str:
    _require(isinstance(value, str) and bool(SHA256.fullmatch(value)), f"{field} must be SHA-256")
    return value


def validate_activation_package(
    activation: dict[str, Any],
    *,
    verify_files: bool = False,
) -> None:
    required = {
        "schema_version",
        "activation_id",
        "activation_type",
        "state",
        "pack",
        "repository",
        "authority",
        "generation",
        "action",
        "validation",
        "publication",
        "block_policy",
        "recovery",
        "integrity",
    }
    missing = sorted(required - activation.keys())
    _require(not missing, f"activation missing fields: {missing}")
    _require(
        activation["schema_version"] == "crazycraft.worker-activation-package.v1.0.0",
        "activation schema version rejected",
    )
    _require(activation["activation_type"] in ACTIVATION_TYPES, "activation type rejected")
    _require(activation["state"] in {"AUTHORIZED", "SUPERSEDED", "COMPLETED", "BLOCKED"}, "activation state rejected")

    pack = activation["pack"]
    _require(isinstance(pack, dict), "pack must be an object")
    for field in ("pack_id", "assignment_id", "worker_role", "lane"):
        _require(isinstance(pack.get(field), str) and pack[field], f"pack.{field} is required")
    _require(pack["lane"] in LANES, "pack.lane rejected")

    repository = activation["repository"]
    _require(isinstance(repository, dict), "repository must be an object")
    repo_path = _absolute_path(repository.get("path"), "repository.path")
    _require(isinstance(repository.get("ref"), str) and repository["ref"].startswith("refs/heads/"), "repository.ref rejected")
    writes = repository.get("exclusive_write_roots")
    _require(isinstance(writes, list) and writes, "repository.exclusive_write_roots is required")
    for index, root in enumerate(writes):
        write_path = _absolute_path(root, f"repository.exclusive_write_roots[{index}]")
        _require(write_path == repo_path or repo_path in write_path.parents, "write root escapes repository")

    authority = activation["authority"]
    _require(isinstance(authority, dict), "authority must be an object")
    for name in ("assignment", "activation_message"):
        record = authority.get(name)
        _require(isinstance(record, dict), f"authority.{name} is required")
        path = _absolute_path(record.get("path"), f"authority.{name}.path")
        expected = _sha(record.get("sha256"), f"authority.{name}.sha256")
        if verify_files:
            _require(path.is_file(), f"authority file missing: {path}")
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
            _require(observed == expected, f"authority hash mismatch: {path}")
    precedence = authority.get("precedence")
    _require(isinstance(precedence, list) and precedence, "authority.precedence is required")
    _require(len(precedence) == len(set(precedence)), "authority.precedence contains duplicates")

    generation = activation["generation"]
    _require(isinstance(generation, dict), "generation must be an object")
    current = generation.get("current")
    next_generation = generation.get("next")
    _require(isinstance(current, int) and current >= 0, "generation.current rejected")
    _require(isinstance(next_generation, int) and next_generation >= 1, "generation.next rejected")
    kind = activation["activation_type"]
    if kind == "NEW_PACK":
        _require(current == 0 and next_generation == 1, "NEW_PACK must begin at generation 1")
    elif kind == "REPAIR_REQUIRED":
        rejected = generation.get("rejected")
        _require(isinstance(rejected, int) and rejected == current, "repair must bind one rejected current generation")
        _require(next_generation == rejected + 1, "repair replacement must be rejected generation + 1")
        _require(generation.get("publication_authorized") is True, "repair publication must be explicit")
    elif kind == "T2_ADAPTER_REPAIR":
        _require(generation.get("publication_authorized") is False, "T2 adapter repair cannot publish a candidate")
    else:
        _require(next_generation in {current, current + 1}, "continuation generation is invalid")

    action = activation["action"]
    _require(isinstance(action, dict), "action must be an object")
    _require(isinstance(action.get("code"), str) and action["code"], "action.code is required")
    maximum = action.get("maximum_new_candidates")
    _require(isinstance(maximum, int) and 0 <= maximum <= 1, "maximum_new_candidates must be 0 or 1")
    completion = action.get("completion")
    _require(isinstance(completion, dict) and isinstance(completion.get("code"), str), "structured action completion is required")

    validation = activation["validation"]
    _require(isinstance(validation, dict), "validation must be an object")
    commands = validation.get("local_commands")
    _require(isinstance(commands, list), "validation.local_commands must be an array")
    for index, command in enumerate(commands):
        _require(isinstance(command, dict), f"local command {index} must be an object")
        argv = command.get("argv")
        _require(
            isinstance(argv, list) and argv and all(isinstance(part, str) and part for part in argv),
            f"local command {index} requires argv",
        )
        _absolute_path(command.get("cwd"), f"validation.local_commands[{index}].cwd")
    delegations = validation.get("downstream_delegations")
    _require(isinstance(delegations, list), "downstream_delegations must be an array")
    for delegation in delegations:
        _require(
            isinstance(delegation, dict)
            and delegation.get("required_before_publication") is False,
            "downstream PASS cannot be a candidate-publication prerequisite",
        )

    block_policy = activation["block_policy"]
    _require(isinstance(block_policy, dict), "block_policy must be an object")
    allowed_codes = block_policy.get("allowed_codes")
    _require(isinstance(allowed_codes, list) and allowed_codes, "block_policy.allowed_codes is required")
    _require(set(allowed_codes).issubset(STOP_CODES), "block policy contains an unknown stop code")

    integrity = activation["integrity"]
    _require(isinstance(integrity, dict), "integrity must be an object")
    expected_digest = _sha(integrity.get("canonical_payload_sha256"), "integrity.canonical_payload_sha256")
    _require(expected_digest == activation_digest(activation), "activation canonical hash mismatch")


def load_activation_package(path: str | Path, *, verify_files: bool = True) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    document = json.loads(source.read_text(encoding="utf-8"))
    _require(isinstance(document, dict), "activation package must be a JSON object")
    validate_activation_package(document, verify_files=verify_files)
    return document
