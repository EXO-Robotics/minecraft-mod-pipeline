from __future__ import annotations

import argparse
import json
from pathlib import Path

from mccompiler.runtime.gametest import augment_mcworld_with_gametest_pack


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC_PACK = ROOT / "benchmarks/rights-cleared-java-mod/reconstruction/diagnostic/simulated-player"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the preview-only Benchmark B simulated-player diagnostic world")
    parser.add_argument("--project", type=Path, required=True, help="Generated Benchmark B conversion project")
    parser.add_argument(
        "--source-world", default="dist/test-world/generated-test-world.mcworld",
        help="Project-relative source .mcworld (defaults to the production generated world)",
    )
    parser.add_argument("--output", type=Path, required=True, help="Destination .mcworld; must differ from the production world")
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    source = (project / args.source_world).resolve()
    if project not in source.parents:
        raise ValueError("--source-world must remain inside the conversion project")
    result = augment_mcworld_with_gametest_pack(source, DIAGNOSTIC_PACK, args.output.expanduser().resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
