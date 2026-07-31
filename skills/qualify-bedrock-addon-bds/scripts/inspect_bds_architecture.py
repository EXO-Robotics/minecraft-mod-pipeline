#!/usr/bin/env python3
"""Report host, Docker, image, and BDS binary architectures."""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
from pathlib import Path


def run(*args: str) -> tuple[int, str]:
    process = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return process.returncode, process.stdout.strip()


def inspect_binary(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"missing file: {path}"
    rc, output = run("file", str(path))
    lowered = output.lower()
    ok = rc == 0 and "cannot open" not in lowered and "no such file" not in lowered
    return ok, output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--stable-binary", type=Path, required=True)
    parser.add_argument("--preview-binary", type=Path, required=True)
    args = parser.parse_args()
    docker_rc, docker_arch = run(
        "docker", "version", "--format",
        "{{.Server.Arch}} {{.Server.Os}}",
    )
    image_rc, image_arch = run(
        "docker", "image", "inspect", args.image,
        "--format", "{{.Architecture}} {{.Os}}",
    )
    stable_ok, stable_file = inspect_binary(args.stable_binary)
    preview_ok, preview_file = inspect_binary(args.preview_binary)
    result = {
        "schema_version": "1.0.0",
        "host": {"machine": platform.machine(), "system": platform.system()},
        "docker_server": {"ok": docker_rc == 0, "value": docker_arch},
        "image": {"reference": args.image, "ok": image_rc == 0, "value": image_arch},
        "stable_binary": {"path": str(args.stable_binary), "ok": stable_ok, "file": stable_file},
        "preview_binary": {"path": str(args.preview_binary), "ok": preview_ok, "file": preview_file},
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    return 0 if all((docker_rc == 0, image_rc == 0, stable_ok, preview_ok)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
