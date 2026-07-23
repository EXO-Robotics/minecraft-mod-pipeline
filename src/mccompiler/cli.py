from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .bedrock import ARCHIVE_NAME, _zip_deterministic, compile_bedrock
from .io import write_json
from .planner import plan_conversion
from .overrides import apply_overrides, load_overrides
from .schema import validate_ir
from .scan import scan_path
from .validate import validate_output


MILESTONE_COMMANDS = {
    "create-rights-strategy": "create_rights_strategy",
    "register-rights-material": "register_rights_material",
    "inspect-rights-material": "inspect_rights_material",
    "build-gameplay-intent": "build_gameplay_intent",
    "validate-gameplay-intent": "validate_gameplay_intent",
    "export-clean-room-contract": "export_clean_room_contract",
    "screen-product-similarity": "screen_product_similarity",
    "build-experience-graph": "build_experience_graph",
    "calculate-experience-coverage": "calculate_experience_coverage",
    "plan-production-wave": "plan_production_wave",
    "validate-production-plan": "validate_production_wave",
    "show-production-plan": "show_production_wave",
}

RECONSTRUCTION_COMMANDS = {
    "prepare-reconstruction-wave": "prepare_reconstruction_wave",
}

PROJECT_OPERATION_COMMANDS = {**MILESTONE_COMMANDS, **RECONSTRUCTION_COMMANDS}


def _run_operation_request(path: str) -> int:
    from .operations.registry import execute_request
    try:
        payload = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
        request = json.loads(payload)
    except (OSError, json.JSONDecodeError) as exc:
        response = {"schema_version": "1.0.0", "request_id": None, "operation": "<invalid>", "ok": False, "project_revision": None, "result": None, "diagnostics": [{"severity": "error", "code": "INVALID_JSON", "message": str(exc)}], "artifacts": []}
    else:
        response = execute_request(request)
    print(json.dumps(response, sort_keys=True, ensure_ascii=False))
    return 0 if response["ok"] else 2


def _run_milestone_operation(args: argparse.Namespace) -> int:
    from .operations.registry import execute_request

    try:
        if args.parameters is None:
            parameters = {}
        else:
            payload = sys.stdin.read() if args.parameters == "-" else Path(args.parameters).read_text(encoding="utf-8")
            parameters = json.loads(payload)
        if not isinstance(parameters, dict):
            raise ValueError("parameters must contain a JSON object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "code": "INVALID_PARAMETERS", "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    request = {
        "schema_version": "1.0.0",
        "request_id": args.request_id,
        "operation": PROJECT_OPERATION_COMMANDS[args.command],
        "project": args.project,
        "parameters": parameters,
    }
    if args.expected_revision is not None:
        request["expected_revision"] = args.expected_revision
    response = execute_request(request)
    if args.output_json:
        print(json.dumps(response, sort_keys=True, ensure_ascii=False))
    elif response["ok"]:
        result = response.get("result") or {}
        status = result.get("status", "OK") if isinstance(result, dict) else "OK"
        print(f"{response['operation']}: {status}")
        print(f"project revision: {response['project_revision']}")
        for artifact in response.get("artifacts", []):
            print(f"artifact: {artifact['path']}")
    else:
        diagnostic = response["diagnostics"][0]
        print(f"{response['operation']}: {diagnostic['code']}: {diagnostic['message']}", file=sys.stderr)
        details = diagnostic.get("details")
        if isinstance(details, dict) and details.get("remediation"):
            print(f"remediation: {details['remediation']}", file=sys.stderr)
    return 0 if response["ok"] else 2


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
    operation_parser = sub.add_parser("operation", help="Execute one structured conversion-project operation")
    operation_parser.add_argument("--request", required=True, help="JSON request file, or - for stdin")
    distill_parser = sub.add_parser("distill-modpack", help="Select a progression-coherent, console-aware scope from a large modpack analysis")
    distill_parser.add_argument("--input", required=True, help="Distillation input JSON or analysis project")
    distill_parser.add_argument("--target", default="MARKETPLACE_ADDON_STABLE")
    distill_parser.add_argument("--effort-budget", default="0.25", help="Fraction of estimated full conversion effort")
    distill_parser.add_argument("--output", required=True, help="Output root for the distillation directory")
    distill_parser.add_argument("--review-adjustments", help="Optional separately recorded AI/human review-adjustment JSON")
    for command in PROJECT_OPERATION_COMMANDS:
        milestone = sub.add_parser(command, help=f"Run the {PROJECT_OPERATION_COMMANDS[command]} project operation")
        milestone.add_argument("--project", required=True, help="Conversion-project root")
        milestone.add_argument("--parameters", help="JSON parameter file, or - for stdin")
        milestone.add_argument("--expected-revision", type=int)
        milestone.add_argument("--request-id")
        milestone.add_argument("--json", action="store_true", dest="output_json", help="Emit the complete operation response as JSON")
    args = parser.parse_args(argv)

    if args.command == "operation":
        return _run_operation_request(args.request)

    if args.command in PROJECT_OPERATION_COMMANDS:
        return _run_milestone_operation(args)

    if args.command == "distill-modpack":
        from .distillation import DistillationError, distill_modpack
        try:
            decimal_budget = Decimal(args.effort_budget)
            basis_points_decimal = decimal_budget * 10_000
            if basis_points_decimal != basis_points_decimal.to_integral_value():
                raise DistillationError("effort budget supports at most four decimal places")
            result = distill_modpack(
                args.input,
                args.output,
                target=args.target,
                effort_budget_basis_points=int(basis_points_decimal),
                review_adjustments=args.review_adjustments,
            )
        except (DistillationError, InvalidOperation) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
            return 2
        summary = {
            "ok": bool(result["selection"]["progression_complete"]),
            "result_digest": result["result_digest"],
            "source_digest": result["source_digest"],
            "selected_systems": result["selection"]["ids"],
            "selected_effort_units": result["selection"]["effort_units"],
            "effort_limit_units": result["selection"]["effort_limit_units"],
            "missing_progression_stages": result["selection"]["missing_progression_stages"],
            "artifacts": [row["path"] for row in result["artifacts"]],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if result["selection"]["progression_complete"] else 1

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
