from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

from .dispatch import DispatchError, ThreadDispatchOutbox
from .eventlog import CanonicalEventLog, EventLogError, rebuild_projection, verify_projection
from .mailbox import MailboxError
from .overseer import POOL_LANES, OverseerRuntime
from .planner import FactoryPlanningError, write_factory_plan
from .platform_authority import (
    PlatformAuthorityError,
    resolve_standing_launch_authority,
    validate_platform_qualification,
)
from .pre_bds_validation import inspect_mcaddon
from .metrics import compute_metrics
from .objects import EvidenceObjectStore, ObjectStoreError
from .campaign import CampaignDefinitionError, load_campaign_definition
from .runtime import WorkerPool
from .scaling import (
    AdaptiveScalingPolicy,
    AdaptiveThreadScaler,
    ScalingError,
    load_adaptive_scaling_config,
)
from .store import OrchestrationStore, StoreError


def _default_db() -> Path:
    return Path(os.environ.get("BEDROCK_FACTORY_QUEUE", ".mccompiler/orchestration.sqlite3"))


def _store(args: argparse.Namespace) -> OrchestrationStore:
    return OrchestrationStore(args.db)


def _print(payload: object, *, pretty: bool = True) -> None:
    print(json.dumps(payload, indent=2 if pretty else None, sort_keys=True))


def _pool_concurrency(values: list[str] | None) -> dict[str, int]:
    configured: dict[str, int] = {}
    for value in values or []:
        name, separator, raw_limit = value.partition("=")
        if not separator or name not in POOL_LANES:
            raise ValueError(
                "--pool must be NAME=COUNT where NAME is one of "
                + ", ".join(POOL_LANES)
            )
        limit = int(raw_limit)
        if limit < 1:
            raise ValueError("pool concurrency must be at least 1")
        configured[name] = limit
    return configured


def _assigned_threads(values: list[str] | None) -> dict[str, int]:
    assigned: dict[str, int] = {}
    for value in values or []:
        name, separator, raw_count = value.partition("=")
        if not separator or name not in POOL_LANES:
            raise ValueError(
                "--assigned must be NAME=COUNT where NAME is one of "
                + ", ".join(POOL_LANES)
            )
        count = int(raw_count)
        if count < 0:
            raise ValueError("assigned thread count must not be negative")
        assigned[name] = count
    return assigned


