from __future__ import annotations

import socket
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .executor import ExecutionError, JobExecutor
from .store import OrchestrationStore


class WorkerPool:
    """Bounded threaded workers sharing transactional SQLite claims."""

    def __init__(
        self,
        store: OrchestrationStore,
        *,
        runtime_root: str | Path,
        concurrency: int = 4,
        lease_seconds: float = 60.0,
        heartbeat_seconds: float = 10.0,
        lanes: set[str] | None = None,
        worker_prefix: str | None = None,
        stop_event: threading.Event | None = None,
    ):
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1")
        if lease_seconds <= heartbeat_seconds:
            raise ValueError("lease_seconds must be greater than heartbeat_seconds")
        self.store = store
        self.executor = JobExecutor(runtime_root)
        self.concurrency = concurrency
        self.lease_seconds = lease_seconds
        self.heartbeat_seconds = heartbeat_seconds
        self.lanes = lanes
        self.stop_event = stop_event
        self.worker_prefix = worker_prefix or (
            f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        )

    def _run_job(self, job: dict[str, Any], worker_id: str) -> str:
        last_heartbeat = 0.0
        lock = threading.Lock()

        def heartbeat() -> None:
            nonlocal last_heartbeat
            with lock:
                now = time.monotonic()
                if now - last_heartbeat < self.heartbeat_seconds:
                    return
                if not self.store.heartbeat(
                    job["id"],
                    worker_id=worker_id,
                    lease_seconds=self.lease_seconds,
                ):
                    raise ExecutionError(f"lease lost while running {job['id']}")
                last_heartbeat = now

        try:
            result, receipt_path, receipt_hash = self.executor.execute(
                job,
                worker_id=worker_id,
                heartbeat=heartbeat,
            )
            self.store.succeed(
                job["id"],
                worker_id=worker_id,
                result=result,
                receipt_path=receipt_path,
                receipt_sha256=receipt_hash,
            )
            return "SUCCEEDED"
        except ExecutionError as exc:
            return self.store.fail(
                job["id"],
                worker_id=worker_id,
                error=str(exc),
                receipt_path=exc.receipt_path,
                receipt_sha256=exc.receipt_sha256,
            )

    def run(
        self,
        *,
        stop_when_idle: bool = True,
        idle_grace_seconds: float = 0.5,
        poll_seconds: float = 0.1,
        stop_event: threading.Event | None = None,
    ) -> dict[str, int]:
        """Run workers until idle or cooperatively asked to stop.

        Setting ``stop_event`` prevents new claims.  Work that already owns a
        lease is allowed to finish so that a shutdown cannot strand a command
        half way through publishing an artifact or receipt.  Existing callers
        that do not pass an event retain the original idle/forever behavior.
        """

        if idle_grace_seconds < 0:
            raise ValueError("idle_grace_seconds must not be negative")
        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be greater than zero")
        stop_event = stop_event or self.stop_event
        self.store.initialize()
        futures: dict[Future[str], str] = {}
        idle_since: float | None = None
        worker_number = 0
        with ThreadPoolExecutor(
            max_workers=self.concurrency,
            thread_name_prefix="mccompiler-worker",
        ) as pool:
            while True:
                finished = [future for future in futures if future.done()]
                for future in finished:
                    future.result()
                    del futures[future]

                stopping = stop_event is not None and stop_event.is_set()
                claimed_any = False
                while not stopping and len(futures) < self.concurrency:
                    worker_number += 1
                    worker_id = f"{self.worker_prefix}-w{worker_number}"
                    job = self.store.claim(
                        worker_id=worker_id,
                        lease_seconds=self.lease_seconds,
                        lanes=self.lanes,
                    )
                    if job is None:
                        break
                    claimed_any = True
                    future = pool.submit(self._run_job, job, worker_id)
                    futures[future] = job["id"]
                    stopping = stop_event is not None and stop_event.is_set()

                if stopping and not futures:
                    break

                if futures or claimed_any:
                    idle_since = None
                elif stop_when_idle:
                    idle_since = idle_since or time.monotonic()
                    if time.monotonic() - idle_since >= idle_grace_seconds:
                        break

                if stop_event is not None and not stop_event.is_set():
                    stop_event.wait(poll_seconds)
                else:
                    # Once the event is set, Event.wait() returns immediately.
                    # Sleep while leased work drains to avoid a busy loop.
                    time.sleep(poll_seconds)
        return self.store.counts()
