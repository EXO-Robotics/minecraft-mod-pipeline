#!/usr/bin/env python3
"""Publish a paused-factory tester intake for the preserved Trailbound tuple."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORIES = json.loads(
    (ROOT / "FACTORY_REPOSITORY_ALLOCATION_REGISTRY.json").read_text(encoding="utf-8")
)
MAILBOX = Path(REPOSITORIES["mailbox_repository"]["path"])
MESSAGE_ID = "MSG-T09-TRAILBOUND-BDS-000001"
OUTPUT = ROOT / "EXISTING_CANDIDATE_TESTER_ROUTE_INTAKE.json"


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(MAILBOX), *args], text=True).strip()


def main() -> None:
    target = MAILBOX / "tester_intake" / "trailbound-packs" / f"{MESSAGE_ID}.json"
    if target.exists():
        raise SystemExit(f"intake already exists: {target}")
    message = {
        "schema_version": "1.0.0",
        "message_id": MESSAGE_ID,
        "message_type": "TESTER_INTAKE",
        "pack_id": "trailbound-packs",
        "sender_role": "T1_PORTFOLIO_SUPERVISOR",
        "recipient_role": "PERSISTENT_TESTER",
        "created_at": "2026-07-29T17:00:00Z",
        "source_authority_commit": "3cfcc28f7a15a8f31413b77ca0cbd6f3c137f5e5",
        "source_authority_tree": "f4dfc5db028a709bc89b588b57719ad78b215d8b",
        "candidate_generation": 2,
        "exact_artifact_hashes": {
            "behavior_pack": "f26e9daddfd7ba8893f6ccd5934b45ec0f88e1380b3e02038c13051d71fad8f3",
            "resource_pack": "14fcdba454ab5ca85381628d71845dadc80b9c255eb812b7aaebea84814ef7af",
            "mcaddon": "949fa581e930460a8bcc8e02f574d1bc89f848a754c57ec84907f07f27372bc4",
        },
        "parent_message_id": None,
        "required_action": "ROUTE_EXACT_PRESERVED_CANDIDATE_THROUGH_STABLE_DOCKER_BDS_ENTRYPOINT",
        "idempotency_key": hashlib.sha256(
            b"factory:trailbound:existing-candidate:stable-route:1"
        ).hexdigest(),
        "proof_boundary": [
            "EXACT_PACKAGE_ROUTE_VERIFICATION",
            "STABLE_BDS_ONLY",
            "NO_PRODUCT_MUTATION",
            "NO_CLIENT_AUDIO_CONTROLLER_MULTIPLAYER_OR_RELEASE_INFERENCE",
        ],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(message, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    git("add", str(target.relative_to(MAILBOX)))
    subprocess.check_call(
        [
            "git",
            "-C",
            str(MAILBOX),
            "-c",
            "user.name=Crazy Craft Factory Mailbox",
            "-c",
            "user.email=factory-mailbox@local.invalid",
            "commit",
            "-m",
            "test: route preserved Trailbound candidate to tester",
        ]
    )
    authority = {
        "mailbox_repository": str(MAILBOX),
        "message_id": MESSAGE_ID,
        "message_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "commit": git("rev-parse", "HEAD"),
        "tree": git("show", "-s", "--format=%T", "HEAD"),
        "candidate_mutated": False,
        "campaign_workers_started": False,
        "status": "PUBLISHED",
    }
    OUTPUT.write_text(json.dumps(authority, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
