from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from .runtime import WorkerPool
from .scaling import AdaptiveScalingPolicy, AdaptiveThreadScaler
from .store import OrchestrationStore


OverseerCallback = Callable[["OverseerRuntime"], None]

POOL_LANES: dict[str, frozenset[str]] = {
    "task_maker": frozenset({"EVIDENCE", "CONTROL"}),
    "production_workers": frozenset({"PRODUCTION"}),
    "integration_worker": frozenset({"INTEGRATION"}),
    "audit_workers": frozenset({"AUDIT"}),
    "tester_workers": frozenset({"QUALIFICATION"}),
}

DEFAULT_POOL_CONCURRENCY: dict[str, int] = {
    "task_maker": 2,
    "production_workers": 2,
    "integration_worker": 1,
    "audit_workers": 1,
    "tester_workers": 2,
}


class OverseerRuntime:
    """Conversation-facing coordinator for the bounded factory roles.

    The runtime deliberately contains no web server or UI.  A caller (for
    example, an overseer Codex thread) creates campaign work in the durable
    store and uses :meth:`snapshot` to report progress.  Optional callbacks
    provide reconciliation and mailbox adapters without coupling the core
    scheduler to a particular mailbox implementation.

    Shutdown is cooperative: no new jobs are claimed after :meth:`stop`, while
    already leased jobs are allowed to finish and publish their receipts.
    """

    def __init__(
        self,
        store: OrchestrationStore,
        *,
        runtime_root: str | Path,
        pool_concurrency: Mapping[str, int] | None = None,
        lease_seconds: float = 60.0,
        heartbeat_seconds: float = 10.0,
        poll_seconds: float = 0.1,
        reconciliation_interval_seconds: float = 1.0,
        reconciliation_callbacks: Iterable[OverseerCallback] | None = None,
        mailbox_callbacks: Iterable[OverseerCallback] | None = None,
        worker_prefix: str = "mccompiler-overseer",
        adaptive_scaling: bool = True,
        adaptive_scaling_policy: AdaptiveScalingPolicy | None = None,
    ):
        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be greater than zero")
        if reconciliation_interval_seconds <= 0:
            raise ValueError(
                "reconciliation_interval_seconds must be greater than zero"
            )

        configured = dict(pool_concurrency or {})
        unknown = set(configured) - set(POOL_LANES)
        if unknown:
            raise ValueError(f"unknown worker pool names: {sorted(unknown)}")
        concurrency = {
            name: int(configured.get(name, DEFAULT_POOL_CONCURRENCY[name]))
            for name in POOL_LANES
        }
        if any(limit < 1 for limit in concurrency.values()):
            raise ValueError("every worker pool concurrency must be at least 1")

        self.store = store
        self.runtime_root = Path(runtime_root).expanduser().resolve()
        self.poll_seconds = poll_seconds
        self.reconciliation_interval_seconds = reconciliation_interval_seconds
        self._reconciliation_callbacks = tuple(reconciliation_callbacks or ())
        self._mailbox_callbacks = tuple(mailbox_callbacks or ())
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._threads: dict[str, threading.Thread] = {}
        self._state = "STOPPED"
        self._started_at: float | None = None
        self._stopped_at: float | None = None
        self._pool_errors: dict[str, str | None] = {
            name: None for name in POOL_LANES
        }
        self._callback_errors: dict[str, str] = {}
        self._reconciliation_cycles = 0
        self._last_reconciled_at: float | None = None
        self.scaler = (
            AdaptiveThreadScaler(
                self.runtime_root / "adaptive-scaling" / "state.json",
                policy=adaptive_scaling_policy,
            )
            if adaptive_scaling
            else None
        )
        self._adaptive_scaling: dict[str, Any] | None = None

        self.pools: dict[str, WorkerPool] = {
            name: WorkerPool(
                store,
                runtime_root=self.runtime_root / "pools" / name,
                concurrency=concurrency[name],
                lease_seconds=lease_seconds,
                heartbeat_seconds=heartbeat_seconds,
                lanes=set(lanes),
                worker_prefix=f"{worker_prefix}-{name}",
                stop_event=self._stop_event,
            )
            for name, lanes in POOL_LANES.items()
        }

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._state == "RUNNING"

    def _run_pool(self, name: str, pool: WorkerPool) -> None:
        try:
            pool.run(
                stop_when_idle=False,
                poll_seconds=self.poll_seconds,
                stop_event=self._stop_event,
            )
        except Exception as exc:
            with self._lock:
                self._pool_errors[name] = f"{type(exc).__name__}: {exc}"
                self._state = "FAILED"
            # A failed pool means the coordinator no longer owns all declared
            # lanes. Stop the sibling pools instead of presenting partial
            # automation as healthy.
            self._stop_event.set()

    def _invoke_callbacks(self) -> None:
        callbacks = (
            ("reconciliation", self._reconciliation_callbacks),
            ("mailbox", self._mailbox_callbacks),
        )
        for group, group_callbacks in callbacks:
            for index, callback in enumerate(group_callbacks):
                key = f"{group}:{index}"
                try:
                    callback(self)
                except Exception as exc:
                    # An adapter failure is observable but is not allowed to
                    # kill workers that already hold durable queue leases.
                    with self._lock:
                        self._callback_errors[key] = (
                            f"{type(exc).__name__}: {exc}"
                        )
                else:
                    with self._lock:
                        self._callback_errors.pop(key, None)

    def _reconcile(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.store.refresh()
                if self.scaler is not None:
                    self._adaptive_scaling = self.scaler.observe(
                        self.store.list_jobs()
                    )
                self._invoke_callbacks()
            except Exception as exc:
                with self._lock:
                    self._callback_errors["store:refresh"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
            else:
                with self._lock:
                    self._callback_errors.pop("store:refresh", None)
            with self._lock:
                self._reconciliation_cycles += 1
                self._last_reconciled_at = time.time()
            self._stop_event.wait(self.reconciliation_interval_seconds)

    def start(self) -> None:
        """Start the named worker pools and reconciliation thread."""

        with self._lock:
            if self._state == "RUNNING":
                return
            if any(thread.is_alive() for thread in self._threads.values()):
                raise RuntimeError("overseer is still stopping")

            self.store.initialize()
            self.runtime_root.mkdir(parents=True, exist_ok=True)
            self._stop_event.clear()
            self._state = "RUNNING"
            self._started_at = time.time()
            self._stopped_at = None
            self._pool_errors = {name: None for name in POOL_LANES}
            self._callback_errors = {}
            self._reconciliation_cycles = 0
            self._last_reconciled_at = None
            self._threads = {
                name: threading.Thread(
                    target=self._run_pool,
                    args=(name, pool),
                    name=f"mccompiler-{name}",
                    daemon=True,
                )
                for name, pool in self.pools.items()
            }
            self._threads["overseer"] = threading.Thread(
                target=self._reconcile,
                name="mccompiler-overseer",
                daemon=True,
            )
            threads = tuple(self._threads.values())

        for thread in threads:
            thread.start()

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for all runtime threads; return ``False`` on timeout."""

        deadline = None if timeout is None else time.monotonic() + max(0.0, timeout)
        with self._lock:
            threads = tuple(self._threads.values())
        for thread in threads:
            remaining = (
                None
                if deadline is None
                else max(0.0, deadline - time.monotonic())
            )
            thread.join(remaining)
        stopped = not any(thread.is_alive() for thread in threads)
        if stopped:
            with self._lock:
                if self._state != "FAILED":
                    self._state = "STOPPED"
                self._stopped_at = self._stopped_at or time.time()
        return stopped

    def stop(self, timeout: float | None = None) -> bool:
        """Request cooperative shutdown and wait for workers to drain."""

        with self._lock:
            if self._state == "STOPPED" and not any(
                thread.is_alive() for thread in self._threads.values()
            ):
                return True
            if self._state != "FAILED":
                self._state = "STOPPING"
            self._stop_event.set()
        return self.wait(timeout)

    def snapshot(self, campaign_id: str | None = None) -> dict[str, Any]:
        """Return a JSON-serializable status view for the overseer thread."""

        with self._lock:
            threads = dict(self._threads)
            state = self._state
            started_at = self._started_at
            stopped_at = self._stopped_at
            pool_errors = dict(self._pool_errors)
            callback_errors = dict(self._callback_errors)
            cycles = self._reconciliation_cycles
            last_reconciled_at = self._last_reconciled_at
            adaptive_scaling = self._adaptive_scaling

        try:
            counts = self.store.counts(campaign_id)
        except Exception as exc:
            counts = {}
            callback_errors["store:snapshot"] = f"{type(exc).__name__}: {exc}"

        return {
            "schema_version": "1.0.0",
            "state": state,
            "started_at": started_at,
            "stopped_at": stopped_at,
            "campaign_id": campaign_id,
            "counts": counts,
            "pools": {
                name: {
                    "lanes": sorted(POOL_LANES[name]),
                    "concurrency": pool.concurrency,
                    "thread_alive": bool(
                        threads.get(name) and threads[name].is_alive()
                    ),
                    "error": pool_errors[name],
                }
                for name, pool in self.pools.items()
            },
            "reconciliation": {
                "thread_alive": bool(
                    threads.get("overseer") and threads["overseer"].is_alive()
                ),
                "cycles": cycles,
                "last_reconciled_at": last_reconciled_at,
                "callback_errors": callback_errors,
                "reconciliation_callback_count": len(
                    self._reconciliation_callbacks
                ),
                "mailbox_callback_count": len(self._mailbox_callbacks),
            },
            "adaptive_scaling": adaptive_scaling,
        }

    def __enter__(self) -> "OverseerRuntime":
        self.start()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.stop()
