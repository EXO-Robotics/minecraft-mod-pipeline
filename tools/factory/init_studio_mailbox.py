#!/usr/bin/env python3
"""Create an empty, independent, append-only Studio factory mailbox."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMAS = ROOT / "schemas" / "mailbox"
MAILBOX_ROOTS = (
    "candidate_submissions",
    "tester_intake",
    "tester_results",
    "worker_repairs",
    "integration_intake",
    "final_decisions",
)


def run(*argv: str, cwd: Path) -> str:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def initialize_mailbox(target: Path, schemas: Path, branch: str) -> dict[str, str]:
    target = target.expanduser().resolve()
    schemas = schemas.expanduser().resolve()
    if target.exists():
        raise ValueError(f"mailbox target already exists: {target}")
    if not schemas.is_dir():
        raise ValueError(f"mailbox schemas do not exist: {schemas}")
    target.parent.mkdir(parents=True, exist_ok=True)
    run("git", "init", "-q", "-b", branch, str(target), cwd=target.parent)
    (target / ".gitignore").write_text(
        ".runtime/\n.DS_Store\n*.tmp\n",
        encoding="utf-8",
    )
    (target / "README.md").write_text(
        "# Studio Java-to-Bedrock factory mailbox\n\n"
        "Messages are immutable Git records. Runtime cursors and queues are "
        "reconstructable and never modify a committed message.\n",
        encoding="utf-8",
    )
    for name in MAILBOX_ROOTS:
        directory = target / name
        directory.mkdir()
        (directory / ".keep").write_text("", encoding="utf-8")
    shutil.copytree(schemas, target / "schemas")
    run("git", "add", ".", cwd=target)
    run(
        "git",
        "-c",
        "user.name=Studio Factory Mailbox",
        "-c",
        "user.email=studio-factory@local.invalid",
        "commit",
        "-q",
        "-m",
        "factory: initialize Studio mailbox",
        cwd=target,
    )
    return {
        "mailbox": str(target),
        "ref": f"refs/heads/{branch}",
        "commit": run("git", "rev-parse", "HEAD", cwd=target),
        "tree": run("git", "rev-parse", "HEAD^{tree}", cwd=target),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    parser.add_argument("--branch", default="codex/studio-factory-mailbox-v1")
    args = parser.parse_args()
    try:
        result = initialize_mailbox(args.target, args.schemas, args.branch)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
