"""Generic product, diagnostic, control-only, integration, and oracle policy."""

from __future__ import annotations

from typing import Any

from .identity import CANDIDATE_DISPOSITIONS, CONTROL_ONLY_DISPOSITIONS, validate_identity


FAILURE_CLASSES = {
    "PRODUCT_DEFECT",
    "DIAGNOSTIC_BEHAVIOR_FAILURE",
    "INFRASTRUCTURE_BLOCKED",
    "MISSING_EVIDENCE",
    "CLIENT_REQUIRED",
}


class LifecyclePolicyError(ValueError):
    pass


def adjudicate_candidate_outcome(
    *,
    disposition: str,
    failure_class: str,
    candidate_id: str | None,
    predecessor_candidate_id: str | None = None,
    product_bytes_changed: bool,
) -> dict[str, Any]:
    if failure_class not in FAILURE_CLASSES:
        raise LifecyclePolicyError(f"unknown failure class: {failure_class}")
    if candidate_id is not None:
        validate_identity(candidate_id, "candidate")
    if predecessor_candidate_id is not None:
        validate_identity(predecessor_candidate_id, "candidate")
    if disposition in CONTROL_ONLY_DISPOSITIONS:
        if product_bytes_changed:
            raise LifecyclePolicyError("control-only disposition cannot change product bytes")
        return {
            "rejected_candidates": [],
            "predecessor_preserved": True,
            "automatic_next_candidate": False,
            "rerun_scope": ["HOST_BINDING", "PROCESS_RECEIPT"],
            "product_defect": False,
        }
    if disposition not in CANDIDATE_DISPOSITIONS:
        raise LifecyclePolicyError(f"unknown candidate disposition: {disposition}")
    if candidate_id is None:
        raise LifecyclePolicyError("candidate disposition requires candidate identity")
    if failure_class in {"INFRASTRUCTURE_BLOCKED", "MISSING_EVIDENCE", "CLIENT_REQUIRED"}:
        return {
            "rejected_candidates": [],
            "predecessor_preserved": True,
            "automatic_next_candidate": False,
            "rerun_scope": [],
            "product_defect": False,
        }
    if disposition == "EVIDENCE_ENABLING_REPLACEMENT" and failure_class == "DIAGNOSTIC_BEHAVIOR_FAILURE":
        return {
            "rejected_candidates": [candidate_id],
            "predecessor_preserved": True,
            "automatic_next_candidate": False,
            "rerun_scope": [],
            "product_defect": True,
        }
    if failure_class == "PRODUCT_DEFECT":
        return {
            "rejected_candidates": [candidate_id],
            "predecessor_preserved": predecessor_candidate_id is not None,
            "automatic_next_candidate": False,
            "rerun_scope": ["AFFECTED_GATES_AFTER_EXPLICIT_REPAIR_AUTHORITY"],
            "product_defect": True,
        }
    raise LifecyclePolicyError("failure class is incompatible with candidate disposition")


def integration_train_due(
    *,
    accepted_since_last_train: int,
    shared_runtime_interface_changed: bool,
    slice_threshold: int = 3,
) -> bool:
    if slice_threshold < 2:
        raise LifecyclePolicyError("integration slice threshold must be at least two")
    return shared_runtime_interface_changed or accepted_since_last_train >= slice_threshold


def full_oracle_authority_reusable(
    authority: dict[str, Any],
    *,
    source_sha256: str,
    oracle_implementation_sha256: str,
    comparison_rules_sha256: str,
) -> bool:
    return authority.get("status") == "PASS" and all(
        authority.get(field) == expected
        for field, expected in (
            ("source_sha256", source_sha256),
            ("oracle_implementation_sha256", oracle_implementation_sha256),
            ("comparison_rules_sha256", comparison_rules_sha256),
        )
    )


ASSURANCE_PROFILES = {
    "LIGHTWEIGHT": (
        "FROZEN_WORK_ORDER",
        "IMPLEMENTATION",
        "LOCAL_TESTS",
        "REVIEW",
        "MERGE",
    ),
    "STANDARD_PRODUCT": (
        "FROZEN_REQUIREMENTS",
        "IMMUTABLE_CANDIDATE",
        "CI_STATIC_ADMISSION",
        "RUNTIME_TEST",
        "INDEPENDENT_EVALUATION",
        "STAGED_INTEGRATION_RELEASE",
    ),
    "HIGH_ASSURANCE": (
        "SOURCE_EVIDENCE_ISOLATION",
        "SANITIZED_CONTRACT",
        "LEAST_AUTHORITY_PRODUCER",
        "IMMUTABLE_CANDIDATE",
        "INDEPENDENT_MECHANICAL_RUNTIME_SEMANTIC_GATES",
        "HIDDEN_EVALUATION",
        "EXPLICIT_INTEGRATION",
        "PHYSICAL_HUMAN_RELEASE_AUTHORITY",
    ),
}


def assurance_profile(name: str) -> tuple[str, ...]:
    try:
        return ASSURANCE_PROFILES[name]
    except KeyError as exc:
        raise LifecyclePolicyError(f"unknown assurance profile: {name}") from exc
