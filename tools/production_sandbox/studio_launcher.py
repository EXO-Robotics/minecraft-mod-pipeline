#!/usr/bin/env python3
"""Launch a backend-neutral production worker inside a Studio-local sandbox."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path


ENTRYPOINT = Path(__file__).with_name("studio_entrypoint.py")
GIT = next(
    candidate
    for candidate in (
        Path("/opt/homebrew/bin/git"),
        Path("/Applications/Xcode.app/Contents/Developer/usr/bin/git"),
        Path("/usr/bin/git"),
    )
    if candidate.is_file()
)
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
REQUIRED_DENIALS = {"evidence", "control", "private_oracle", "canary"}


def sha256(target: Path) -> str:
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def git(repository: Path, *arguments: str) -> str:
    return subprocess.check_output(
        [str(GIT), *arguments],
        cwd=repository,
        text=True,
    ).strip()


def parse_denied_path(value: str) -> tuple[str, Path]:
    denied_class, separator, raw_path = value.partition("=")
    if not separator or denied_class not in REQUIRED_DENIALS or not raw_path:
        raise argparse.ArgumentTypeError(
            "--deny must be one of evidence=PATH, control=PATH, "
            "private_oracle=PATH, or canary=PATH"
        )
    target = Path(raw_path).expanduser()
    if not target.is_absolute():
        raise argparse.ArgumentTypeError("denied paths must be absolute")
    return denied_class, target.resolve()


def validate_policy_path(target: Path) -> str:
    resolved = str(target.resolve())
    if any(character in resolved for character in ('"', "\n", "\r")):
        raise ValueError("sandbox paths may not contain quotes or line breaks")
    return resolved


def render_profile(
    repository: Path,
    runtime: Path,
    launcher_root: Path,
    denied_paths: dict[str, Path],
) -> str:
    repository_text = validate_policy_path(repository)
    runtime_text = validate_policy_path(runtime)
    launcher_text = validate_policy_path(launcher_root)
    metadata_paths = {"/Applications", "/opt", "/opt/homebrew"}
    for root in (repository.resolve(), runtime.resolve(), launcher_root.resolve()):
        current = root
        while current != current.parent:
            metadata_paths.add(str(current))
            current = current.parent
    metadata_rules = "\n".join(
        f'  (literal "{target}")' for target in sorted(metadata_paths)
    )
    denied_rules = "\n".join(
        f'(deny file-read* (subpath "{validate_policy_path(target)}"))\n'
        f'(deny file-write* (subpath "{validate_policy_path(target)}"))'
        for target in denied_paths.values()
    )
    return f"""(version 1)
(deny default)
(import "system.sb")
(allow process-fork)
(allow file-ioctl)
(allow process-exec
  (subpath "/bin")
  (subpath "/usr/bin")
  (subpath "/usr/sbin")
  (subpath "/opt/homebrew")
  (subpath "/Applications/Xcode.app"))
(allow file-read*
  (subpath "/System")
  (subpath "/usr")
  (subpath "/bin")
  (subpath "/sbin")
  (subpath "/opt/homebrew")
  (subpath "/private/etc")
  (subpath "/private/var/select")
  (subpath "/var/select")
  (subpath "/dev")
  (subpath "/Applications/Xcode.app")
  (subpath "{repository_text}")
  (subpath "{runtime_text}")
  (subpath "{launcher_text}"))
(allow file-read-metadata
{metadata_rules})
(allow file-read-data
{metadata_rules})
(allow file-write*
  (subpath "{repository_text}")
  (subpath "{runtime_text}"))
