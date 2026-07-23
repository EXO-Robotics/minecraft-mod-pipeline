#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mccompiler.runtime.gametest import augment_mcworld_with_gametest_pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Preview-only SimulatedPlayer diagnostic world")
    parser.add_argument("--project", type=Path, required=True, help="Generated conversion project")
    parser.add_argument("--source-world", required=True, help="Project-relative source .mcworld")
    parser.add_argument("--diagnostic-pack", type=Path, required=True, help="Diagnostic behavior-pack directory")
    parser.add_argument("--output", type=Path, required=True, help="Destination .mcworld")
    parser.add_argument(
        "--diagnostic-server-version",
        help="Preview-only @minecraft/server version overlay for embedded production packs",
    )
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    source = (project / args.source_world).resolve()
    if project not in source.parents:
        raise ValueError("--source-world must remain inside the conversion project")
    result = augment_mcworld_with_gametest_pack(
        source, args.diagnostic_pack.expanduser().resolve(), args.output.expanduser().resolve(),
        diagnostic_server_version=args.diagnostic_server_version,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
