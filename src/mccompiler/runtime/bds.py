from __future__ import annotations

import hashlib
import json
import queue
import re
import shutil
import subprocess
import threading
import time
import tempfile
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
class BDSConsoleProbe:
    check_id: str
    cycle: int
    after_boot_seconds: float
    command: str
    expect_output: str


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
    restart_count: int = 1
    upgrade_mcworld: Path | None = None
    console_probes: tuple[BDSConsoleProbe, ...] = ()


def validate_console_probes(probes: tuple[BDSConsoleProbe, ...], *, restart_count: int, boot_grace_seconds: int) -> None:
    if len(probes) > 16:
        raise BDSDiagnosticError("console_probes cannot contain more than 16 checks")
    seen: set[str] = set()
    for probe in probes:
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", probe.check_id):
            raise BDSDiagnosticError(f"invalid console probe check_id: {probe.check_id}")
        if probe.check_id in seen:
            raise BDSDiagnosticError(f"duplicate console probe check_id: {probe.check_id}")
        seen.add(probe.check_id)
        if probe.cycle < 1 or probe.cycle > restart_count:
            raise BDSDiagnosticError(f"console probe {probe.check_id} has an invalid cycle")
        if probe.after_boot_seconds < 0 or probe.after_boot_seconds > max(0, boot_grace_seconds - 1):
            raise BDSDiagnosticError(f"console probe {probe.check_id} runs outside the boot grace window")
        if not probe.command or len(probe.command) > 512 or any(ord(char) < 32 for char in probe.command):
            raise BDSDiagnosticError(f"console probe {probe.check_id} has an invalid command")
        verb = probe.command.split(maxsplit=1)[0].lower()
        if verb not in {"setblock", "testforblock", "tickingarea"}:
            raise BDSDiagnosticError(f"console probe {probe.check_id} uses disallowed command: {verb}")
        if verb == "tickingarea" and not re.fullmatch(
            r"tickingarea add circle -?\d+ -?\d+ -?\d+ [12] [a-z0-9_-]{1,32} true",
            probe.command,
        ):
            raise BDSDiagnosticError(f"console probe {probe.check_id} uses an unbounded tickingarea command")
        if not probe.expect_output or len(probe.expect_output) > 512 or any(ord(char) < 32 for char in probe.expect_output):
            raise BDSDiagnosticError(f"console probe {probe.check_id} has invalid expected output")


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


def overlay_mcworld_packs(mcworld: Path, world_root: Path, *, expected_level_name: str) -> dict[str, Any]:
    """Replace only embedded packs and bindings while preserving the world database."""
    if not mcworld.is_file() or not zipfile.is_zipfile(mcworld):
        raise BDSDiagnosticError(f"Not a readable upgrade .mcworld archive: {mcworld}")
    managed_roots = {"behavior_packs", "resource_packs"}
    managed_files = {"world_behavior_packs.json", "world_resource_packs.json"}
    with tempfile.TemporaryDirectory(prefix="mccompiler-upgrade-", dir=world_root.parent) as temporary:
        stage = Path(temporary)
        with zipfile.ZipFile(mcworld) as archive:
            try:
                level_name = _safe_level_name(archive.read("levelname.txt").decode("utf-8", errors="strict"))
            except KeyError as exc:
                raise BDSDiagnosticError("The upgrade .mcworld is missing levelname.txt") from exc
            if level_name != expected_level_name:
                raise BDSDiagnosticError(f"Upgrade world name mismatch: expected {expected_level_name}, got {level_name}")
            for member in archive.infolist():
                relative = PurePosixPath(member.filename)
                if relative.is_absolute() or ".." in relative.parts:
                    raise BDSDiagnosticError(f"Unsafe path in upgrade .mcworld: {member.filename}")
                if not relative.parts or (relative.parts[0] not in managed_roots and relative.as_posix() not in managed_files):
                    continue
                target = stage.joinpath(*relative.parts)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as archive_source, target.open("wb") as output:
                    shutil.copyfileobj(archive_source, output)
        if not any((stage / root).is_dir() for root in managed_roots):
            raise BDSDiagnosticError("The upgrade .mcworld contains no embedded packs")
        inventory: list[dict[str, Any]] = []
        for root in sorted(managed_roots):
            source = stage / root
            target = world_root / root
            if target.exists():
                shutil.rmtree(target)
            if source.is_dir():
                shutil.copytree(source, target)
                inventory.extend({"path": path.relative_to(world_root).as_posix(), "sha256": sha256_file(path)} for path in sorted(target.rglob("*")) if path.is_file())
        for name in sorted(managed_files):
            source = stage / name
            target = world_root / name
            if source.is_file():
                shutil.copyfile(source, target)
                inventory.append({"path": name, "sha256": sha256_file(target)})
            elif target.exists():
                target.unlink()
        return {"artifact": {"path": str(mcworld), "sha256": sha256_file(mcworld)}, "files": inventory}


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
    if request.console_probes:
        command.insert(2, "-i")
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
    persistent_boot_values = [int(match.group(1)) for line in materialized if (match := re.search(r"persistent_boot=(\d+)", line))]
    migrated_lock_values = [int(match.group(1)) for line in materialized if (match := re.search(r"migration_nonempty_verified=(\d+)", line))]
    migrated_state_records = [int(match.group(1)) for line in materialized if (match := re.search(r"migration_state_records=(\d+)", line))]
    return {
        "booted": booted,
        "script_initialized": script_initialized,
        "clean": not errors,
        "critical_lines": errors,
        "bedrock_version": version,
        "bedrock_build_id": build_id,
        "persistent_boot_values": persistent_boot_values,
        "migrated_lock_values": migrated_lock_values,
        "migrated_state_records": migrated_state_records,
        "line_count": len(materialized),
    }


