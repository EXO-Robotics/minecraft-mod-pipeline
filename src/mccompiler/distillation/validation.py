from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from .reports import REQUIRED_ARTIFACTS


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def validate_with_schema(value: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def walk(instance: Any, contract: dict[str, Any], path: str, root: dict[str, Any]) -> None:
        reference = contract.get("$ref")
        if isinstance(reference, str):
            if not reference.startswith("#/"):
                errors.append(f"{path}: unsupported external schema reference {reference}")
                return
            target: Any = root
            for part in reference[2:].split("/"):
                target = target.get(part) if isinstance(target, dict) else None
            if not isinstance(target, dict):
                errors.append(f"{path}: unresolved schema reference {reference}")
                return
            walk(instance, target, path, root)
            return
        expected = contract.get("type")
        if isinstance(expected, str) and not _matches_type(instance, expected):
            errors.append(f"{path}: expected {expected}")
            return
        if "const" in contract and instance != contract["const"]:
            errors.append(f"{path}: expected constant {contract['const']!r}")
        if isinstance(contract.get("enum"), list) and instance not in contract["enum"]:
            errors.append(f"{path}: value is not in enum")
        if isinstance(instance, str) and len(instance) < int(contract.get("minLength", 0)):
            errors.append(f"{path}: string is too short")
        if isinstance(instance, int) and not isinstance(instance, bool):
            if "minimum" in contract and instance < int(contract["minimum"]):
                errors.append(f"{path}: value is below minimum")
            if "maximum" in contract and instance > int(contract["maximum"]):
                errors.append(f"{path}: value is above maximum")
        if isinstance(instance, list):
            if len(instance) < int(contract.get("minItems", 0)):
                errors.append(f"{path}: array has too few items")
            if contract.get("uniqueItems"):
                serialized = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in instance]
                if len(serialized) != len(set(serialized)):
                    errors.append(f"{path}: array items are not unique")
            item_contract = contract.get("items")
            if isinstance(item_contract, dict):
                for index, item in enumerate(instance):
                    walk(item, item_contract, f"{path}[{index}]", root)
        if isinstance(instance, dict):
            required = contract.get("required", [])
            if isinstance(required, list):
                for key in required:
                    if key not in instance:
                        errors.append(f"{path}: missing required property {key}")
            properties = contract.get("properties", {})
            if isinstance(properties, dict):
                for key, item in instance.items():
                    child = properties.get(key)
                    if isinstance(child, dict):
                        walk(item, child, f"{path}.{key}", root)
                    elif contract.get("additionalProperties") is False:
                        errors.append(f"{path}: unexpected property {key}")
                    elif isinstance(contract.get("additionalProperties"), dict):
                        walk(item, contract["additionalProperties"], f"{path}.{key}", root)

    walk(value, schema, "$", schema)
    return errors


def validate_distillation_output(root: str | Path, *, require_complete: bool = True) -> list[str]:
    base = Path(root) / "distillation"
    errors: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        path = base / name
        if not path.is_file():
            errors.append(f"missing artifact: distillation/{name}")
    if errors:
        return errors
    try:
        quarter = json.loads((base / "quarter-scope.json").read_text(encoding="utf-8"))
        quarter_yaml = json.loads((base / "quarter-scope.yaml").read_text(encoding="utf-8"))
        deferred = json.loads((base / "deferred-scope.yaml").read_text(encoding="utf-8"))
        scores = json.loads((base / "scoring-report.json").read_text(encoding="utf-8"))
        progression = json.loads((base / "progression-graph.json").read_text(encoding="utf-8"))
        console = json.loads((base / "console-performance-risk.json").read_text(encoding="utf-8"))
        rights = json.loads((base / "rights-risk.json").read_text(encoding="utf-8"))
        manifest = json.loads((base / "distillation-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid machine-readable artifact: {exc}"]
    if quarter != quarter_yaml:
        errors.append("quarter-scope JSON and YAML differ")
    selection = quarter.get("selection", {})
    selected_ids = set(selection.get("ids", []))
    selected_rows = quarter.get("systems", [])
    if selected_ids != {row.get("id") for row in selected_rows}:
        errors.append("selected ids do not match quarter-scope systems")
    if int(selection.get("effort_units", 0)) > int(selection.get("effort_limit_units", -1)):
        errors.append("selection exceeds effort budget")
    if int(selection.get("console_cost_units", 0)) > int(console.get("limit_units", -1)):
        errors.append("selection exceeds static console budget")
    if require_complete and (not selection.get("progression_complete") or not progression.get("complete")):
        errors.append("selection progression is incomplete")
    if require_complete and progression.get("missing_stages"):
        errors.append("progression graph has missing stages")
    if require_complete and progression.get("missing_transitions"):
        errors.append("progression graph has disconnected stage transitions")
    prerequisites = {row.get("id"): set(row.get("prerequisites", [])) for row in selected_rows}
    for identifier, required in prerequisites.items():
        missing = required - selected_ids
        if missing:
            errors.append(f"{identifier} has unselected prerequisites: {', '.join(sorted(missing))}")
    decision_ids = selected_ids | {row.get("id") for row in deferred.get("systems", [])}
    score_ids = {row.get("system_id") for row in scores.get("scores", [])}
    if decision_ids != score_ids:
        errors.append("selected/deferred decisions do not cover every scored system")
    feature_scores = scores.get("feature_scores", [])
    if not isinstance(feature_scores, list):
        errors.append("scoring report feature_scores must be an array")
    if rights.get("approval_claimed") is not False:
        errors.append("rights report must not claim approval")
    contracts = schema_contracts()
    errors.extend(f"quarter-scope schema: {error}" for error in validate_with_schema(quarter, contracts["distillation-output-1.0.0.json"]))
    errors.extend(f"scoring schema: {error}" for error in validate_with_schema(scores, contracts["distillation-scoring-1.0.0.json"]))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("manifest artifacts must be an array")
    else:
        for artifact in artifacts:
            if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str) or not isinstance(artifact.get("sha256"), str):
                errors.append("manifest artifact entry is malformed")
                continue
            artifact_path = Path(root) / artifact["path"]
            if not artifact_path.is_file():
                errors.append(f"manifest artifact is missing: {artifact['path']}")
                continue
            digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            if digest != artifact["sha256"]:
                errors.append(f"manifest digest mismatch: {artifact['path']}")
    return errors


def schema_contracts() -> dict[str, dict[str, Any]]:
    schema_root = Path(__file__).resolve().parents[1] / "schemas"
    names = (
        "distillation-input-1.0.0.json",
        "distillation-scoring-1.0.0.json",
        "distillation-output-1.0.0.json",
        "distillation-review-adjustments-1.0.0.json",
    )
    return {name: json.loads((schema_root / name).read_text(encoding="utf-8")) for name in names}
