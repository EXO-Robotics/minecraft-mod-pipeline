from __future__ import annotations

import argparse
import json
import sys
from typing import TextIO

from mccompiler.operations.registry import OperationRegistry


def serve(input_stream: TextIO, output_stream: TextIO) -> int:
    registry = OperationRegistry()
    for raw in input_stream:
        if not raw.strip():
            continue
        try:
            request = json.loads(raw)
        except json.JSONDecodeError as exc:
            response = {
                "schema_version": "1.0.0", "request_id": None, "operation": "<invalid>",
                "ok": False, "project_revision": None, "result": None, "artifacts": [],
                "diagnostics": [{"severity": "error", "code": "INVALID_JSON", "message": str(exc)}],
            }
        else:
            response = registry.execute(request)
        output_stream.write(json.dumps(response, sort_keys=True, ensure_ascii=False) + "\n")
        output_stream.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mccompiler-agent", description="JSON-lines agent adapter")
    parser.parse_args(argv)
    return serve(sys.stdin, sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
