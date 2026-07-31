#!/usr/bin/env python3
"""Render a launchd agent for the durable orchestration worker pool."""

from __future__ import annotations

import argparse
import plistlib
from pathlib import Path


def render_launch_agent(
    *,
    repository: Path,
    database: Path,
    runtime_root: Path,
    concurrency: int,
    lanes: list[str],
) -> dict[str, object]:
    repository = repository.expanduser().resolve()
    database = database.expanduser().resolve()
    runtime_root = runtime_root.expanduser().resolve()
    executable = repository / ".venv/bin/bedrock-factory"
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")
    arguments = [
        str(executable),
        "--db",
        str(database),
        "run",
        "--forever",
        "--concurrency",
        str(concurrency),
        "--runtime-root",
        str(runtime_root),
    ]
    for lane in lanes:
        arguments.extend(["--lane", lane])
    return {
        "Label": "com.mccompiler.orchestrator",
        "ProgramArguments": arguments,
        "WorkingDirectory": str(repository),
        "RunAtLoad": True,
        "KeepAlive": True,
        "ProcessType": "Background",
        "ThrottleInterval": 10,
        "StandardOutPath": str(runtime_root / "launchd.stdout.log"),
        "StandardErrorPath": str(runtime_root / "launchd.stderr.log"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--lane", action="append", default=[])
    args = parser.parse_args()
    payload = render_launch_agent(
        repository=args.repository,
        database=args.db,
        runtime_root=args.runtime_root,
        concurrency=args.concurrency,
        lanes=args.lane,
    )
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(plistlib.dumps(payload, sort_keys=True))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
