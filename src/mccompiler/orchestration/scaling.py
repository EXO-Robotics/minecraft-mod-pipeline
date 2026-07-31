from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


ACTIONABLE_STATUSES = {"READY"}
RUNNING_STATUS = "RUNNING"

LANE_TO_POOL = {
    "EVIDENCE": "task_maker",
    "CONTROL": "task_maker",
    "PRODUCTION": "production_workers",
    "INTEGRATION": "integration_worker",
    "AUDIT": "audit_workers",
    "QUALIFICATION": "tester_workers",
}

DEFAULT_MAX_THREADS = {
    "task_maker": 4,
    "production_workers": 6,
    "integration_worker": 2,
    "audit_workers": 3,
    "tester_workers": 4,
}

DEFAULT_MIN_THREADS = {
    "task_maker": 1,
    "production_workers": 1,
    "integration_worker": 1,
    "audit_workers": 1,
    "tester_workers": 1,
}

DEFAULT_SERVICE_CAPS = {"STABLE_BDS": 2}

UPSTREAM_POOLS = {
    "task_maker": [],
    "production_workers": ["task_maker"],
    "integration_worker": ["production_workers"],
    "audit_workers": ["production_workers"],
    "tester_workers": ["production_workers"],
}


class ScalingError(ValueError):
    pass


@dataclass(frozen=True)
class AdaptiveScalingPolicy:
    wait_heartbeats: int = 2
    idle_heartbeats: int = 4
    min_threads: Mapping[str, int] = field(
        default_factory=lambda: dict(DEFAULT_MIN_THREADS)
    )
    max_threads: Mapping[str, int] = field(
        default_factory=lambda: dict(DEFAULT_MAX_THREADS)
    )
    service_caps: Mapping[str, int] = field(
        default_factory=lambda: dict(DEFAULT_SERVICE_CAPS)
    )

    def __post_init__(self) -> None:
        if self.wait_heartbeats < 1:
            raise ScalingError("wait_heartbeats must be at least 1")
        if self.idle_heartbeats < 1:
            raise ScalingError("idle_heartbeats must be at least 1")
        expected = set(LANE_TO_POOL.values())
        if set(self.min_threads) != expected or set(self.max_threads) != expected:
            raise ScalingError("thread limits must define every named worker pool")
        for pool in sorted(expected):
            minimum = self.min_threads[pool]
            maximum = self.max_threads[pool]
            if (
                not isinstance(minimum, int)
                or isinstance(minimum, bool)
                or minimum < 0
            ):
                raise ScalingError(f"invalid minimum for {pool}")
            if (
                not isinstance(maximum, int)
                or isinstance(maximum, bool)
                or maximum < 1
                or maximum < minimum
            ):
                raise ScalingError(f"invalid maximum for {pool}")
        if any(
            not isinstance(limit, int) or isinstance(limit, bool) or limit < 1
            for limit in self.service_caps.values()
        ):
            raise ScalingError("service caps must be positive integers")

    def as_dict(self) -> dict[str, Any]:
        return {
            "wait_heartbeats": self.wait_heartbeats,
            "idle_heartbeats": self.idle_heartbeats,
            "min_threads": dict(self.min_threads),
            "max_threads": dict(self.max_threads),
            "service_caps": dict(self.service_caps),
        }


def load_adaptive_scaling_config(
    path: str | Path,
) -> tuple[bool, AdaptiveScalingPolicy]:
    """Load the machine-readable factory policy used by the overseer."""

    config_path = Path(path).expanduser().resolve()
    document = json.loads(config_path.read_text(encoding="utf-8"))
    section = document.get("adaptive_scaling")
    if not isinstance(section, Mapping):
        raise ScalingError("factory config has no adaptive_scaling object")
    service_values = section.get("service_caps")
    if not isinstance(service_values, Mapping):
        raise ScalingError("adaptive scaling service_caps must be an object")
    service_caps: dict[str, int] = {}
    for service, definition in service_values.items():
        if not isinstance(service, str) or not isinstance(definition, Mapping):
            raise ScalingError("adaptive scaling service cap entry rejected")
        execution_slots = definition.get("execution_slots")
        if not isinstance(execution_slots, int) or isinstance(execution_slots, bool):
            raise ScalingError(f"service cap has no integer execution_slots: {service}")
        service_caps[service] = execution_slots
    min_threads = section.get("min_threads")
    max_threads = section.get("max_threads")
    if not isinstance(min_threads, Mapping) or not isinstance(max_threads, Mapping):
        raise ScalingError("adaptive scaling thread limits must be objects")
    wait_heartbeats = section.get("wait_heartbeats_before_scale_up")
    idle_heartbeats = section.get("idle_heartbeats_before_scale_down")
    if (
        not isinstance(wait_heartbeats, int)
        or isinstance(wait_heartbeats, bool)
        or not isinstance(idle_heartbeats, int)
        or isinstance(idle_heartbeats, bool)
    ):
        raise ScalingError("adaptive heartbeat thresholds must be integers")
    policy = AdaptiveScalingPolicy(
        wait_heartbeats=wait_heartbeats,
        idle_heartbeats=idle_heartbeats,
        min_threads=dict(min_threads),
        max_threads=dict(max_threads),
        service_caps=service_caps,
    )
    enabled = section.get("enabled")
    if not isinstance(enabled, bool):
        raise ScalingError("adaptive scaling enabled flag must be boolean")
    return enabled, policy


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(_canonical_bytes(value) + b"\n")
    os.replace(temporary, path)


