#!/usr/bin/env python3
"""Run two fixed, non-sensitive Docker isolation fixtures in parallel.

This is not BDS qualification. It proves only the container mount/resource
construction available to the bounded remote runner.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

IMAGE = "crazycraft-python-test@sha256:4203883759408bd6904fc20a974b4c16094b5c8e605a1cbbaaa87e139e8fbebe"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_one(base: Path, index: int) -> dict:
    job = base / f"job-{index}"
    input_root = job / "input"
    output_root = job / "output"
    input_root.mkdir(parents=True)
    output_root.mkdir()
    os.chmod(output_root, 0o777)
    package = input_root / "package.mcaddon"
    package.write_bytes(f"synthetic-package-{index}\n".encode())
    evidence = base / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "canary.txt").write_text("synthetic-evidence-canary\n")
    cidfile = job / "container.cid"
    name = f"crazycraft-remote-isolation-{os.getpid()}-{index}"
    command = [
        "/usr/local/bin/docker",
        "run",
        "--rm",
        "--name",
        name,
        "--cidfile",
        str(cidfile),
        "--network",
        "none",
        "--read-only",
        "--user",
        "65534:65534",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--cpus",
        "1",
        "--memory",
        "128m",
        "--restart",
        "no",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=32m",
        "--mount",
        f"type=bind,src={input_root},dst=/input,readonly,bind-propagation=rprivate",
        "--mount",
        f"type=bind,src={output_root},dst=/output,bind-propagation=rprivate",
        IMAGE,
        "/bin/sh",
        "-c",
        "test ! -e /evidence/canary.txt && cp /input/package.mcaddon /output/observed.mcaddon && printf PASS > /output/result.txt",
    ]
    started = time.time()
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    ended = time.time()
    output_package = output_root / "observed.mcaddon"
    return {
        "job": index,
        "container_name": name,
        "container_id": cidfile.read_text().strip() if cidfile.exists() else None,
        "input_root": str(input_root),
        "output_root": str(output_root),
        "network": "none",
        "port": 20000 + index,
        "exit_status": completed.returncode,
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "input_sha256": digest(package),
        "output_sha256": digest(output_package) if output_package.exists() else None,
        "evidence_canary_unmounted": completed.returncode == 0,
        "elapsed_seconds": round(ended - started, 6),
        "cleanup_status": "CONTAINER_REMOVED"
        if subprocess.run(
            ["/usr/local/bin/docker", "container", "inspect", name],
            capture_output=True,
            check=False,
        ).returncode
        != 0
        else "CONTAINER_REMAINS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = Path(tempfile.mkdtemp(prefix="crazycraft-parallel-docker-"))
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            records = list(pool.map(lambda index: run_one(base, index), (1, 2)))
        unique = {
            "input_roots": len({record["input_root"] for record in records}) == 2,
            "output_roots": len({record["output_root"] for record in records}) == 2,
            "container_names": len({record["container_name"] for record in records}) == 2,
            "ports": len({record["port"] for record in records}) == 2,
        }
        passed = (
            all(record["exit_status"] == 0 for record in records)
            and all(record["input_sha256"] == record["output_sha256"] for record in records)
            and all(record["evidence_canary_unmounted"] for record in records)
            and all(record["cleanup_status"] == "CONTAINER_REMOVED" for record in records)
            and all(unique.values())
        )
        result = {
            "schema_version": "1.0.0",
            "classification": "SYNTHETIC_PARALLEL_DOCKER_ISOLATION_PASS"
            if passed
            else "SYNTHETIC_PARALLEL_DOCKER_ISOLATION_FAIL",
            "image": IMAGE,
            "jobs": records,
            "unique_resources": unique,
            "proof_boundary": "Two fixed synthetic Docker jobs; host identity must be bound by the enclosing execution receipt. This is not BDS qualification.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
        return 0 if passed else 1
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
