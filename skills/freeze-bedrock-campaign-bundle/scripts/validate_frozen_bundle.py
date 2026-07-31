#!/usr/bin/env python3
"""Validate a slim frozen Bedrock campaign bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

REQUIRED_DIRS = (
    "behavior_pack", "resource_pack", "editable_assets", "contracts",
    "provenance", "qualification", "audits", "packages",
)
FORBIDDEN_NAMES = {"auth.json", "installation_id", ".hidden-canary", ".DS_Store"}
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
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    root = args.bundle.resolve()
    for name in REQUIRED_DIRS:
        if not (root / name).is_dir():
            fail(f"missing directory: {name}")
    if not (root / "FINAL_REPORT.md").is_file():
        fail("missing FINAL_REPORT.md")

    files = [path for path in root.rglob("*") if path.is_file()]
    if any(path.is_symlink() for path in root.rglob("*")):
        fail("bundle contains symlink")
    for path in files:
        if (
            path.name in FORBIDDEN_NAMES
            or path.suffix.lower() == ".jar"
            or ".private." in path.name.lower()
        ):
            fail(f"forbidden file: {path.relative_to(root)}")
        lowered = path.as_posix().lower()
        if "/node_modules/" in lowered or "/bds-seeds/" in lowered:
            fail(f"bulky generated tree: {path.relative_to(root)}")

    freeze_path = root / "provenance" / "candidate-freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for path in (root / "provenance").rglob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(value, sort_keys=True)
        if (
            "PRIVATE_EVIDENCE_ONLY" in serialized
            or '"may_transfer_to_production": false' in serialized
            or '"contains_source_identities": true' in serialized
        ):
            fail(f"private evidence metadata in bundle: {path.relative_to(root)}")
    package = freeze.get("combined_mcaddon", {})
    relative = package.get("path")
    expected = package.get("sha256")
    if not isinstance(relative, str) or not HEX64.fullmatch(str(expected or "")):
        fail("candidate package record invalid")
    package_path = root / relative
    if not package_path.is_file() or sha256(package_path) != expected:
        fail("candidate package hash mismatch")
    if freeze.get("qualification", {}).get("status") != "EXACT_CANDIDATE_STABLE_PREVIEW_BDS_QUALIFIED":
        fail("Stable/Preview qualification not frozen")
    metadata_path = root / "qualification" / "qualification-metadata.json"
    if not metadata_path.is_file():
        fail("qualification metadata missing")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata_candidate = metadata.get("candidate", {})
    if (
        metadata_candidate.get("commit") != freeze.get("qualification_commit")
        or metadata_candidate.get("tree") != freeze.get("git_tree")
        or metadata_candidate.get("package_sha256") != expected
    ):
        fail("qualification metadata candidate binding mismatch")
    if metadata.get("deterministic_rebuild", {}).get("passed") is not True:
        fail("deterministic rebuild not frozen")
    mctools = metadata.get("mctools", {})
    if mctools.get("exit_code") != 0 or mctools.get("errors") != 0:
        fail("MCTools zero-error pass not frozen")
    runtime_dir = root / "audits" / "final-runtime"
    visual_dir = root / "audits" / "final-visual"
    if not any(runtime_dir.iterdir()):
        fail("final runtime audit missing")
    if not any(visual_dir.iterdir()):
        fail("final visual audit missing")
    runtime_audits = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in runtime_dir.glob("*.json")
    ]
    if not runtime_audits or not any(
        audit.get("decision") == "PASS"
        and audit.get("severity_findings", {}).get("P0") == []
        and audit.get("severity_findings", {}).get("P1") == []
        for audit in runtime_audits
    ):
        fail("final runtime audit is not a zero-P0/P1 PASS")
    visual_audits = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in visual_dir.glob("*.json")
    ]
    if not visual_audits or not any(
        audit.get("verdict") == "GO"
        and audit.get("scores", {}).get("high_defects") == 0
        for audit in visual_audits
    ):
        fail("final visual audit is not a zero-high-defect GO")

    manifest = root / "MANIFEST.sha256"
    if not manifest.is_file():
        fail("MANIFEST.sha256 missing")
    checked = 0
    manifested: set[str] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        try:
            expected_hash, relative_path = line.split(None, 1)
        except ValueError:
            fail("malformed manifest line")
        relative_path = relative_path.removeprefix("*").removeprefix("./")
        target = root / relative_path
        if not target.is_file() or sha256(target) != expected_hash:
            fail(f"manifest mismatch: {relative_path}")
        manifested.add(relative_path)
        checked += 1
    if checked == 0:
        fail("manifest is empty")
    actual = {
        path.relative_to(root).as_posix()
        for path in files
        if path.name != "MANIFEST.sha256"
    }
    if manifested != actual:
        missing = sorted(actual - manifested)
        stale = sorted(manifested - actual)
        fail(f"manifest coverage mismatch missing={missing[:5]} stale={stale[:5]}")
    print(
        f"PASS frozen bundle files={len(files)} manifest_entries={checked} "
        f"package_sha256={expected}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
