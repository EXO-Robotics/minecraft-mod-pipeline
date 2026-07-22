from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .bedrock import ARCHIVE_NAME, _zip_deterministic, compile_bedrock
from .io import write_json
from .planner import plan_conversion
from .overrides import apply_overrides, load_overrides
from .schema import validate_ir
from .scan import scan_path
from .validate import validate_output


def _scan_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", required=True, help="Mod JAR, source directory, or modpack directory")
    parser.add_argument("--output", required=True, help="JSON path or output directory")
    parser.add_argument("--bedrock-server", help="Optional Bedrock server root to use as a read-only target profile")
    parser.add_argument("--overrides", help="Persistent compiler override JSON")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mccompiler")
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan", help="Scan input into ModIR")
    _scan_args(scan_parser)
    compile_parser = sub.add_parser("compile", help="Scan, plan, and generate a Bedrock scaffold")
    _scan_args(compile_parser)
    validate_parser = sub.add_parser("validate", help="Validate generated packs")
    validate_parser.add_argument("--path", required=True)
    validate_parser.add_argument(
        "--runtime", action="store_true",
        help="Require and validate reports/runtime-evidence.json",
    )
    validate_parser.add_argument("--record", action="store_true", help="Record validation layers in conversion reports and rebuild the deterministic archive")
    args = parser.parse_args(argv)

    if args.command == "validate":
        result = validate_output(args.path, runtime=args.runtime)
        if args.record:
            root = Path(args.path).expanduser().resolve()
            if root.is_file():
                root = root.parent
            report_path = root / "reports/conversion-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["validation"] = json.loads(json.dumps(result["layers"]).replace(str(root), "."))
            report["result"] = "validated" if result["valid"] else "validation_failed"
            write_json(report_path, report)
            markdown = root / "reports/conversion-report.md"
            base = markdown.read_text(encoding="utf-8").split("\n## Validation results\n", 1)[0].rstrip()
            statuses = [f"- {name.title()}: **{layer.get('status', 'unknown')}**" for name, layer in result["layers"].items()]
            markdown.write_text(base + "\n\n## Validation results\n\n" + "\n".join(statuses) + "\n", encoding="utf-8")
            _zip_deterministic(root, root / ARCHIVE_NAME)
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1

    ir = scan_path(args.input, args.bedrock_server)
    try:
        apply_overrides(ir, load_overrides(args.overrides))
    except ValueError as exc:
        print(f"Override error: {exc}", file=sys.stderr)
        return 2
    schema_errors = validate_ir(ir)
    if schema_errors:
        ir.setdefault("errors", []).extend(schema_errors)
    if args.command == "scan":
        write_json(Path(args.output), ir)
        print(f"Wrote ModIR: {args.output}")
        return 1 if ir.get("errors") else 0

    plan = plan_conversion(ir)
    archive = compile_bedrock(ir, plan, args.output)
    print(f"Wrote deterministic add-on: {archive}")
    print(f"Technical similarity estimate: {plan['scores']['technical_similarity']:.0%}")
    print(f"Gameplay fidelity estimate: {plan['scores']['gameplay_fidelity']:.0%}")
    return 1 if ir.get("errors") else 0


if __name__ == "__main__":
    sys.exit(main())
