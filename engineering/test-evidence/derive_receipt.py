#!/usr/bin/env python3
"""Derive a qualification receipt from captured observations and evidence files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_evidence_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe evidence path: {value!r}")
    return path


def require_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise ValueError(f"{label} missing keys: {', '.join(missing)}")


def derive(observation: dict[str, Any], evidence_root: Path) -> dict[str, Any]:
    require_keys(observation, {"schema", "candidate", "checks"}, "observation")
    if observation["schema"] != "aionbound.engineering-evidence-input.v1":
        raise ValueError("unsupported observation schema")
    if "status" in observation:
        raise ValueError("input may not supply an overall status")
    if not isinstance(observation["checks"], list) or not observation["checks"]:
        raise ValueError("at least one check is required")

    candidate = observation["candidate"]
    require_keys(candidate, {"id", "commit", "tree", "mcaddon_sha256"}, "candidate")
    derived_checks = []
    required_count = 0
    for index, check in enumerate(observation["checks"]):
        label = f"check[{index}]"
        require_keys(check, {"id", "required", "command", "exit_code", "assertions", "evidence_files"}, label)
        if "status" in check:
            raise ValueError(f"{label} may not supply status")
        if not isinstance(check["required"], bool):
            raise ValueError(f"{label}.required must be boolean")
        if not isinstance(check["command"], list) or not check["command"] or not all(isinstance(x, str) for x in check["command"]):
            raise ValueError(f"{label}.command must be a non-empty string array")
        if not isinstance(check["exit_code"], int):
            raise ValueError(f"{label}.exit_code must be an integer")
        if not isinstance(check["assertions"], list) or not check["assertions"]:
            raise ValueError(f"{label}.assertions must be non-empty")
        if not isinstance(check["evidence_files"], list) or not check["evidence_files"]:
            raise ValueError(f"{label}.evidence_files must be non-empty")

        assertions = []
        for assertion_index, assertion in enumerate(check["assertions"]):
            require_keys(assertion, {"name", "expected", "actual"}, f"{label}.assertions[{assertion_index}]")
            matched = assertion["actual"] == assertion["expected"]
            assertions.append({**assertion, "matched": matched})

        files = []
        for name in check["evidence_files"]:
            relative = relative_evidence_path(name)
            path = evidence_root.joinpath(*relative.parts)
            if not path.is_file():
                raise ValueError(f"missing evidence file: {relative.as_posix()}")
            files.append({"path": relative.as_posix(), "sha256": sha256(path), "size": path.stat().st_size})

        passed = check["exit_code"] == 0 and all(assertion["matched"] for assertion in assertions)
        if check["required"]:
            required_count += 1
        derived_checks.append({
            "id": check["id"],
            "required": check["required"],
            "command": check["command"],
            "exit_code": check["exit_code"],
            "assertions": assertions,
            "evidence_files": files,
            "status": "PASS" if passed else "FAIL",
        })

    if required_count == 0:
        raise ValueError("at least one required check is required")
    overall_pass = all(check["status"] == "PASS" for check in derived_checks if check["required"])
    return {
        "schema": "aionbound.engineering-evidence-receipt.v1",
        "candidate": candidate,
        "checks": derived_checks,
        "status": "PASS" if overall_pass else "FAIL",
        "status_basis": "derived from required check exit codes and assertion equality; evidence files are hash-bound",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    observation = json.loads(args.input.read_text())
    receipt = derive(observation, args.evidence_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
