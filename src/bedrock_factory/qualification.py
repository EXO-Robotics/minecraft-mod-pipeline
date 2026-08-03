"""Two-milestone validation planning and exact evidence reuse.

Broad validation is intentionally legal at only two reconstruction points:
immediately before the first BDS run and immediately before the mod is marked
complete.  Everything else is a cheap control-plane invariant, runtime work,
or ordinary implementation work.
"""

from __future__ import annotations

from typing import Any


PRE_BDS_MILESTONE = "PRE_BDS_MILESTONE"
FINAL_MOD_MILESTONE = "FINAL_MOD_MILESTONE"
VALIDATION_MILESTONES = (
    PRE_BDS_MILESTONE,
    FINAL_MOD_MILESTONE,
)
ALWAYS_ON_INVARIANTS = (
    "identity_syntax",
    "referenced_hash_equality",
    "path_containment",
    "append_only_sequence",
    "lease_and_owner_binding",
)
MILESTONE_BINDINGS = {
    PRE_BDS_MILESTONE: (
        "candidate_sha256",
        "pre_bds_validator_sha256",
        "configuration_sha256",
        "package_authority_sha256",
    ),
    FINAL_MOD_MILESTONE: (
        "candidate_sha256",
        "final_validator_sha256",
        "configuration_sha256",
        "bds_receipt_sha256",
        "observation_authority_sha256",
        "audit_authority_sha256",
        "integration_authority_sha256",
    ),
}


def validation_plan() -> list[str]:
    return list(VALIDATION_MILESTONES)


def may_reuse_milestone_evidence(
    previous: dict[str, Any],
    requested: dict[str, Any],
    *,
    milestone: str,
) -> bool:
    bindings = MILESTONE_BINDINGS.get(milestone)
    if bindings is None:
        raise ValueError(f"unknown validation milestone: {milestone}")
    return (
        previous.get("status") == "PASS"
        and previous.get("milestone") == milestone
        and requested.get("milestone") == milestone
        and all(previous.get(field) == requested.get(field) for field in bindings)
    )


def next_validation_milestone(completed: dict[str, str]) -> str | None:
    for milestone in VALIDATION_MILESTONES:
        status = completed.get(milestone)
        if status == "FAIL":
            return None
        if status != "PASS":
            return milestone
    return None
