#!/usr/bin/env python3
"""OpenSSH forced-command adapter for one fixed Crazy Craft role."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from pathlib import Path

JOB_ID = re.compile(r"^JOB-[0-9]{12}$")
OPERATIONS = {"ingest", "activate", "status", "fetch", "fetch-failure", "cleanup"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-role", choices=("T1", "T10"), required=True)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("~/crazycraft-remote-jobs").expanduser(),
    )
    args = parser.parse_args()
    original = os.environ.get("SSH_ORIGINAL_COMMAND", "")
    try:
        words = shlex.split(original, posix=True)
    except ValueError:
        return 126
    if len(words) != 4:
        return 126
    executable, operation, role, job_id = words
    if executable != "/usr/local/libexec/crazycraft-remote-entry":
        return 126
    if operation not in OPERATIONS or role != args.expected_role:
        return 126
    if not JOB_ID.fullmatch(job_id):
        return 126
    entrypoint = Path(__file__).resolve().with_name("remote_job_entrypoint.py")
    if not entrypoint.is_file():
        return 127
    environment = {
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(args.root / "runtime" / f"{role.lower()}-home"),
        "TMPDIR": str(args.root / "runtime" / f"{role.lower()}-tmp"),
        "CRAZYCRAFT_REMOTE_ROLE": role,
        "CRAZYCRAFT_REMOTE_ROOT": str(args.root),
    }
    os.execve(
        sys.executable,
        [
            sys.executable,
            str(entrypoint),
            operation,
            role,
            job_id,
            "--root",
            str(args.root),
        ],
        environment,
    )
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
