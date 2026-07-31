#!/usr/bin/env python3
"""MacBook-side bounded submit/status/retrieve client.

No request field is evaluated as a command. SSH command construction uses a
closed role configuration and a validated monotonic job ID.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT))

from remote_job_lib import (  # noqa: E402
    ValidationError,
    disclosure_scan,
    ensure_job_root,
    locate_job,
    sha256_file,
    validate_input_manifest,
    validate_request,
)

ALLOWED_RETRIEVALS = {
    "result.json",
    "report.md",
    "receipt.json",
    "status.json",
}


def load_config(path: Path, role: str) -> dict:
    config = json.loads(path.read_text())
    entry = config["roles"][role]
    required = {"host_alias", "identity_file", "known_hosts_file", "remote_root"}
    if set(entry) != required:
        raise ValidationError("remote role configuration is not canonical")
    identity = Path(entry["identity_file"]).expanduser()
    known_hosts = Path(entry["known_hosts_file"]).expanduser()
    if not identity.is_file():
        raise ValidationError(f"dedicated identity unavailable: {identity}")
    if identity.stat().st_mode & 0o077:
        raise ValidationError("dedicated identity permissions too broad")
    if not known_hosts.is_file():
        raise ValidationError("pinned known-hosts file unavailable")
    return entry


def ssh_base(config: dict) -> list[str]:
    return [
        "ssh",
        "-T",
        "-o",
        "BatchMode=yes",
        "-o",
        "ForwardAgent=no",
        "-o",
        "ClearAllForwardings=yes",
        "-o",
        "PermitLocalCommand=no",
        "-o",
        "RequestTTY=no",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={Path(config['known_hosts_file']).expanduser()}",
        "-i",
        str(Path(config["identity_file"]).expanduser()),
        config["host_alias"],
    ]


def validate_local_bundle(bundle: Path, role: str) -> dict:
    if not bundle.is_dir() or bundle.is_symlink():
        raise ValidationError("job bundle must be a real directory")
    required = {"request.json", "request.sha256", "input-manifest.json", "inputs"}
    observed = {path.name for path in bundle.iterdir()}
    if observed != required:
        raise ValidationError(f"unexpected job bundle members: {sorted(observed)}")
    request = json.loads((bundle / "request.json").read_text())
    validate_request(request, expected_role=role)
    if request["job_id"] != bundle.name:
        raise ValidationError("bundle/job ID mismatch")
    if (bundle / "request.sha256").read_text().strip() != sha256_file(
        bundle / "request.json"
    ):
        raise ValidationError("request file hash mismatch")
    manifest = json.loads((bundle / "input-manifest.json").read_text())
    if manifest["job_id"] != request["job_id"]:
        raise ValidationError("manifest/request job mismatch")
    validate_input_manifest(manifest, bundle / "inputs")
    return request


def encode_transfer(bundle: Path) -> bytes:
    manifest = json.loads((bundle / "input-manifest.json").read_text())
    inputs = []
    for entry in manifest["entries"]:
        path = bundle / "inputs" / entry["relative_path"]
        inputs.append(
            {
                "relative_path": entry["relative_path"],
                "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
            }
        )
    payload = {
        "job_id": bundle.name,
        "request_json_base64": base64.b64encode(
            (bundle / "request.json").read_bytes()
        ).decode("ascii"),
        "request_sha256_base64": base64.b64encode(
            (bundle / "request.sha256").read_bytes()
        ).decode("ascii"),
        "input_manifest_base64": base64.b64encode(
            (bundle / "input-manifest.json").read_bytes()
        ).decode("ascii"),
        "inputs": inputs,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")


def local_submit(bundle: Path, root: Path, role: str, wait: bool) -> int:
    request = validate_local_bundle(bundle, role)
    ensure_job_root(root)
    if locate_job(root, request["job_id"]):
        raise ValidationError("duplicate job ID")
    destination = root / "incoming" / request["job_id"]
    shutil.copytree(bundle, destination, symlinks=False)
    entrypoint = MODULE_ROOT / "studio" / "remote_job_entrypoint.py"
    command = [
        sys.executable,
        str(entrypoint),
        "activate",
        role,
        request["job_id"],
        "--root",
        str(root),
        "--synthetic-test",
    ]
    if wait:
        return subprocess.run(command, check=False).returncode
    subprocess.Popen(command, start_new_session=True)
    return 0


def ssh_submit(bundle: Path, config_path: Path, role: str, wait: bool) -> int:
    request = validate_local_bundle(bundle, role)
    config = load_config(config_path, role)
    job_id = request["job_id"]
    ingest = ssh_base(config) + [
        "/usr/local/libexec/crazycraft-remote-entry",
        "ingest",
        role,
        job_id,
    ]
    subprocess.run(ingest, input=encode_transfer(bundle), check=True)
    activate = ssh_base(config) + [
        "/usr/local/libexec/crazycraft-remote-entry",
        "activate",
        role,
        job_id,
    ]
    if wait:
        return subprocess.run(activate, check=False).returncode
    subprocess.Popen(activate, start_new_session=True)
    return 0


def local_status(root: Path, job_id: str) -> int:
    found = locate_job(root, job_id)
    if not found:
        print(json.dumps({"job_id": job_id, "state": "NOT_FOUND"}))
        return 1
    state, path = found
    status = path / "status.json"
    print(status.read_text() if status.exists() else json.dumps({"job_id": job_id, "state": state.upper()}))
    return 0


def local_retrieve(root: Path, job_id: str, destination: Path, failed: bool = False) -> int:
    state = "failed" if failed else "completed"
    source = root / state / job_id
    if not source.is_dir():
        raise ValidationError(f"{state} job not found")
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in sorted(ALLOWED_RETRIEVALS):
        source_file = source / name
        if source_file.is_file():
            shutil.copy2(source_file, destination / name)
    artifacts = source / "artifacts"
    if artifacts.is_dir():
        shutil.copytree(artifacts, destination / "artifacts", symlinks=False)
    scan = disclosure_scan([destination])
    if scan["status"] != "PASS":
        shutil.rmtree(destination)
        raise ValidationError("retrieved result failed disclosure scan")
    receipt = destination / "receipt.json"
    if not receipt.is_file():
        shutil.rmtree(destination)
        raise ValidationError("retrieved result missing receipt")
    return 0


def decode_retrieval(encoded: bytes, destination: Path) -> int:
    import base64

    payload = json.loads(encoded.decode("ascii"))
    if set(payload) != {"job_id", "state", "files"}:
        raise ValidationError("retrieval framing mismatch")
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        for entry in payload["files"]:
            if set(entry) != {"relative_path", "content_base64"}:
                raise ValidationError("retrieval entry mismatch")
            relative = str(
                __import__("remote_job_lib").validate_safe_relative_path(
                    entry["relative_path"]
                )
            )
            top = relative.split("/", 1)[0]
            if top not in ALLOWED_RETRIEVALS | {"artifacts"}:
                raise ValidationError("retrieval path not allowlisted")
            path = destination / relative
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            data = base64.b64decode(entry["content_base64"], validate=True)
            descriptor = os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o400,
            )
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
        if disclosure_scan([destination])["status"] != "PASS":
            raise ValidationError("retrieved result failed disclosure scan")
        if not (destination / "receipt.json").is_file():
            raise ValidationError("retrieved result missing receipt")
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return 0


def ssh_operation(
    config_path: Path,
    role: str,
    operation: str,
    job_id: str,
    destination: Path | None = None,
) -> int:
    config = load_config(config_path, role)
    command = ssh_base(config) + [
        "/usr/local/libexec/crazycraft-remote-entry",
        operation,
        role,
        job_id,
    ]
    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        sys.stderr.buffer.write(completed.stderr)
        return completed.returncode
    if operation in {"fetch", "fetch-failure"}:
        return decode_retrieval(completed.stdout, destination)
    sys.stdout.buffer.write(completed.stdout)
    return 0


def local_cleanup(root: Path, job_id: str) -> int:
    found = locate_job(root, job_id)
    if not found:
        return 0
    state, path = found
    if state in {"incoming", "active"}:
        raise ValidationError("cannot cleanup nonterminal job")
    # Preserve receipt/result authority; cleanup removes artifacts only.
    artifacts = path / "artifacts"
    if artifacts.exists():
        shutil.rmtree(artifacts)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("validate", "submit", "status", "retrieve", "failure", "cleanup"))
    parser.add_argument("--role", choices=("T1", "T10"), required=True)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--job-id")
    parser.add_argument("--transport", choices=("local", "ssh"), default="ssh")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    if args.operation == "validate":
        validate_local_bundle(args.bundle, args.role)
        return 0
    if args.operation == "submit":
        if args.transport == "local":
            return local_submit(args.bundle, args.root, args.role, args.wait)
        return ssh_submit(args.bundle, args.config, args.role, args.wait)
    if args.transport == "ssh":
        operation = {
            "status": "status",
            "retrieve": "fetch",
            "failure": "fetch-failure",
            "cleanup": "cleanup",
        }[args.operation]
        return ssh_operation(
            args.config, args.role, operation, args.job_id, args.destination
        )
    if args.operation == "status":
        return local_status(args.root, args.job_id)
    if args.operation in {"retrieve", "failure"}:
        return local_retrieve(
            args.root,
            args.job_id,
            args.destination,
            failed=args.operation == "failure",
        )
    return local_cleanup(args.root, args.job_id)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"REMOTE_JOB_REJECTED: {exc}", file=sys.stderr)
        raise SystemExit(2)
