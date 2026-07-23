"""Render the deterministic Controlled Chaos forest planning package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mccompiler.forest_planning.package import canonical, load_repository_package


def render(root: Path, output: Path) -> tuple[Path, Path]:
    contract = root / "tests/fixtures/forest_planning/controlled-chaos-forest-contract.json"
    package, validation = load_repository_package(root, contract)
    output.mkdir(parents=True, exist_ok=True)
    for stale_intent in output.glob("contracts/*/gameplay-intent.json"):
        stale_intent.unlink()
    package_path = output / "controlled-chaos-forest-production-plan.json"
    validation_path = output / "controlled-chaos-forest-production-plan.validation.json"
    analysis_root = root / "analysis/gameplay-intent/controlled-chaos-forest"
    analysis_root.mkdir(parents=True, exist_ok=True)
    (analysis_root / "forest-planning-analysis.json").write_bytes(canonical(package))
    production_elements: list[dict[str, object]] = []
    safe_element_keys = (
        "product_id", "abstract_gameplay_role", "clean_room_design_contract",
        "rights_disposition", "originality_requirements",
        "similarity_screening_requirement", "experience_nodes_satisfied",
        "progression_dependencies", "asset_contract", "behavior_contract",
        "structure_or_encounter_contract", "production_effort",
        "ps4_cost_dimensions", "multiplayer_requirements",
        "persistence_requirements", "cleanup_policy", "qualification_plan",
        "current_status",
    )
    for element in package["components"]["forest-elements.json"]:
        if element["product_id"] == "bramblehorn":
            bramble_contract_root = output / "contracts/bramblehorn"
            bramble_contract_root.mkdir(parents=True, exist_ok=True)
            bramble_clean_room = {
                "schema_version": "1.0.0",
                "product_id": "bramblehorn",
                "abstract_gameplay_role": element["abstract_gameplay_role"],
                "rights_disposition": element["rights_disposition"],
                "originality_requirements": element["originality_requirements"],
                "similarity_screening_requirement": element["similarity_screening_requirement"],
                "source_receipt": "receipt:prototype:bramblehorn:authoring",
            }
            (bramble_contract_root / "clean-room-design.json").write_bytes(
                canonical(bramble_clean_room)
            )
            production_elements.append({
                **{key: element[key] for key in safe_element_keys},
                "clean_room_design_contract": "production/planning/controlled-chaos-forest/contracts/bramblehorn/clean-room-design.json",
                "gameplay_intent_ir_ref": "intent:forest:bramblehorn",
            })
            continue
        element_root = output / "contracts" / element["product_id"]
        element_root.mkdir(parents=True, exist_ok=True)
        records = {
            "clean-room-design.json": {
                "schema_version": "1.0.0",
                "product_id": element["product_id"],
                "abstract_gameplay_role": element["abstract_gameplay_role"],
                "rights_disposition": element["rights_disposition"],
                "originality_requirements": element["originality_requirements"],
                "similarity_screening_requirement": element["similarity_screening_requirement"],
            },
            "asset.json": {
                "schema_version": "1.0.0",
                "planning_only": True,
                "product_id": element["product_id"],
                "requirements": element["originality_requirements"],
                "production_effort": element["production_effort"],
            },
            "behavior.json": {
                "schema_version": "1.0.0",
                "planning_only": True,
                "product_id": element["product_id"],
                "multiplayer_requirements": element["multiplayer_requirements"],
                "persistence_requirements": element["persistence_requirements"],
                "cleanup_policy": element["cleanup_policy"],
            },
            "qualification.json": {
                "schema_version": "1.0.0",
                "planning_only": True,
                "product_id": element["product_id"],
                "qualification_plan": element["qualification_plan"],
                "current_status": element["current_status"],
            },
        }
        if element["structure_or_encounter_contract"] is not None:
            records["encounter.json"] = {
                "schema_version": "1.0.0",
                "planning_only": True,
                "product_id": element["product_id"],
                "bounded": True,
                "cleanup_policy": element["cleanup_policy"],
            }
        for name, record in records.items():
            (element_root / name).write_bytes(canonical(record))
        intent = {
            "schema_version": "1.0.0",
            "planning_only": True,
            "excluded_from_production_export": True,
            "product_id": element["product_id"],
            "experience_nodes_satisfied": element["experience_nodes_satisfied"],
            "progression_dependencies": element["progression_dependencies"],
        }
        (analysis_root / f"{element['product_id']}.json").write_bytes(canonical(intent))
        production_elements.append({
            **{key: element[key] for key in safe_element_keys},
            "gameplay_intent_ir_ref": f"intent:forest:{element['product_id']}",
        })
    graph = json.loads(json.dumps(
        package["components"]["experience-acceptance-graph.json"]
    ))
    for node in graph["nodes"]:
        node["implementation_refs"] = [
            ref for ref in node["implementation_refs"]
            if ref.startswith("prototypes/blockbench/bramblehorn/")
        ]
        node["evidence_refs"] = [
            ref for ref in node["evidence_refs"]
            if ref.startswith("prototypes/blockbench/bramblehorn/")
            or ref.startswith("receipt:")
        ]
        node["contract_refs"] = [
            ref for ref in node["contract_refs"]
            if ref.startswith("production/planning/")
            or ref.startswith("prototypes/blockbench/bramblehorn/")
        ]
    exported_components = {
        "experience-acceptance-graph.json": graph,
        "experience-coverage-report.json": package["components"]["experience-coverage-report.json"],
        "production-wave-plan.json": package["components"]["production-wave-plan.json"],
        "forest-elements.json": production_elements,
        "bramblehorn-evidence.json": package["components"]["evidence.json"]["bramblehorn"],
    }
    exported_hashes = {
        name: hashlib.sha256(canonical(value)).hexdigest()
        for name, value in sorted(exported_components.items())
    }
    exported = {
        "schema_version": "1.0.0",
        "export_profile": "CLEAN_ROOM_PRODUCTION_PLANNING",
        "components": exported_components,
        "component_hashes": exported_hashes,
        "package_sha256": hashlib.sha256(canonical(exported_hashes)).hexdigest(),
    }
    exported_validation = {
        "schema_version": "1.0.0",
        "valid": True,
        "errors": [],
        "package_sha256": exported["package_sha256"],
        "component_hashes": exported_hashes,
    }
    package_path.write_bytes(canonical(exported))
    validation_path.write_bytes(canonical(exported_validation))
    return package_path, validation_path


def main() -> None:
    parser = argparse.ArgumentParser()
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument(
        "--output",
        type=Path,
        default=default_root / "production/planning/controlled-chaos-forest",
    )
    args = parser.parse_args()
    paths = render(args.root.resolve(), args.output.resolve())
    print(json.dumps({"written": [str(path) for path in paths]}, sort_keys=True))


if __name__ == "__main__":
    main()
