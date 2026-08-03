"""Queue-aware staged qualification planning and exact evidence reuse."""

from __future__ import annotations

from typing import Any


QUALIFICATION_FUNNEL = (
    "PRODUCER_T1_SHADOW",
    "INDEPENDENT_T1",
    "BDS_ENTRYPOINT_SMOKE",
    "STABLE_RESTART_PERSISTENCE",
    "PREVIEW_WHEN_REQUIRED",
    "CALIBRATED_OBSERVATION",
    "T10_COMPONENT_AUDITS",
    "T10_FINAL_ADJUDICATION",
)
REUSE_BINDINGS = (
    "candidate_sha256",
    "gate_implementation_sha256",
    "runtime_image_sha256",
    "configuration_sha256",
    "probe_authority_sha256",
)


def qualification_plan(*, preview_required: bool) -> list[str]:
    return [stage for stage in QUALIFICATION_FUNNEL if preview_required or stage != "PREVIEW_WHEN_REQUIRED"]


def may_reuse_gate_evidence(previous: dict[str, Any], requested: dict[str, Any]) -> bool:
    return previous.get("status") == "PASS" and all(
        previous.get(field) == requested.get(field) for field in REUSE_BINDINGS
    )


def next_qualification_stage(completed: dict[str, str], *, preview_required: bool) -> str | None:
    for stage in qualification_plan(preview_required=preview_required):
        status = completed.get(stage)
        if status == "FAIL":
            return None
        if status != "PASS":
            return stage
    return None