def _stream_lines(process: subprocess.Popen[str], output: queue.Queue[str | None]) -> None:
    assert process.stdout is not None
    try:
        for line in process.stdout:
            output.put(line.rstrip("\r\n"))
    finally:
        output.put(None)


def _run_cycle(request: BDSRunRequest, *, docker: str, data_root: Path, level_name: str, cycle: int) -> tuple[list[str], dict[str, Any]]:
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
    reader: threading.Thread | None = None
    cycle_probes = sorted(
        (probe for probe in request.console_probes if probe.cycle == cycle),
        key=lambda probe: (probe.after_boot_seconds, probe.check_id),
    )
    probe_results: list[dict[str, Any]] = []
    next_probe = 0
    try:
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        reader = threading.Thread(target=_stream_lines, args=(process, output), daemon=True)
        reader.start()
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
            if boot_seen_at is not None:
                since_boot = time.monotonic() - boot_seen_at
                while next_probe < len(cycle_probes) and cycle_probes[next_probe].after_boot_seconds <= since_boot:
                    probe = cycle_probes[next_probe]
                    result: dict[str, Any] = {
                        "check_id": probe.check_id,
                        "classification": "adapter_integration",
                        "command": probe.command,
                        "expect_output": probe.expect_output,
                        "sent": False,
                        "matched": False,
                        "line_start": len(lines),
                    }
                    try:
                        if process.stdin is None:
                            raise BrokenPipeError("BDS stdin is unavailable")
                        process.stdin.write(probe.command + "\n")
                        process.stdin.flush()
                        result["sent"] = True
                    except (BrokenPipeError, OSError) as error:
                        result["error"] = str(error)
                    probe_results.append(result)
                    next_probe += 1
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
        if reader is not None:
            reader.join(timeout=5)
        while True:
            try:
                item = output.get_nowait()
            except queue.Empty:
                break
            if item:
                lines.append(item)
        for index, result in enumerate(probe_results):
            line_end = int(probe_results[index + 1]["line_start"]) if index + 1 < len(probe_results) else len(lines)
            observed = lines[int(result["line_start"]):line_end]
            result["matched"] = bool(result["sent"] and any(str(result["expect_output"]) in line for line in observed))
            result["status"] = "PASSED" if result["matched"] else "FAILED"
            del result["line_start"]
    finally:
        subprocess.run([docker, "rm", "-f", container_name], capture_output=True, text=True, timeout=30, check=False)
    analysis = analyze_bds_log(lines)
    return lines, {
        "cycle": cycle,
        "timeout_seconds": request.timeout_seconds,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started_at, 3),
        "container_exit_code": process.returncode if process else None,
        "stop_exit_code": stop_result.returncode if stop_result else None,
        "analysis": analysis,
        "console_probes": probe_results,
        "passed": bool(
            analysis["booted"] and analysis["script_initialized"] and analysis["clean"] and not timed_out
            and len(probe_results) == len(cycle_probes) and all(bool(result["matched"]) for result in probe_results)
        ),
    }