def _service(job: Mapping[str, Any]) -> str | None:
    payload = job.get("payload")
    if not isinstance(payload, Mapping):
        payload = {}
    for key in ("qualification_gate", "service", "gate"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().upper()
    stage = job.get("stage")
    if isinstance(stage, str) and stage.strip().upper() in DEFAULT_SERVICE_CAPS:
        return stage.strip().upper()
    return None


def _is_actionable(job: Mapping[str, Any]) -> bool:
    if job.get("status") in ACTIONABLE_STATUSES:
        return True
    payload = job.get("payload")
    return bool(
        isinstance(payload, Mapping)
        and payload.get("capacity_blocked") is True
        and job.get("status") == "WAITING"
    )


def _pool(job: Mapping[str, Any]) -> str | None:
    lane = job.get("lane")
    return LANE_TO_POOL.get(lane) if isinstance(lane, str) else None


class AdaptiveThreadScaler:
    """Restart-safe heartbeat pressure detector for conversation-owned tasks.

    This controller never creates or kills a Codex task itself. It emits one
    durable directive that the conversation-facing overseer acknowledges after
    it has assigned a packet. An unacknowledged directive is not duplicated on
    later heartbeats. Stable BDS has a separate proven-execution cap, so adding
    a tester task cannot accidentally imply another safe Docker BDS slot.
    """

    schema_version = "studio-adaptive-thread-scaling-v1"

    def __init__(
        self,
        state_path: str | Path,
        *,
        policy: AdaptiveScalingPolicy | None = None,
    ):
        self.state_path = Path(state_path).expanduser().resolve()
        self.policy = policy or AdaptiveScalingPolicy()
        self._lock = threading.RLock()

    def _empty_state(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cycle": 0,
            "wait_streaks": {},
            "idle_streaks": {pool: 0 for pool in self.policy.max_threads},
            "open_directives": {},
            "recent_directives": [],
            "last_observation": {},
            "policy": self.policy.as_dict(),
        }

    @contextmanager
    def _process_lock(self):
        """Serialize heartbeat projections across local overseer processes."""

        import fcntl

        lock_path = self.state_path.with_suffix(self.state_path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._empty_state()
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        if state.get("schema_version") != self.schema_version:
            raise ScalingError("adaptive scaling state schema rejected")
        if state.get("policy") != self.policy.as_dict():
            raise ScalingError(
                "adaptive scaling policy changed; migrate or remove only the runtime projection"
            )
        return state

    @staticmethod
    def _directive_id(payload: Mapping[str, Any]) -> str:
        return hashlib.sha256(_canonical_bytes(payload)).hexdigest()

    def _new_directive(
        self,
        state: dict[str, Any],
        *,
        action: str,
        pool: str,
        reason: str,
        job_ids: Sequence[str],
        service: str | None,
        capacity_used: int,
        capacity_limit: int,
    ) -> dict[str, Any]:
        identity = {
            "cycle": state["cycle"],
            "action": action,
            "pool": pool,
            "service": service,
            "job_ids": list(job_ids),
            "reason": reason,
        }
        directive = {
            "schema_version": self.schema_version,
            "directive_id": self._directive_id(identity),
            **identity,
            "wait_heartbeats": max(
                state["wait_streaks"].get(job_id, 0) for job_id in job_ids
            ),
            "capacity_used": capacity_used,
            "capacity_limit": capacity_limit,
            "upstream_pools": list(UPSTREAM_POOLS[pool]),
            "state": "OPEN",
        }
        state["open_directives"][directive["directive_id"]] = directive
        return directive

    def observe(
        self,
        jobs: Sequence[Mapping[str, Any]],
        *,
        assigned_threads: Mapping[str, int] | None = None,
    ) -> dict[str, Any]:
        """Record one overseer heartbeat and return the full durable snapshot."""

        with self._lock, self._process_lock():
            if assigned_threads is not None:
                unknown = set(assigned_threads) - set(self.policy.max_threads)
                if unknown:
                    raise ScalingError(
                        f"assigned thread counts contain unknown pools: {sorted(unknown)}"
                    )
                if any(
                    not isinstance(value, int)
                    or isinstance(value, bool)
                    or value < 0
                    for value in assigned_threads.values()
                ):
                    raise ScalingError(
                        "assigned thread counts must be non-negative integers"
                    )
            state = self._load()
            state["cycle"] += 1
            actionable = {
                str(job["id"]): job
                for job in jobs
                if job.get("id") is not None and _is_actionable(job) and _pool(job)
            }
            running = [
                job
                for job in jobs
                if job.get("status") == RUNNING_STATUS and _pool(job)
            ]

            prior_streaks = state["wait_streaks"]
            state["wait_streaks"] = {
                job_id: int(prior_streaks.get(job_id, 0)) + 1
                for job_id in actionable
            }

            # A spawn directive is fulfilled mechanically when its exact job
            # leaves the actionable queue. Backpressure resolves when all of
            # its named jobs do likewise or the constrained service frees up.
            for directive_id, directive in list(state["open_directives"].items()):
                named = set(directive["job_ids"])
                still_waiting = named.intersection(actionable)
                service = directive.get("service")
                service_active = sum(
                    1 for job in running if service is not None and _service(job) == service
                ) + sum(
                    1
                    for other in state["open_directives"].values()
                    if other["directive_id"] != directive_id
                    and other["action"] == "SPAWN_THREAD"
                    and other.get("service") == service
                )
                service_cap = self.policy.service_caps.get(service) if service else None
                resolved = not still_waiting
                if directive["action"] == "BACKPRESSURE_UPSTREAM" and service_cap is not None:
                    resolved = resolved or service_active < service_cap
                if resolved:
                    completed = {**directive, "state": "AUTO_RESOLVED", "resolved_cycle": state["cycle"]}
                    state["recent_directives"].append(completed)
                    del state["open_directives"][directive_id]

            active_by_pool = {
                pool: sum(1 for job in running if _pool(job) == pool)
                for pool in self.policy.max_threads
            }
            open_spawns_by_pool = {
                pool: sum(
                    1
                    for directive in state["open_directives"].values()
                    if directive["pool"] == pool and directive["action"] == "SPAWN_THREAD"
                )
                for pool in self.policy.max_threads
            }

            emitted: list[dict[str, Any]] = []
            waiting_by_pool: dict[str, list[Mapping[str, Any]]] = {
                pool: [] for pool in self.policy.max_threads
            }
            for job_id, job in actionable.items():
                if state["wait_streaks"][job_id] >= self.policy.wait_heartbeats:
                    waiting_by_pool[_pool(job)].append(job)  # type: ignore[index]
            for pool in waiting_by_pool:
                waiting_by_pool[pool].sort(
                    key=lambda job: (
                        -int(job.get("priority", 0)),
                        float(job.get("created_at", 0)),
                        str(job["id"]),
                    )
                )

            for pool, waiting in waiting_by_pool.items():
                for job in waiting:
                    job_id = str(job["id"])
                    already_open = any(
                        job_id in directive["job_ids"]
                        for directive in state["open_directives"].values()
                    )
                    if already_open:
                        continue
                    service = _service(job)
                    observed_pool_used = (
                        active_by_pool[pool] + open_spawns_by_pool[pool]
                    )
                    pool_used = (
                        max(
                            observed_pool_used,
                            int(assigned_threads.get(pool, 0)),
                        )
                        if assigned_threads is not None
                        else observed_pool_used
                    )
                    pool_limit = self.policy.max_threads[pool]
                    service_used = sum(
                        1 for running_job in running if _service(running_job) == service
                    ) + sum(
                        1
                        for directive in state["open_directives"].values()
                        if directive["action"] == "SPAWN_THREAD"
                        and directive.get("service") == service
                    )
                    service_limit = self.policy.service_caps.get(service)
                    constrained = pool_used >= pool_limit or (
                        service_limit is not None and service_used >= service_limit
                    )
                    if not constrained:
                        directive = self._new_directive(
                            state,
                            action="SPAWN_THREAD",
                            pool=pool,
                            reason="WAIT_THRESHOLD_REACHED",
                            job_ids=[job_id],
                            service=service,
                            capacity_used=service_used if service_limit is not None else pool_used,
                            capacity_limit=service_limit or pool_limit,
                        )
                        emitted.append(directive)
                        open_spawns_by_pool[pool] += 1
                        continue

                    saturated_key = (pool, service)
                    existing_backpressure = any(
                        directive["action"] == "BACKPRESSURE_UPSTREAM"
                        and (directive["pool"], directive.get("service")) == saturated_key
                        for directive in state["open_directives"].values()
                    )
                    if not existing_backpressure:
                        same_constraint = [
                            str(candidate["id"])
                            for candidate in waiting
                            if _service(candidate) == service
                        ]
                        directive = self._new_directive(
                            state,
                            action="BACKPRESSURE_UPSTREAM",
                            pool=pool,
                            reason=(
                                "SERVICE_CAP_SATURATED"
                                if service_limit is not None
                                else "POOL_CAP_SATURATED"
                            ),
                            job_ids=same_constraint,
                            service=service,
                            capacity_used=service_used if service_limit is not None else pool_used,
                            capacity_limit=service_limit or pool_limit,
                        )
                        emitted.append(directive)

            for pool in self.policy.max_threads:
                has_pressure = any(_pool(job) == pool for job in actionable.values())
                has_active = active_by_pool[pool] > 0
                state["idle_streaks"][pool] = (
                    0 if has_pressure or has_active else int(state["idle_streaks"].get(pool, 0)) + 1
                )
                if assigned_threads is None:
                    continue
                assigned = int(assigned_threads.get(pool, 0))
                open_release = any(
                    directive["action"] == "RELEASE_IDLE_THREAD"
                    and directive["pool"] == pool
                    for directive in state["open_directives"].values()
                )
                if (
                    state["idle_streaks"][pool] >= self.policy.idle_heartbeats
                    and assigned > self.policy.min_threads[pool]
                    and not open_release
                ):
                    emitted.append(
                        self._new_directive(
                            state,
                            action="RELEASE_IDLE_THREAD",
                            pool=pool,
                            reason="IDLE_COOLDOWN_REACHED",
                            job_ids=[f"idle:{pool}"],
                            service=None,
                            capacity_used=assigned,
                            capacity_limit=self.policy.min_threads[pool],
                        )
                    )

            state["last_observation"] = {
                "cycle": state["cycle"],
                "actionable_by_pool": {
                    pool: sum(1 for job in actionable.values() if _pool(job) == pool)
                    for pool in self.policy.max_threads
                },
                "running_by_pool": active_by_pool,
                "emitted_directive_ids": [item["directive_id"] for item in emitted],
            }
            state["recent_directives"] = state["recent_directives"][-100:]
            _atomic_json(self.state_path, state)
            return json.loads(json.dumps(state, sort_keys=True))

    def acknowledge(
        self,
        directive_id: str,
        *,
        outcome: str,
        worker_task_id: str | None = None,
        evidence: str | None = None,
    ) -> dict[str, Any]:
        if outcome not in {"ASSIGNED", "RELEASED", "FAILED"}:
            raise ScalingError("scaling outcome must be ASSIGNED, RELEASED, or FAILED")
        with self._lock, self._process_lock():
            state = self._load()
            directive = state["open_directives"].get(directive_id)
            if directive is None:
                for historical in state["recent_directives"]:
                    if historical["directive_id"] == directive_id:
                        return historical
                raise ScalingError(f"unknown open scaling directive: {directive_id}")
            if directive.get("state") == outcome:
                return directive
            completed = {
                **directive,
                "state": outcome,
                "resolved_cycle": state["cycle"],
                "worker_task_id": worker_task_id,
                "evidence": evidence,
            }
            if outcome == "ASSIGNED" and directive["action"] == "SPAWN_THREAD":
                # Keep the binding open until the exact packet is claimed.
                # This closes the acknowledgement-to-claim race without
                # creating another task for the same packet.
                state["open_directives"][directive_id] = completed
                _atomic_json(self.state_path, state)
                return completed
            del state["open_directives"][directive_id]
            state["recent_directives"].append(completed)
            if outcome == "FAILED":
                for job_id in directive["job_ids"]:
                    state["wait_streaks"][job_id] = 0
            if directive["action"] == "RELEASE_IDLE_THREAD" and outcome == "RELEASED":
                state["idle_streaks"][directive["pool"]] = 0
            state["recent_directives"] = state["recent_directives"][-100:]
            _atomic_json(self.state_path, state)
            return completed

    def snapshot(self) -> dict[str, Any]:
        with self._lock, self._process_lock():
            return self._load()
