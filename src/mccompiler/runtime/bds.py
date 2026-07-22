from __future__ import annotations

import hashlib
import json
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


_SAFE_LEVEL = re.compile(r"[^A-Za-z0-9._ -]+")
_BOOT_MARKERS = ("Server started.", "Server started")
_SCRIPT_MARKERS = ("runtime initialized", "script runtime initialized")
_ERROR_MARKERS = ("[error]", "error:", "error ", "syntaxerror", "failed to load", "uncaught exception")


class BDSDiagnosticError(RuntimeError):
    pass


@dataclass(frozen=True)
class BDSRunRequest:
    image: str
    mcworld: Path
    run_root: Path
    timeout_seconds: int = 120
    boot_grace_seconds: int = 15
    docker_executable: str = "docker"
    network_mode: str = "none"
    bds_version: str | None = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_level_name(raw: str) -> str:
    value = _SAFE_LEVEL.sub("_", raw.strip()).strip(". ")
    if not value:
        raise BDSDiagnosticError("The .mcworld has an empty or unsafe level name")
    return value[:64]


def extract_mcworld(mcworld: Path, data_root: Path) -> tuple[str, Path]:
    """Extract a generated world without allowing archive path traversal."""
    if not mcworld.is_file() or not zipfile.is_zipfile(mcworld):
        raise BDSDiagnosticError(f"Not a readable .mcworld archive: {mcworld}")
    with zipfile.ZipFile(mcworld) as archive:
        try:
            level_name = _safe_level_name(archive.read("levelname.txt").decode("utf-8", errors="strict"))
        except KeyError as exc:
            raise BDSDiagnosticError("The .mcworld is missing levelname.txt") from exc
        destination = data_root / "worlds" / level_name
        destination.mkdir(parents=True, exist_ok=False)
        for member in archive.infolist():
            relative = PurePosixPath(member.filename)
            if relative.is_absolute() or ".." in relative.parts:
                raise BDSDiagnosticError(f"Unsafe path in .mcworld: {member.filename}")
            target = destination.joinpath(*relative.parts)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    return level_name, destination


def docker_run_command(request: BDSRunRequest, *, container_name: str, data_root: Path, level_name: str) -> list[str]:
    if request.network_mode not in {"none", "bridge"}:
        raise BDSDiagnosticError("network_mode must be none or bridge")
    command = [
        request.docker_executable, "run", "--name", container_name, "--rm", "--pull", "never",
        "--network", request.network_mode, "--mount", f"type=bind,src={data_root},dst=/data",
        "-e", "EULA=TRUE", "-e", f"LEVEL_NAME={level_name}", "-e", "ONLINE_MODE=false",
        "-e", "ALLOW_LIST=false", "-e", "WHITE_LIST=false",
        "-e", "CONTENT_LOG_CONSOLE_OUTPUT_ENABLED=true",
        "-e", "SERVER_PORT=19132", "-e", "SERVER_PORT_V6=19133",
    ]
    if request.bds_version:
        command.extend(("-e", f"VERSION={request.bds_version}"))
    command.append(request.image)
    return command


def analyze_bds_log(lines: Iterable[str]) -> dict[str, Any]:
    materialized = list(lines)
    lowered = [line.lower() for line in materialized]
    booted = any(any(marker.lower() in line for marker in _BOOT_MARKERS) for line in lowered)
    script_initialized = any(any(marker in line for marker in _SCRIPT_MARKERS) for line in lowered)
    errors = [line for line in materialized if any(marker in line.lower() for marker in _ERROR_MARKERS)]
    version = next((match.group(1) for line in materialized if (match := re.search(r"Version:\s*([^\s]+)", line))), None)
    build_id = next((match.group(1) for line in materialized if (match := re.search(r"Build Id:\s*([^\s]+)", line, re.I))), None)
    return {
        "booted": booted,
        "script_initialized": script_initialized,
        "clean": not errors,
        "critical_lines": errors,
        "bedrock_version": version,
        "bedrock_build_id": build_id,
        "line_count": len(materialized),
    }


