"""Throughput and assurance metrics derived only from canonical events."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def compute_metrics(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(events)
    types = Counter(row["event_type"] for row in rows)
    queue_started: dict[str, float] = {}
    run_started: dict[str, float] = {}
    queue_ages: dict[str, list[float]] = defaultdict(list)
    service_times: dict[str, list[float]] = defaultdict(list)
    defect_stages: Counter[str] = Counter()
    accepted_at: dict[tuple[str, str], float] = {}
    integration_lag: list[float] = []
    for row in rows:
        payload = row.get("payload", {})
        run = row.get("gate_run_id")
        gate = str(payload.get("gate", "UNKNOWN"))
        if row["event_type"] == "GATE_QUEUED" and run:
            queue_started[run] = row["created_at"]
        elif row["event_type"] == "GATE_RUN_STARTED" and run:
            run_started[run] = row["created_at"]
            if run in queue_started:
                queue_ages[gate].append(row["created_at"] - queue_started[run])
        elif row["event_type"] == "GATE_RUN_FINISHED" and run and run in run_started:
            service_times[gate].append(row["created_at"] - run_started[run])
        if row["event_type"] == "DEFECT_FOUND":
            defect_stages[str(payload.get("stage", "UNKNOWN"))] += 1
        key = (row["campaign_id"], row["workload_id"])
        if row["event_type"] == "SLICE_ACCEPTED":
            accepted_at[key] = row["created_at"]
        elif row["event_type"] == "INTEGRATION_STARTED" and key in accepted_at:
            integration_lag.append(row["created_at"] - accepted_at[key])
    activations = types["ACTIVATION_STARTED"]
    candidates = types["CANDIDATE_PUBLISHED"]
    product_changes = sum(
        1 for row in rows
        if row["event_type"] == "ACTIVATION_FINISHED" and row.get("payload", {}).get("product_bytes_changed") is True
    )
    repeated = sum(
        1 for row in rows
        if row["event_type"] == "GATE_RUN_FINISHED" and row.get("payload", {}).get("reused_or_repeated_unchanged") is True
    )
    return {
        "activation_amplification": _ratio(activations, candidates),
        "candidate_first_pass_yield": _ratio(types["CANDIDATE_T1_FIRST_PASS"], candidates),
        "bds_first_pass_yield": _ratio(types["BDS_SMOKE_FIRST_PASS"], candidates),
        "infrastructure_blocked_share": _ratio(types["INFRASTRUCTURE_BLOCKED"], activations),
        "product_byte_change_rate": _ratio(product_changes, types["ACTIVATION_FINISHED"]),
        "repeated_evidence_rate": _ratio(repeated, types["GATE_RUN_FINISHED"]),
        "queue_age_by_gate_seconds": {gate: round(sum(values) / len(values), 6) for gate, values in sorted(queue_ages.items())},
        "gate_service_time_seconds": {gate: round(sum(values) / len(values), 6) for gate, values in sorted(service_times.items())},
        "accepted_slice_integration_lag_seconds": round(sum(integration_lag) / len(integration_lag), 6) if integration_lag else None,
        "defect_escape_stage": dict(sorted(defect_stages.items())),
        "projection_replay_integrity_target": 1.0,
        "event_count": len(rows),
    }