(deny file-write*
  (literal "{runtime_text}/assignment.json")
  (literal "{runtime_text}/environment-manifest.json")
  (literal "{runtime_text}/studio-entrypoint.py")
  (literal "{runtime_text}/studio-production.sb"))
{denied_rules}
; Studio production is offline by default.
(deny network*)
"""


def initialize_repository(
    repository: Path,
    *,
    base_repository: Path | None,
    inputs: list[tuple[str, Path]],
) -> tuple[str, str, list[dict[str, object]]]:
    if base_repository is None:
        repository.mkdir(parents=True)
        subprocess.run(
            [str(GIT), "init", "-q", "--initial-branch=main"],
            cwd=repository,
            check=True,
        )
    else:
        subprocess.run(
            [
                str(GIT),
                "clone",
                "-q",
                "--no-local",
                str(base_repository.resolve()),
                str(repository),
            ],
            check=True,
        )
        subprocess.run(
            [str(GIT), "remote", "remove", "origin"],
            cwd=repository,
            check=True,
        )
    subprocess.run(
        [str(GIT), "config", "user.name", "Studio Production Worker"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        [str(GIT), "config", "user.email", "studio-production@invalid"],
        cwd=repository,
        check=True,
    )
    input_root = repository / "inputs"
    input_root.mkdir(exist_ok=True)
    transferred: list[dict[str, object]] = []
    for index, (input_class, source) in enumerate(inputs, start=1):
        source = source.resolve()
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"approved input must be a regular file: {source}")
        destination = input_root / f"{index:02d}-{input_class}{source.suffix}"
        shutil.copy2(source, destination)
        transferred.append(
            {
                "class": input_class,
                "path": destination.relative_to(repository).as_posix(),
                "sha256": sha256(destination),
                "size": destination.stat().st_size,
                "source_path_sha256": sha256_bytes(str(source).encode()),
            }
        )
    readme = repository / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Studio clean-room production lane\n\n"
            "Only the hash-bound files under `inputs/` are approved context.\n",
            encoding="utf-8",
        )
    subprocess.run(
        [str(GIT), "add", "README.md", "inputs"],
        cwd=repository,
        check=True,
    )
    if git(repository, "status", "--porcelain"):
        subprocess.run(
            [str(GIT), "commit", "-q", "-m", "Freeze Studio production inputs"],
            cwd=repository,
            check=True,
        )
    return (
        git(repository, "rev-parse", "HEAD"),
        git(repository, "rev-parse", "HEAD^{tree}"),
        transferred,
    )


def inventory(repository: Path) -> tuple[list[dict[str, object]], list[str]]:
    files: list[dict[str, object]] = []
    hazards: list[str] = []
    for target in sorted(repository.rglob("*")):
        if ".git" in target.parts:
            continue
        mode = target.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            hazards.append(target.relative_to(repository).as_posix())
        elif stat.S_ISREG(mode):
            files.append(
                {
                    "path": target.relative_to(repository).as_posix(),
                    "sha256": sha256(target),
                    "size": target.stat().st_size,
                }
            )
    return files, hazards


def verify_transferred_inputs(
    repository: Path,
    transferred: list[dict[str, object]],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for expected in transferred:
        target = repository / str(expected["path"])
        actual = sha256(target) if target.is_file() and not target.is_symlink() else None
        results.append(
            {
                "path": expected["path"],
                "expected_sha256": expected["sha256"],
                "actual_sha256": actual,
                "match": actual == expected["sha256"],
            }
        )
    return results


def postflight_isolation(repository: Path) -> dict[str, object]:
    git_directory = Path(
        git(repository, "rev-parse", "--path-format=absolute", "--git-common-dir")
    )
    alternates = git_directory / "objects/info/alternates"
    symlinks = [
        path.relative_to(repository).as_posix()
        for path in repository.rglob("*")
        if path.is_symlink() and ".git" not in path.parts
    ]
    hardlinks = [
        path.relative_to(git_directory).as_posix()
        for path in (git_directory / "objects").rglob("*")
        if path.is_file() and path.stat().st_nlink > 1
    ]
    return {
        "remotes_absent": git(repository, "remote") == "",
        "alternates_absent": not alternates.exists(),
        "cross_lane_symlinks_absent": not symlinks,
        "hardlinks_absent": not hardlinks,
        "symlinks": symlinks,
        "hardlinks": hardlinks,
    }


def scan_forbidden_material(
    roots: list[Path],
    *,
    canary: Path,
) -> dict[str, object]:
    forbidden_names = {
        "auth.json",
        "credentials.json",
        ".env",
        "installation_id",
    }
    forbidden_tokens = (
        b"OPENAI_API_KEY",
        b"GITHUB_TOKEN",
        b"RESTRICTED_REHEARSAL_CANARY",
    )
    canary_hash = sha256(canary) if canary.is_file() else None
    name_matches: list[str] = []
    token_matches: list[str] = []
    hash_matches: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for target in root.rglob("*"):
            if not target.is_file() or target.is_symlink():
                continue
            relative = f"{root.name}/{target.relative_to(root)}"
            if target.name.lower() in forbidden_names:
                name_matches.append(relative)
            if target.stat().st_size <= 8 * 1024 * 1024:
                payload = target.read_bytes()
                if any(token in payload for token in forbidden_tokens):
                    token_matches.append(relative)
            if canary_hash is not None and sha256(target) == canary_hash:
                hash_matches.append(relative)
    return {
        "name_matches": sorted(name_matches),
        "token_matches": sorted(token_matches),
        "hash_matches": sorted(hash_matches),
        "clean": not name_matches and not token_matches and not hash_matches,
    }


def parse_worker_command(command_file: Path) -> list[str]:
    command = json.loads(command_file.read_text(encoding="utf-8"))
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(part, str) and part for part in command)
    ):
        raise ValueError("worker command file must contain a non-empty argv array")
    executable = Path(command[0]).expanduser()
    if not executable.is_absolute():
        raise ValueError("worker command executable must be absolute")
    command[0] = str(executable.resolve())
    return command


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Launch a Studio-local clean-room production worker."
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--assignment", type=Path, required=True)
    parser.add_argument("--sanitized-contract", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--worker-command", type=Path, required=True)
    parser.add_argument("--platform-qualification", type=Path, required=True)
    parser.add_argument("--platform-qualification-sha256", required=True)
    parser.add_argument("--base-repo", type=Path)
    parser.add_argument("--deny", action="append", type=parse_denied_path, default=[])
    args = parser.parse_args()

    denied_paths = dict(args.deny)
    if set(denied_paths) != REQUIRED_DENIALS:
        missing = sorted(REQUIRED_DENIALS - set(denied_paths))
        raise SystemExit(f"all four denial classes are required; missing: {missing}")
    run_root = args.run_root.expanduser().resolve()
    if run_root.exists():
        raise SystemExit(f"run root must be fresh: {run_root}")
    assignment_source = args.assignment.expanduser().resolve()
    contract_source = args.sanitized_contract.expanduser().resolve()
    prompt_source = args.prompt.expanduser().resolve()
    worker_command_source = args.worker_command.expanduser().resolve()
    platform_qualification = args.platform_qualification.expanduser().resolve()
    if not platform_qualification.is_file():
        raise SystemExit("platform qualification receipt is missing")
    platform_qualification_sha256 = sha256(platform_qualification)
    if platform_qualification_sha256 != args.platform_qualification_sha256:
        raise SystemExit("platform qualification receipt hash mismatch")
    platform_document = json.loads(platform_qualification.read_text(encoding="utf-8"))
    if platform_document.get("status") != "PASS":
        raise SystemExit("platform qualification receipt is not PASS")
    worker_command = parse_worker_command(worker_command_source)
    repository = run_root / "repo"
    runtime = run_root / "runtime"
    for target in (
        runtime / "home",
        runtime / "tmp",
        runtime / "cache",
        runtime / "logs",
    ):
        target.mkdir(parents=True, exist_ok=True)
    baseline_commit, baseline_tree, transferred = initialize_repository(
        repository,
        base_repository=(
            args.base_repo.expanduser().resolve() if args.base_repo else None
        ),
        inputs=[
            ("assignment", assignment_source),
            ("contract", contract_source),
            ("prompt", prompt_source),
        ],
    )
    assignment_document = json.loads(
        assignment_source.read_text(encoding="utf-8")
    )
    if assignment_document.get("schema_version") != "1.0.0":
        raise SystemExit("assignment schema_version must be 1.0.0")
    if not assignment_document.get("assignment_id"):
        raise SystemExit("assignment_id is required")
    if assignment_document.get("role") not in {
        "feature_producer",
        "visual_producer",
        "segment_integrator",
        "repair_agent",
    }:
        raise SystemExit("assignment role is not a production role")
    assignment_payload = {
        "schema_version": "1.0.0",
        "assignment_id": assignment_document["assignment_id"],
        "denied_paths": [
            {"class": denied_class, "path": str(target)}
            for denied_class, target in sorted(denied_paths.items())
        ],
        "transferred_inputs": transferred,
        "baseline_commit": baseline_commit,
        "baseline_tree": baseline_tree,
    }
    assignment_path = runtime / "assignment.json"
    assignment_path.write_text(
        json.dumps(assignment_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    entrypoint_path = runtime / "studio-entrypoint.py"
    shutil.copy2(ENTRYPOINT, entrypoint_path)
    profile_path = runtime / "studio-production.sb"
    profile_path.write_text(
        render_profile(repository, runtime, runtime, denied_paths),
        encoding="utf-8",
    )
    environment_manifest = {
        "schema_version": "1.0.0",
        "host_role": "STUDIO_PRODUCTION_HOST",
        "network_policy": "DENY_ALL",
        "authentication_policy": "NO_AUTHENTICATION_FILES_EXPOSED",
        "worker_command_sha256": sha256(worker_command_source),
        "python": sys.version.split()[0],
        "git": subprocess.check_output(
            [str(GIT), "--version"], text=True
        ).strip(),
    }
    environment_path = runtime / "environment-manifest.json"
    environment_path.write_text(
        json.dumps(environment_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    environment = {
        "HOME": str(runtime / "home"),
        "TMPDIR": str(runtime / "tmp"),
        "XDG_CACHE_HOME": str(runtime / "cache"),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "PATH": (
            "/Applications/Xcode.app/Contents/Developer/usr/bin:"
            "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        ),
        "STUDIO_PRODUCTION_REPOSITORY": str(repository),
        "STUDIO_PRODUCTION_RUNTIME": str(runtime),
        "STUDIO_ASSIGNMENT": str(assignment_path),
        "STUDIO_GIT": str(GIT),
        "STUDIO_WORKER_COMMAND_JSON": json.dumps(worker_command),
        "STUDIO_PLATFORM_QUALIFIED": "1",
    }
    command = [
        str(SANDBOX_EXEC),
        "-f",
        str(profile_path),
        "/usr/bin/env",
        "-i",
        *[f"{key}={value}" for key, value in environment.items()],
        str(Path(sys.executable).resolve()),
        str(entrypoint_path),
    ]
    events_path = runtime / "logs/events.jsonl"
    stderr_path = runtime / "logs/stderr.log"
    with events_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.run(
            command,
            cwd=repository,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    input_postflight = verify_transferred_inputs(repository, transferred)
    shutil.rmtree(runtime / "cache", ignore_errors=True)
    assignment_id = assignment_payload["assignment_id"]
    attestation = {
        "schema_version": "bedrock-factory.activation-attestation.v1.0.0",
        "activation_id": assignment_document.get("activation_id", assignment_id),
        "assignment_sha256": sha256(assignment_source),
        "platform_qualification_sha256": platform_qualification_sha256,
        "repository_ref": git(repository, "symbolic-ref", "HEAD"),
        "exit_code": process.returncode,
        "cleanup_status": "PASS" if not (runtime / "cache").exists() else "FAIL",
    }
    if isinstance(assignment_document.get("candidate_id"), str):
        attestation["candidate_id"] = assignment_document["candidate_id"]
    attestation_path = runtime / "activation-attestation.json"
    attestation_path.write_text(
        json.dumps(attestation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    accepted = (
        process.returncode == 0
        and all(row["match"] for row in input_postflight)
        and git(repository, "status", "--porcelain") == ""
        and attestation["cleanup_status"] == "PASS"
    )
    print(
        json.dumps(
            {
                "status": "PASS" if accepted else "FAIL",
                "host_role": "STUDIO_PRODUCTION_HOST",
                "activation_attestation": str(attestation_path),
                "exit_status": process.returncode,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if accepted else (process.returncode or 96)


if __name__ == "__main__":
    raise SystemExit(main())
