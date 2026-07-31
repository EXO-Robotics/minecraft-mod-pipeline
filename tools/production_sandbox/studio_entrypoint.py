#!/usr/bin/env python3
"""Probe the Studio sandbox from inside, then exec the assigned worker."""

from __future__ import annotations

import json
import os
import socket
import subprocess
from pathlib import Path


GIT = str(
    next(
        candidate
        for candidate in (
            Path("/opt/homebrew/bin/git"),
            Path("/Applications/Xcode.app/Contents/Developer/usr/bin/git"),
            Path("/usr/bin/git"),
        )
        if candidate.is_file()
    )
)


def inaccessible(target: Path) -> bool:
    try:
        if target.is_dir():
            next(target.iterdir(), None)
        else:
            target.open("rb").read(1)
        return False
    except OSError:
        return True


def write_probe(target: Path) -> bool:
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("probe", encoding="utf-8")
        target.unlink()
        return True
    except OSError:
        return False


def network_denied() -> bool:
    try:
        with socket.create_connection(("1.1.1.1", 443), timeout=1):
            return False
    except OSError:
        return True


def git(repository: Path, *arguments: str) -> str:
    return subprocess.check_output(
        [GIT, *arguments],
        cwd=repository,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def main() -> int:
    repository = Path(os.environ["STUDIO_PRODUCTION_REPOSITORY"]).resolve()
    runtime = Path(os.environ["STUDIO_PRODUCTION_RUNTIME"]).resolve()
    assignment = json.loads(
        Path(os.environ["STUDIO_ASSIGNMENT"]).read_text(encoding="utf-8")
    )
    command = json.loads(os.environ["STUDIO_WORKER_COMMAND_JSON"])
    denied = {
        row["class"]: Path(row["path"])
        for row in assignment["denied_paths"]
    }
    git_directory = Path(
        git(repository, "rev-parse", "--path-format=absolute", "--git-common-dir")
    )
    alternates = git_directory / "objects/info/alternates"
    symlinks = [
        str(path.relative_to(repository))
        for path in repository.rglob("*")
        if path.is_symlink() and ".git" not in path.parts
    ]
    hardlinks = [
        str(path.relative_to(git_directory))
        for path in (git_directory / "objects").rglob("*")
        if path.is_file() and path.stat().st_nlink > 1
    ]
    restricted_environment = sorted(
        key
        for key in os.environ
        if any(
            token in key.upper()
            for token in (
                "EVIDENCE",
                "PRIVATE_ORACLE",
                "CANARY",
                "JAVA_SOURCE",
                "GITHUB_TOKEN",
                "OPENAI_API_KEY",
                "AWS_",
            )
        )
    )
    checks = {
        "approved_inputs_readable": all(
            (repository / row["path"]).is_file()
            for row in assignment["transferred_inputs"]
        ),
        "production_write": write_probe(repository / ".write-probe"),
        "runtime_write": write_probe(runtime / ".write-probe"),
        "temp_write": write_probe(Path(os.environ["TMPDIR"]) / ".write-probe"),
        "cache_write": write_probe(
            Path(os.environ["XDG_CACHE_HOME"]) / ".write-probe"
        ),
        "denied_paths": {
            denied_class: inaccessible(target)
            for denied_class, target in denied.items()
        },
        "remotes_absent": git(repository, "remote") == "",
        "alternates_absent": not alternates.exists(),
        "hardlinks_absent": not hardlinks,
        "cross_lane_symlinks_absent": not symlinks,
        "restricted_environment_absent": not restricted_environment,
        "external_network_denied": network_denied(),
        "pid": os.getpid(),
    }
    required_denials = {"evidence", "control", "private_oracle", "canary"}
    denials_pass = (
        required_denials.issubset(checks["denied_paths"])
        and all(checks["denied_paths"].values())
    )
    passed = denials_pass and all(
        value
        for key, value in checks.items()
        if isinstance(value, bool)
    )
    print(
        json.dumps(
            {
                "studio_production_preflight": {
                    "result": "PASS" if passed else "FAIL",
                    "checks": checks,
                }
            },
            sort_keys=True,
        ),
        flush=True,
    )
    if not passed:
        return 97
    os.execv(command[0], command)
    return 98


if __name__ == "__main__":
    raise SystemExit(main())