def _stream_lines(process: subprocess.Popen[str], output: queue.Queue[str | None]) -> None:
    assert process.stdout is not None
    try:
        for line in process.stdout:
            output.put(line.rstrip("\r\n"))
    finally:
        output.put(None)


def run_bds_diagnostic(request: BDSRunRequest) -> dict[str, Any]:
    if request.timeout_seconds < 10 or request.timeout_seconds > 900:
        raise BDSDiagnosticError("timeout_seconds must be between 10 and 900")
    if request.boot_grace_seconds < 0 or request.boot_grace_seconds > 30:
        raise BDSDiagnosticError("boot_grace_seconds must be between 0 and 30")
    docker = shutil.which(request.docker_executable)
    if docker is None:
        raise BDSDiagnosticError(f"Docker executable is unavailable: {request.docker_executable}")
    request.run_root.mkdir(parents=True, exist_ok=False)
    data_root = request.run_root / "data"
    data_root.mkdir()
    level_name, _ = extract_mcworld(request.mcworld, data_root)
    container_name = f"mccompiler-bds-{uuid.uuid4().hex[:12]}"
    command = docker_run_command(request, container_name=container_name, data_root=data_root, level_name=level_name)
    command[0] = docker
    started_at = time.time()
    lines: list[str] = []
    output: queue.Queue[str | None] = queue.Queue()
    process: subprocess.Popen[str] | None = None
    stop_result: subprocess.CompletedProcess[str] | None = None
    timed_out = False
    boot_seen_at: float | None = None
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)
        threading.Thread(target=_stream_lines, args=(process, output), daemon=True).start()
        deadline = time.monotonic() + request.timeout_seconds
        stream_done = False
        while time.monotonic() < deadline:
            try:
                item = output.get(timeout=0.25)
            except queue.Empty:
                item = ""
            if item is None:
                stream_done = True
            elif item:
                lines.append(item)
                if boot_seen_at is None and any(marker.lower() in item.lower() for marker in _BOOT_MARKERS):
                    boot_seen_at = time.monotonic()
            if boot_seen_at is not None and time.monotonic() - boot_seen_at >= request.boot_grace_seconds:
                break
            if stream_done and process.poll() is not None:
                break
        else:
            timed_out = True
        stop_result = subprocess.run([docker, "stop", "--timeout", "20", container_name], capture_output=True, text=True, timeout=30, check=False)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        while True:
            try:
                item = output.get_nowait()
            except queue.Empty:
                break
            if item:
                lines.append(item)
    finally:
        subprocess.run([docker, "rm", "-f", container_name], capture_output=True, text=True, timeout=30, check=False)

    log_text = "\n".join(lines) + ("\n" if lines else "")
    log_path = request.run_root / "content.log"
    log_path.write_text(log_text, encoding="utf-8")
    analysis = analyze_bds_log(lines)
    passed = bool(analysis["booted"] and analysis["script_initialized"] and analysis["clean"] and not timed_out)
    result = {
        "schema_version": "1.0.0",
        "status": "BDS_DIAGNOSTIC_BOOT_VERIFIED" if passed else "BDS_DIAGNOSTIC_FAILED",
        "passed": passed,
        "artifact": {"path": str(request.mcworld), "sha256": sha256_file(request.mcworld)},
        "runtime": {"adapter": "docker-bds", "image": request.image, "requested_bds_version": request.bds_version, "network": request.network_mode, "published_ports": False, "level_name": level_name},
        "execution": {"timeout_seconds": request.timeout_seconds, "timed_out": timed_out, "elapsed_seconds": round(time.time() - started_at, 3), "container_exit_code": process.returncode if process else None, "stop_exit_code": stop_result.returncode if stop_result else None},
        "log": {**analysis, "path": str(log_path), "sha256": hashlib.sha256(log_text.encode()).hexdigest()},
        "claims": {"bds_boot_verified": passed, "gameplay_verified": False, "persistence_verified": False, "multiplayer_verified": False, "console_verified": False, "marketplace_approval_implied": False},
    }
    (request.run_root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
