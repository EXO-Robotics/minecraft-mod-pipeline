#!/usr/bin/env python3
"""Validate an exact-candidate Stable/Preview BDS receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--mct-log", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--package-path", required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    if receipt.get("status") != "EXACT_CANDIDATE_STABLE_PREVIEW_BDS_QUALIFIED":
        fail("receipt is not fully qualified")
    if metadata.get("schema_version") != "1.0.0":
        fail("qualification metadata schema_version must be 1.0.0")
    candidate = receipt.get("candidate", {})
    commit = candidate.get("commit")
    expected = candidate.get("package_sha256")
    if not HEX40.fullmatch(str(commit or "")) or not HEX64.fullmatch(str(expected or "")):
        fail("candidate commit or package hash missing")
    metadata_candidate = metadata.get("candidate", {})
    if metadata_candidate.get("commit") != commit or metadata_candidate.get("package_sha256") != expected:
        fail("qualification metadata candidate binding mismatch")
    tree = metadata_candidate.get("tree")
    if not HEX40.fullmatch(str(tree or "")):
        fail("qualification metadata tree is invalid")
    resolved_tree = subprocess.run(
        ["git", "-C", str(args.repository), "rev-parse", f"{commit}^{{tree}}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if resolved_tree.returncode or resolved_tree.stdout.strip() != tree:
        fail("candidate tree mismatch")
    receipt_binding = metadata.get("receipt", {})
    if receipt_binding.get("sha256") != sha256(args.receipt):
        fail("qualification receipt hash mismatch")
    process = subprocess.run(
        ["git", "-C", str(args.repository), "show", f"{commit}:{args.package_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode:
        fail(process.stderr.decode(errors="replace").strip())
    if hashlib.sha256(process.stdout).hexdigest() != expected:
        fail("committed package hash mismatch")
    working = args.repository / args.package_path
    if not working.is_file() or sha256(working) != expected:
        fail("working package does not match receipt")
    deterministic = metadata.get("deterministic_rebuild", {})
    if deterministic.get("passed") is not True or deterministic.get("builds", 0) < 2:
        fail("deterministic two-build evidence missing")
    if deterministic.get("package_sha256") != expected:
        fail("deterministic rebuild package hash mismatch")
    mctools = metadata.get("mctools", {})
    if mctools.get("exit_code") != 0 or mctools.get("errors") != 0:
        fail("MCTools did not pass with zero errors")
    if not HEX64.fullmatch(str(mctools.get("log_sha256", ""))):
        fail("MCTools log hash missing")
    if not args.mct_log.is_file() or sha256(args.mct_log) != mctools.get("log_sha256"):
        fail("MCTools log bytes do not match metadata")
    architecture = metadata.get("architecture", {})
    for key in ("host", "docker_server", "image", "stable_binary", "preview_binary"):
        if not isinstance(architecture.get(key), str) or not architecture[key]:
            fail(f"architecture.{key} missing")
    if metadata.get("image") != receipt.get("runtime_profile", {}).get("image"):
        fail("image digest mismatch")
    script_policy = metadata.get("script_policy", {})
    require_script = script_policy.get("require_script_runtime")
    if not isinstance(require_script, bool):
        fail("explicit script policy missing")
    declared = {
        "stable": receipt.get("runtime_profile", {}).get("stable_restarts"),
        "preview": receipt.get("runtime_profile", {}).get("preview_restarts"),
    }
    for channel in ("stable", "preview"):
        row = receipt.get("channels", {}).get(channel, {})
        if row.get("qualified") is not True:
            fail(f"{channel} is not qualified")
        cycles = row.get("result", {}).get("execution", {}).get("cycles", [])
        if not isinstance(declared[channel], int) or len(cycles) != declared[channel]:
            fail(f"{channel} restart ledger length mismatch")
        for cycle in cycles:
            analysis = cycle.get("analysis", {})
            if cycle.get("passed") is not True:
                fail(f"{channel} cycle failed")
            if analysis.get("booted") is not True or analysis.get("clean") is not True:
                fail(f"{channel} cycle did not boot cleanly")
            if analysis.get("critical_lines"):
                fail(f"{channel} cycle has critical lines")
            if cycle.get("timed_out") is not False:
                fail(f"{channel} cycle timed out")
            if cycle.get("container_exit_code") != 0 or cycle.get("stop_exit_code") != 0:
                fail(f"{channel} cycle exit status is not clean")
            if require_script and analysis.get("script_initialized") is not True:
                fail(f"{channel} script marker missing")
        if row.get("validation_errors"):
            fail(f"{channel} has validation errors")
    claims = receipt.get("claims", {})
    for key in (
        "controller_verified", "multiplayer_verified", "physical_console_verified",
        "physical_ps4_verified", "real_client_verified",
        "real_player_gameplay_verified", "realm_verified",
        "split_screen_verified",
    ):
        if claims.get(key) is not False:
            fail(f"claim boundary must remain false: {key}")
    print(f"PASS exact BDS receipt commit={commit} package_sha256={expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