def _adaptive_policy(
    config_path: Path | None,
) -> tuple[bool, AdaptiveScalingPolicy]:
    if config_path is None:
        return True, AdaptiveScalingPolicy()
    return load_adaptive_scaling_config(config_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bedrock-factory",
        description="Durable multi-worker Java-to-Bedrock campaign controller",
    )
    parser.add_argument("--db", type=Path, default=_default_db())
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize the SQLite queue")
    create = sub.add_parser("create", help="Create a campaign from a JSON definition")
    create.add_argument("--definition", type=Path, required=True)

    run = sub.add_parser("run", help="Run a bounded worker pool")
    run.add_argument("--concurrency", type=int, default=4)
    run.add_argument("--runtime-root", type=Path, default=Path(".mccompiler/runtime"))
    run.add_argument("--lease-seconds", type=float, default=60)
    run.add_argument("--heartbeat-seconds", type=float, default=10)
    run.add_argument("--lane", action="append", dest="lanes")
    run.add_argument(
        "--forever",
        action="store_true",
        help="Poll continuously instead of exiting when currently runnable work is idle",
    )

    status = sub.add_parser("status", help="Show campaigns and jobs")
    status.add_argument("--campaign")
    status.add_argument("--job")

    approve = sub.add_parser("approve", help="Approve an explicit manual gate")
    approve.add_argument("job")
    approve.add_argument("--operator", required=True)
    approve.add_argument("--reason", required=True)

    retry = sub.add_parser("retry", help="Reset a quarantined or blocked job")
    retry.add_argument("job")
    retry.add_argument("--operator", required=True)
    retry.add_argument("--reason", required=True)
    retry.add_argument("--additional-attempts", type=int, default=1)

    events = sub.add_parser("events", help="Read the append-only event stream")
    events.add_argument("--campaign", required=True)
    events.add_argument("--after", type=int, default=0)
    events.add_argument("--limit", type=int, default=200)

    plan = sub.add_parser(
        "factory-plan",
        help="Inspect one authorized local modpack and write a deterministic task plan",
    )
    plan.add_argument("--modpack", type=Path, required=True)
    plan.add_argument("--output-root", type=Path, required=True)
    plan.add_argument("--authority", required=True)
    plan.add_argument(
        "--authorization-file",
        type=Path,
        help="Optional JSON object keyed by authorization ID",
    )

    oversee = sub.add_parser(
        "oversee",
        help="Run the conversation-facing bounded role pools (no web UI)",
    )
    oversee.add_argument("--runtime-root", type=Path, required=True)
    oversee.add_argument(
        "--pool",
        action="append",
        help="Override a named pool as NAME=COUNT",
    )
    oversee.add_argument(
        "--seconds",
        type=float,
        default=0,
        help="Stop after N seconds; zero runs until SIGINT/SIGTERM",
    )
    oversee.add_argument("--campaign")
    oversee.add_argument(
        "--config",
        type=Path,
        help="Factory config; defaults to the parent of --runtime-root when present",
    )

    pending = sub.add_parser(
        "dispatch-pending",
        help="List durable worker requests for this overseer task to send",
    )
    pending.add_argument("--outbox", type=Path, required=True)

    acknowledge = sub.add_parser(
        "dispatch-ack",
        help="Record a successfully sent, failed, or superseded worker request",
    )
    acknowledge.add_argument("--outbox", type=Path, required=True)
    acknowledge.add_argument("--request", required=True)
    acknowledge.add_argument(
        "--state",
        required=True,
        choices=["SENT", "ACKNOWLEDGED", "FAILED", "SUPERSEDED"],
    )
    acknowledge.add_argument("--worker-task-id")
    acknowledge.add_argument("--error-code")

    messages = sub.add_parser("mailbox-messages", help="Read the durable semantic mailbox")
    messages.add_argument("--campaign")
    messages.add_argument("--pack")
    messages.add_argument("--message-type")

    candidates = sub.add_parser("candidates", help="Read immutable candidate generations")
    candidates.add_argument("--campaign")
    candidates.add_argument("--pack")

    platform_validate = sub.add_parser(
        "platform-validate",
        help="Validate one exact factory-platform qualification receipt",
    )
    platform_validate.add_argument("--receipt", type=Path, required=True)

    authority_resolve = sub.add_parser(
        "authority-resolve",
        help="Resolve a typed activation against standing and platform authority",
    )
    authority_resolve.add_argument("--authority", type=Path, required=True)
    authority_resolve.add_argument("--activation", type=Path, required=True)
    authority_resolve.add_argument("--platform-receipt", type=Path, required=True)

    pre_bds = sub.add_parser(
        "pre-bds-validate",
        help="Run the package checks owned by PRE_BDS_MILESTONE",
    )
    pre_bds.add_argument("--candidate", type=Path, required=True)

    event_append = sub.add_parser("event-append", help="Append one canonical lifecycle event")
    event_append.add_argument("--log", type=Path, required=True)
    event_append.add_argument("--event", type=Path, required=True)

    projection_rebuild = sub.add_parser("projection-rebuild", help="Rebuild lifecycle SQLite from zero")
    projection_rebuild.add_argument("--log", type=Path, required=True)
    projection_rebuild.add_argument("--projection", type=Path, required=True)

    projection_verify = sub.add_parser("projection-verify", help="Fail closed if retained lifecycle projection differs")
    projection_verify.add_argument("--log", type=Path, required=True)
    projection_verify.add_argument("--projection", type=Path, required=True)

    metrics = sub.add_parser("metrics", help="Compute throughput metrics from canonical events")
    metrics.add_argument("--log", type=Path, required=True)

    object_put = sub.add_parser("object-put", help="Store one content-addressed evidence object")
    object_put.add_argument("--objects", type=Path, required=True)
    object_put.add_argument("--file", type=Path, required=True)
    object_put.add_argument("--object-type", required=True)

    scaling_status = sub.add_parser(
        "scaling-status", help="Read adaptive thread pressure and open directives"
    )
    scaling_status.add_argument("--state", type=Path, required=True)
    scaling_status.add_argument("--config", type=Path)

    scaling_heartbeat = sub.add_parser(
        "scaling-heartbeat", help="Record one adaptive overseer heartbeat"
    )
    scaling_heartbeat.add_argument("--state", type=Path, required=True)
    scaling_heartbeat.add_argument("--campaign")
    scaling_heartbeat.add_argument("--config", type=Path)
    scaling_heartbeat.add_argument(
        "--assigned",
        action="append",
        help="Actual conversation tasks by pool as NAME=COUNT; enables scale-down",
    )

    scaling_ack = sub.add_parser(
        "scaling-ack", help="Acknowledge one adaptive scaling directive"
    )
    scaling_ack.add_argument("--state", type=Path, required=True)
    scaling_ack.add_argument("--directive", required=True)
    scaling_ack.add_argument(
        "--outcome", required=True, choices=["ASSIGNED", "RELEASED", "FAILED"]
    )
    scaling_ack.add_argument("--worker-task-id")
    scaling_ack.add_argument("--evidence")
    scaling_ack.add_argument("--config", type=Path)

    args = parser.parse_args(argv)
    store = _store(args)
    try:
        if args.command == "init":
            store.initialize()
            _print({"ok": True, "database": str(store.path)})
        elif args.command == "create":
            _print(load_campaign_definition(args.definition, store))
        elif args.command == "run":
            pool = WorkerPool(
                store,
                runtime_root=args.runtime_root,
                concurrency=args.concurrency,
                lease_seconds=args.lease_seconds,
                heartbeat_seconds=args.heartbeat_seconds,
                lanes=set(args.lanes) if args.lanes else None,
            )
            _print(
                {
                    "ok": True,
                    "counts": pool.run(stop_when_idle=not args.forever),
                }
            )
        elif args.command == "status":
            store.initialize()
            if args.job:
                _print(store.get_job(args.job))
            else:
                _print(
                    {
                        "counts": store.counts(args.campaign),
                        "jobs": store.list_jobs(campaign_id=args.campaign),
                    }
                )
        elif args.command == "approve":
            store.approve(args.job, operator=args.operator, reason=args.reason)
            _print({"ok": True, "job": store.get_job(args.job)})
        elif args.command == "retry":
            store.retry(
                args.job,
                operator=args.operator,
                reason=args.reason,
                additional_attempts=args.additional_attempts,
            )
            _print({"ok": True, "job": store.get_job(args.job)})
        elif args.command == "events":
            _print(
                {
                    "events": store.events(
                        args.campaign,
                        after_sequence=args.after,
                        limit=args.limit,
                    )
                }
            )
        elif args.command == "factory-plan":
            overrides = None
            if args.authorization_file:
                overrides = json.loads(
                    args.authorization_file.read_text(encoding="utf-8")
                )
                if not isinstance(overrides, dict):
                    raise ValueError("authorization file must contain a JSON object")
            target = write_factory_plan(
                args.modpack,
                args.output_root,
                inspection_authority=args.authority,
                authorization_overrides=overrides,
            )
            document = json.loads(target.read_text(encoding="utf-8"))
            _print(
                {
                    "ok": True,
                    "plan": str(target),
                    "plan_id": document["plan_id"],
                    "unit_count": len(document["intake"]["units"]),
                    "task_count": len(document["tasks"]),
                }
            )
        elif args.command == "oversee":
            if args.seconds < 0:
                raise ValueError("--seconds must not be negative")
            config_path = args.config
            inferred_config = (
                args.runtime_root.expanduser().resolve().parent
                / "factory-config.json"
            )
            if config_path is None and inferred_config.is_file():
                config_path = inferred_config
            scaling_enabled, scaling_policy = _adaptive_policy(config_path)
            runtime = OverseerRuntime(
                store,
                runtime_root=args.runtime_root,
                pool_concurrency=_pool_concurrency(args.pool),
                adaptive_scaling=scaling_enabled,
                adaptive_scaling_policy=scaling_policy,
            )
            stopping = False

            def request_stop(_signum: int, _frame: object) -> None:
                nonlocal stopping
                stopping = True

            previous = {
                signum: signal.signal(signum, request_stop)
                for signum in (signal.SIGINT, signal.SIGTERM)
            }
            runtime.start()
            started = time.monotonic()
            try:
                while not stopping and (
                    args.seconds == 0 or time.monotonic() - started < args.seconds
                ):
                    time.sleep(0.1)
            finally:
                runtime.stop(timeout=30)
                for signum, handler in previous.items():
                    signal.signal(signum, handler)
            _print({"ok": True, "overseer": runtime.snapshot(args.campaign)})
        elif args.command == "dispatch-pending":
            _print({"requests": ThreadDispatchOutbox(args.outbox).pending()})
        elif args.command == "dispatch-ack":
            _print(
                ThreadDispatchOutbox(args.outbox).acknowledge(
                    args.request,
                    state=args.state,
                    worker_task_id=args.worker_task_id,
                    error_code=args.error_code,
                )
            )
        elif args.command == "mailbox-messages":
            store.initialize()
            _print(
                {
                    "messages": store.list_messages(
                        campaign_id=args.campaign,
                        pack_id=args.pack,
                        message_type=args.message_type,
                    )
                }
            )
        elif args.command == "candidates":
            store.initialize()
            _print(
                {
                    "candidates": store.list_candidates(
                        campaign_id=args.campaign,
                        pack_id=args.pack,
                    )
                }
            )
        elif args.command == "platform-validate":
            receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
            validate_platform_qualification(receipt)
            _print({"status": "PASS", "qualification_id": receipt["qualification_id"]})
        elif args.command == "authority-resolve":
            authority = json.loads(args.authority.read_text(encoding="utf-8"))
            activation = json.loads(args.activation.read_text(encoding="utf-8"))
            platform_receipt = json.loads(
                args.platform_receipt.read_text(encoding="utf-8")
            )
            result = resolve_standing_launch_authority(
                authority, activation, platform_receipt
            )
            _print(result)
            if result["status"] != "PASS":
                return 2
        elif args.command == "pre-bds-validate":
            result = inspect_mcaddon(args.candidate)
            _print(result)
            if result["status"] != "PASS":
                return 1
        elif args.command == "event-append":
            event = json.loads(args.event.read_text(encoding="utf-8"))
            _print(CanonicalEventLog(args.log).append(**event))
        elif args.command == "projection-rebuild":
            _print(rebuild_projection(CanonicalEventLog(args.log).read(), args.projection))
        elif args.command == "projection-verify":
            _print(verify_projection(CanonicalEventLog(args.log).read(), args.projection))
        elif args.command == "metrics":
            _print(compute_metrics(CanonicalEventLog(args.log).read()))
        elif args.command == "object-put":
            _print(EvidenceObjectStore(args.objects).put_file(args.file, object_type=args.object_type))
        elif args.command == "scaling-status":
            _, scaling_policy = _adaptive_policy(args.config)
            _print(
                {
                    "adaptive_scaling": AdaptiveThreadScaler(
                        args.state, policy=scaling_policy
                    ).snapshot()
                }
            )
        elif args.command == "scaling-heartbeat":
            store.initialize()
            scaling_enabled, scaling_policy = _adaptive_policy(args.config)
            if not scaling_enabled:
                raise ScalingError("adaptive scaling is disabled by factory config")
            assigned = _assigned_threads(args.assigned)
            _print(
                {
                    "adaptive_scaling": AdaptiveThreadScaler(
                        args.state, policy=scaling_policy
                    ).observe(
                        store.list_jobs(campaign_id=args.campaign),
                        assigned_threads=assigned if args.assigned else None,
                    )
                }
            )
        elif args.command == "scaling-ack":
            scaling_enabled, scaling_policy = _adaptive_policy(args.config)
            if not scaling_enabled:
                raise ScalingError("adaptive scaling is disabled by factory config")
            _print(
                AdaptiveThreadScaler(args.state, policy=scaling_policy).acknowledge(
                    args.directive,
                    outcome=args.outcome,
                    worker_task_id=args.worker_task_id,
                    evidence=args.evidence,
                )
            )
        return 0
    except (
        DispatchError,
        FactoryPlanningError,
        PlatformAuthorityError,
        EventLogError,
        ObjectStoreError,
        MailboxError,
        CampaignDefinitionError,
        StoreError,
        ScalingError,
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        _print({"ok": False, "error": str(exc)}, pretty=False)
        return 2


if __name__ == "__main__":
    sys.exit(main())
