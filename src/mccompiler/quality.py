from __future__ import annotations

from dataclasses import dataclass
from typing import Any


QUALITY_DIMENSIONS = (
    "gameplay_fidelity",
    "visual_fidelity",
    "audio_fidelity",
    "interaction_fidelity",
    "controller_usability",
    "multiplayer_fidelity",
    "persistence_fidelity",
    "performance",
    "stability",
    "discoverability",
    "feedback_clarity",
    "world_update_compatibility",
)

QUALITY_CLASSIFICATIONS = (
    "IMPROVED",
    "PARITY",
    "ACCEPTABLE_REDESIGN",
    "DEGRADED_WITH_APPROVAL",
    "MANUAL_REDESIGN_REQUIRED",
    "UNSUPPORTED",
)


@dataclass(frozen=True)
class QualityPolicy:
    gameplay_fidelity: float = 0.90
    interaction_fidelity: float = 0.90
    persistence_fidelity: float = 1.0
    multiplayer_fidelity: float = 1.0
    critical_behavior_omissions: int = 0
    silent_failures: int = 0
    crash_causing_script_errors: int = 0
    unbounded_tick_loops: int = 0


def validate_quality_record(record: dict[str, Any], policy: QualityPolicy | None = None) -> list[str]:
    policy = policy or QualityPolicy()
    errors: list[str] = []
    identifier = str(record.get("feature_id") or "<unknown>")
    classification = record.get("classification")
    if classification not in QUALITY_CLASSIFICATIONS:
        errors.append(f"{identifier}: invalid quality classification {classification!r}")
    dimensions = record.get("dimensions")
    if not isinstance(dimensions, dict):
        return errors + [f"{identifier}: quality dimensions are required"]
    for dimension in QUALITY_DIMENSIONS:
        value = dimensions.get(dimension)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
            errors.append(f"{identifier}: {dimension} must be a score from 0 to 1")
    evidence = record.get("evidence")
    if classification in {"IMPROVED", "PARITY"} and not evidence:
        errors.append(f"{identifier}: {classification} requires validation evidence")
    if classification == "DEGRADED_WITH_APPROVAL":
        approval = record.get("approval")
        if not isinstance(approval, dict) or not approval.get("actor") or not approval.get("reason"):
            errors.append(f"{identifier}: degraded quality requires explicit approval")
    losses = record.get("losses")
    if classification in {"ACCEPTABLE_REDESIGN", "DEGRADED_WITH_APPROVAL"} and not isinstance(losses, list):
        errors.append(f"{identifier}: redesign/degradation must list preserved and lost behavior")
    metrics = record.get("invariants") or {}
    supported = classification in {"IMPROVED", "PARITY", "ACCEPTABLE_REDESIGN", "DEGRADED_WITH_APPROVAL"}
    if supported:
        thresholds = {
            "gameplay_fidelity": policy.gameplay_fidelity,
            "interaction_fidelity": policy.interaction_fidelity,
            "persistence_fidelity": policy.persistence_fidelity,
            "multiplayer_fidelity": policy.multiplayer_fidelity,
        }
        for key, threshold in thresholds.items():
            if float(dimensions.get(key, 0)) < threshold and classification in {"IMPROVED", "PARITY"}:
                errors.append(f"{identifier}: {classification} does not meet {key} threshold {threshold}")
        maximums = {
            "critical_behavior_omissions": policy.critical_behavior_omissions,
            "silent_failures": policy.silent_failures,
            "crash_causing_script_errors": policy.crash_causing_script_errors,
            "unbounded_tick_loops": policy.unbounded_tick_loops,
        }
        for key, maximum in maximums.items():
            value = metrics.get(key)
            if not isinstance(value, int):
                errors.append(f"{identifier}: invariant {key} is required")
            elif value > maximum:
                errors.append(f"{identifier}: invariant {key} exceeds {maximum}")
    return errors

