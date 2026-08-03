"""Hash-bound platform qualification and standing campaign launch authority."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .identity import validate_identity


PLATFORM_SCHEMA = "bedrock-factory.platform-qualification.v1.0.0"
STANDING_AUTHORITY_SCHEMA = "bedrock-factory.standing-launch-authority.v1.0.0"
RESOLUTION_SCHEMA = "bedrock-factory.launch-resolution.v1.0.0"
REQUIRED_PLATFORM_COMPONENTS = {
    "launcher",
    "sandbox_profile",
    "codex_executable",
    "codex_startup_mode",
    "ephemeral_auth_bootstrap",
    "lane_local_home_policy",
    "working_directory_policy",
    "path_canonicalization_policy",
    "negative_access_probes",
    "privileged_broker",
    "docker_bds_adapter",
    "cleanup_validator",
    "process_receipt_validator",
}
REQUIRED_CANARY_STEPS = {
    "STANDING_AUTHORITY_VALIDATED",
    "EMPTY_LANE_INITIALIZED",
    "CODEX_STARTED",
    "REPOSITORY_CWD_PROVED",
    "LANE_LOCAL_HOME_AND_CACHE_PROVED",
    "ALLOWED_READS_PROVED",
    "DENIED_READS_PROVED",
    "PRIVILEGED_BROKER_OPERATION_PROVED",
    "WORKER_TERMINATED",
    "CLEANUP_VALIDATED",
    "PROCESS_RECEIPT_VALIDATED",
}
ROUTINE_ACTIVATION_TYPES = {
    "NEW_PACK",
    "CONTINUE_NONTERMINAL",
    "REPAIR_REQUIRED",
    "T2_ADAPTER_REPAIR",
    "RECOVERY_AFTER_INTERRUPTION",
}
NEW_AUTHORITY_TRIGGERS = {
    "RIGHTS_OR_SOURCE_CHANGE",
    "LAUNCHER_OR_SECURITY_MODEL_CHANGE",
    "AUTHENTICATED_IDENTITY",
    "REALMS",
    "RETAIL_CLIENT",
    "PHYSICAL_CONSOLE",
    "PUBLIC_DISTRIBUTION",
    "MARKETPLACE_OR_RELEASE",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PlatformAuthorityError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def document_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require(condition: bool, code: str, detail: str) -> None:
    if not condition:
        raise PlatformAuthorityError(code, detail)


def _sha(value: object, field: str) -> str:
    _require(isinstance(value, str) and bool(SHA256.fullmatch(value)), "INVALID_DOCUMENT", f"{field} must be SHA-256")
    return value


def validate_platform_qualification(receipt: dict[str, Any]) -> dict[str, Any]:
    _require(receipt.get("schema_version") == PLATFORM_SCHEMA, "PLATFORM_UNQUALIFIED", "platform schema rejected")
    _require(receipt.get("status") == "PASS", "PLATFORM_UNQUALIFIED", "platform receipt is not PASS")
    _require(isinstance(receipt.get("qualification_id"), str) and receipt["qualification_id"].startswith("FPQ-"), "INVALID_DOCUMENT", "qualification_id rejected")
    components = receipt.get("components")
    _require(isinstance(components, dict), "INVALID_DOCUMENT", "components must be an object")
    _require(set(components) == REQUIRED_PLATFORM_COMPONENTS, "PLATFORM_UNQUALIFIED", "platform component set changed")
    for name, digest in components.items():
        _sha(digest, f"components.{name}")
    steps = receipt.get("canary_steps")
    _require(isinstance(steps, dict) and set(steps) == REQUIRED_CANARY_STEPS, "PLATFORM_UNQUALIFIED", "platform canary step set changed")
    _require(all(value == "PASS" for value in steps.values()), "PLATFORM_UNQUALIFIED", "platform canary did not fully pass")
    _sha(receipt.get("process_receipt_sha256"), "process_receipt_sha256")
    _sha(receipt.get("cleanup_receipt_sha256"), "cleanup_receipt_sha256")
    integrity = _sha(receipt.get("canonical_payload_sha256"), "canonical_payload_sha256")
    normalized = dict(receipt)
    normalized.pop("canonical_payload_sha256", None)
    _require(integrity == document_sha256(normalized), "PLATFORM_HASH_MISMATCH", "platform receipt canonical hash mismatch")
    return receipt


def resolve_standing_launch_authority(
    authority: dict[str, Any],
    activation: dict[str, Any],
    platform_receipt: dict[str, Any],
) -> dict[str, Any]:
    try:
        validate_platform_qualification(platform_receipt)
        _require(authority.get("schema_version") == STANDING_AUTHORITY_SCHEMA, "AUTHORITY_INVALID", "standing authority schema rejected")
        _require(authority.get("state") == "ACTIVE", "AUTHORITY_INACTIVE", "standing authority is inactive")
        _require(authority.get("visibility") == "PRIVATE_FACTORY_ONLY", "NEW_AUTHORITY_REQUIRED", "standing authority is private-only")
        for field in ("campaign_id", "source_authority_sha256", "rights_authority_sha256", "security_model_sha256"):
            _require(activation.get(field) == authority.get(field), "AUTHORITY_HASH_MISMATCH", f"{field} changed")
        expected_platform = _sha(authority.get("platform_qualification_sha256"), "platform_qualification_sha256")
        _require(expected_platform == document_sha256(platform_receipt), "PLATFORM_HASH_MISMATCH", "activation platform receipt changed")
        activation_type = activation.get("activation_type")
        _require(activation_type in ROUTINE_ACTIVATION_TYPES, "NEW_AUTHORITY_REQUIRED", "activation type is outside routine authority")
        requested = set(activation.get("requested_new_authority_triggers", []))
        _require(requested.issubset(NEW_AUTHORITY_TRIGGERS), "INVALID_DOCUMENT", "unknown new-authority trigger")
        _require(not requested, "NEW_AUTHORITY_REQUIRED", f"new authority requested: {sorted(requested)}")
        validate_identity(activation.get("activation_id"), "activation")
        candidate_id = activation.get("candidate_id")
        if candidate_id is not None:
            validate_identity(candidate_id, "candidate")
        if activation_type in {"CONTINUE_NONTERMINAL", "RECOVERY_AFTER_INTERRUPTION"}:
            _require(activation.get("product_bytes_changed") is False, "CANDIDATE_IDENTITY_MISMATCH", "control-only activation cannot change product bytes")
        return {
            "schema_version": RESOLUTION_SCHEMA,
            "status": "PASS",
            "decision": "LAUNCH_ALLOWED_BY_STANDING_AUTHORITY",
            "authority_id": authority.get("authority_id"),
            "campaign_id": authority.get("campaign_id"),
            "activation_id": activation.get("activation_id"),
            "candidate_id": candidate_id,
            "platform_qualification_id": platform_receipt.get("qualification_id"),
            "new_authority_required": False,
        }
    except (PlatformAuthorityError, ValueError) as exc:
        code = exc.code if isinstance(exc, PlatformAuthorityError) else "IDENTITY_INVALID"
        return {
            "schema_version": RESOLUTION_SCHEMA,
            "status": "FAIL",
            "decision": "LAUNCH_DENIED",
            "error": {"code": code, "detail": str(exc)},
            "new_authority_required": code in {"NEW_AUTHORITY_REQUIRED", "AUTHORITY_HASH_MISMATCH", "PLATFORM_HASH_MISMATCH"},
        }
