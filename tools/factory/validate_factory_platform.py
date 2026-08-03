#!/usr/bin/env python3
"""Validate one exact factory-platform qualification receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from bedrock_factory.platform_authority import PlatformAuthorityError, validate_platform_qualification


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.receipt.read_text(encoding="utf-8"))
        validate_platform_qualification(document)
    except (OSError, json.JSONDecodeError, PlatformAuthorityError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "PASS", "qualification_id": document["qualification_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
