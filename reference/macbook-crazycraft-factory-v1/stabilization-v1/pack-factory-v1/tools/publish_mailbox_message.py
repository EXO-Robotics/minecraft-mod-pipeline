#!/usr/bin/env python3
"""Publish one immutable factory mailbox message under a single local lock."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


MAILBOX = Path(
    "/Users/blakegrove/Desktop/bedrock-server/program/"
    "crazycraft-pack-factory-mailboxes-v1"
)
ALLOWED_ROOTS = {
    "candidate_submissions",
    "tester_intake",
    "tester_results",
    "worker_repairs",
    "integration_intake",
    "final_decisions",
}
MESSAGE_ID = re.compile(r"^[A-Z0-9][A-Z0-9._-]{7,127}$")


class PublishError(RuntimeError):
    pass


def run(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(MAILBOX), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def validate_target(value: str, message: dict[str, Any]) -> Path:
    relative = PurePosixPath(value)
    if (
        relative.is_absolute()
        or len(relative.parts) != 3
        or relative.parts[0] not in ALLOWED_ROOTS
        or relative.suffix != ".json"
        or any(part in {"", ".", ".."} or part.startswith(".") for part in relative.parts)
    ):
        raise PublishError("target path rejected")
    if relative.parts[1] != message.get("pack_id"):
        raise PublishError("target pack mismatch")
    if relative.stem != message.get("message_id"):
        raise PublishError("target message ID mismatch")
    return MAILBOX.joinpath(*relative.parts)


def validate_message(message: Any) -> dict[str, Any]:
    if not isinstance(message, dict):
        raise PublishError("message must be an object")
    required = {
        "schema_version",
        "message_id",
        "message_type",
        "pack_id",
        "sender_role",
        "recipient_role",
        "created_at",
        "source_authority_commit",
        "source_authority_tree",
        "candidate_generation",
        "exact_artifact_hashes",
        "parent_message_id",
        "required_action",
        "idempotency_key",
        "proof_boundary",
    }
    missing = sorted(required - message.keys())
    if missing:
        raise PublishError(f"missing required fields: {missing}")
    if message["schema_version"] != "1.0.0":
        raise PublishError("schema version rejected")
    if not MESSAGE_ID.fullmatch(str(message["message_id"])):
        raise PublishError("message ID rejected")
    for field, length in (
        ("source_authority_commit", 40),
        ("source_authority_tree", 40),
        ("idempotency_key", 64),
    ):
        value = str(message[field])
        if len(value) != length or any(character not in "0123456789abcdef" for character in value):
            raise PublishError(f"{field} rejected")
    if not isinstance(message["proof_boundary"], list):
        raise PublishError("proof boundary rejected")
    return message


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--actor", required=True)
    args = parser.parse_args()
    message = validate_message(json.loads(args.message.read_text(encoding="utf-8")))
    target = validate_target(args.target, message)
    git_dir = Path(run("rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = MAILBOX / git_dir
    lock_path = git_dir / "tester-publish.lock"
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        observed = run("rev-parse", "HEAD")
        if observed != args.expected_head:
            raise PublishError(
                f"stale expected head: expected={args.expected_head} observed={observed}"
            )
        if run("status", "--porcelain"):
            raise PublishError("mailbox worktree is not clean")
        if target.exists():
            raise PublishError("message target already exists")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".json.tmp")
        temporary.write_bytes(canonical(message) + b"\n")
        os.replace(temporary, target)
        run("add", target.relative_to(MAILBOX).as_posix())
        subprocess.run(
            [
                "git",
                "-C",
                str(MAILBOX),
                "-c",
                f"user.name={args.actor}",
                "-c",
                "user.email=factory-mailbox@local.invalid",
                "commit",
                "-m",
                f"mailbox: {message['message_id']}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        commit = run("rev-parse", "HEAD")
        tree = run("show", "-s", "--format=%T", "HEAD")
        if run("rev-parse", "HEAD^") != observed:
            raise PublishError("publication parent mismatch")
        if run("status", "--porcelain"):
            raise PublishError("mailbox dirty after publication")
        result = {
            "message_id": message["message_id"],
            "commit": commit,
            "tree": tree,
            "parent": observed,
            "target": target.relative_to(MAILBOX).as_posix(),
            "message_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