def run_bds_diagnostic(request: BDSRunRequest) -> dict[str, Any]:
    if request.timeout_seconds < 10 or request.timeout_seconds > 900:
        raise BDSDiagnosticError("timeout_seconds must be between 10 and 900")
    if request.boot_grace_seconds < 0 or request.boot_grace_seconds > 30:
        raise BDSDiagnosticError("boot_grace_seconds must be between 0 and 30")
    if request.restart_count < 1 or request.restart_count > 3:
        raise BDSDiagnosticError("restart_count must be between 1 and 3")
    if request.upgrade_mcworld is not None and request.restart_count < 2:
        raise BDSDiagnosticError("upgrade_mcworld requires restart_count of at least 2")
    validate_console_probes(
        request.console_probes, restart_count=request.restart_count, boot_grace_seconds=request.boot_grace_seconds,
    )
    docker = shutil.which(request.docker_executable)
    if docker is None:
        raise BDSDiagnosticError(f"Docker executable is unavailable: {request.docker_executable}")
    request.run_root.mkdir(parents=True, exist_ok=False)
    data_root = request.run_root / "data"
    data_root.mkdir()
    level_name, world_root = extract_mcworld(request.mcworld, data_root)
    started_at = time.time()
    cycles: list[dict[str, Any]] = []
    combined_lines: list[str] = []
    upgrade: dict[str, Any] | None = None
    for cycle in range(1, request.restart_count + 1):
        lines, execution = _run_cycle(request, docker=docker, data_root=data_root, level_name=level_name, cycle=cycle)
        combined_lines.append(f"[mccompiler-harness] cycle={cycle}")
        combined_lines.extend(lines)
        cycles.append(execution)
        if not execution["passed"]:
            break
        if cycle == 1 and request.upgrade_mcworld is not None:
            upgrade = overlay_mcworld_packs(request.upgrade_mcworld, world_root, expected_level_name=level_name)
            combined_lines.append(f"[mccompiler-harness] upgrade={upgrade['artifact']['sha256']}")
    log_text = "\n".join(combined_lines) + ("\n" if combined_lines else "")
    log_path = request.run_root / "content.log"
    log_path.write_text(log_text, encoding="utf-8")
    analysis = analyze_bds_log(combined_lines)
    passed = len(cycles) == request.restart_count and all(bool(cycle["passed"]) for cycle in cycles)
    diagnostic_state_persistence_verified = bool(
        request.restart_count >= 2
        and analysis["persistent_boot_values"][:request.restart_count] == list(range(1, request.restart_count + 1))
    )
    nonempty_state_migration_verified = bool(request.upgrade_mcworld is not None and any(value > 0 for value in analysis["migrated_lock_values"]))
    migrated_state_restart_verified = bool(request.restart_count >= 3 and any(value > 0 for value in analysis["migrated_state_records"]))
    console_probe_results = [probe for cycle in cycles for probe in cycle["console_probes"]]
    adapter_integration_verified = bool(
        request.console_probes and len(console_probe_results) == len(request.console_probes)
        and all(probe["status"] == "PASSED" for probe in console_probe_results)
    )
    result = {
        "schema_version": "1.0.0",
        "status": "BDS_DIAGNOSTIC_BOOT_VERIFIED" if passed else "BDS_DIAGNOSTIC_FAILED",
        "passed": passed,
        "artifact": {"path": str(request.mcworld), "sha256": sha256_file(request.mcworld)},
        "runtime": {"adapter": "docker-bds", "image": request.image, "requested_bds_version": request.bds_version, "network": request.network_mode, "published_ports": False, "level_name": level_name},
        "execution": {"restart_count": request.restart_count, "elapsed_seconds": round(time.time() - started_at, 3), "cycles": cycles},
        "upgrade": upgrade,
        "log": {**analysis, "path": str(log_path), "sha256": hashlib.sha256(log_text.encode()).hexdigest()},
        "checks": console_probe_results,
        "claims": {"bds_boot_verified": passed, "adapter_integration_verified": adapter_integration_verified, "diagnostic_state_persistence_verified": diagnostic_state_persistence_verified, "nonempty_state_migration_verified": nonempty_state_migration_verified, "migrated_state_restart_verified": migrated_state_restart_verified, "gameplay_verified": False, "persistence_verified": False, "multiplayer_verified": False, "console_verified": False, "marketplace_approval_implied": False},
    }
    (request.run_root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
