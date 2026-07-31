#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from remote_job_lib import ValidationError, validate_input_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("input_root", type=Path)
    args = parser.parse_args()
    try:
        validate_input_manifest(json.loads(args.manifest.read_text()), args.input_root)
    except (ValidationError, json.JSONDecodeError, OSError) as exc:
        print(f"HASH_MANIFEST_FAIL: {exc}", file=sys.stderr)
        return 1
    print("HASH_MANIFEST_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
