from __future__ import annotations

import json
from pathlib import Path
import unittest

from mccompiler.distillation.validation import validate_with_schema
from mccompiler.forest_planning import (
    AcceptanceGraph, AcceptanceNode, Budget, EvidenceState, ForestElement,
    ProductionWavePlanner, load_repository_package,
)
from mccompiler.forest_planning.package import MANDATORY, NODE_IDS
from mccompiler.forest_planning.waves import DIMENSIONS
from tools.forest_planning.render_controlled_chaos_forest_plan import render


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/forest_planning/controlled-chaos-forest-contract.json"


class ForestProductionPlanningTests(unittest.TestCase):
    def package(self) -> tuple[dict[str, object], dict[str, object]]:
        return load_repository_package(ROOT, FIXTURE)

    def test_exact_product_and_experience_scope(self) -> None:
        package, _ = self.package()
        elements = package["components"]["forest-elements.json"]
        graph = package["components"]["experience-acceptance-graph.json"]
        self.assertEqual(10, len(elements))
        self.assertEqual(list(NODE_IDS), [row["node_id"] for row in graph["nodes"]])
        self.assertEqual(18, len(graph["nodes"]))
        self.assertNotIn("boss", " ".join(row["product_id"] for row in elements))

    def test_bramblehorn_is_actual_evidence_and_all_others_contract_only(self) -> None:
        package, _ = self.package()
        evidence = package["components"]["evidence.json"]
        self.assertEqual("SERVER_QUALIFIED_PS4_PENDING", evidence["bramblehorn"]["status"])
        self.assertEqual("PASSED", evidence["bramblehorn"]["gates"]["STABLE_BDS"])
        self.assertEqual("PENDING", evidence["bramblehorn"]["physical_ps4"])
        elements = package["components"]["forest-elements.json"]
        for row in elements:
            expected = "SERVER_QUALIFIED" if row["product_id"] == "bramblehorn" else "CONTRACT_ONLY"
            self.assertEqual(expected, row["current_status"])

    def test_every_element_has_completion_audit_contract(self) -> None:
        package, _ = self.package()
        required = {
            "product_id", "abstract_gameplay_role", "clean_room_design_contract",
            "gameplay_intent_ir_ref", "rights_disposition",
            "originality_requirements", "similarity_screening_requirement",
            "experience_nodes_satisfied", "progression_dependencies",
            "asset_contract", "behavior_contract",
            "structure_or_encounter_contract", "production_effort",
            "ps4_cost_dimensions", "multiplayer_requirements",
            "persistence_requirements", "cleanup_policy", "qualification_plan",
            "current_status",
        }
        for element in package["components"]["forest-elements.json"]:
            self.assertEqual(required, set(element))
            self.assertEqual(set(DIMENSIONS), set(element["ps4_cost_dimensions"]))

    def test_bramblehorn_evidence_chain_names_every_actual_surface(self) -> None:
        package, _ = self.package()
        bramble = package["components"]["evidence.json"]["bramblehorn"]
        self.assertEqual({
            "asset_registry", "authoring_operation", "authoring_report",
            "geometry", "texture", "rig_and_locators", "animations",
            "animation_controller", "behavior", "spawn", "loot", "stable_bds",
            "ps4_cost", "readiness",
        }, set(bramble["references"]))
        self.assertEqual(
            ["BEDROCK_DESKTOP", "PERSISTENCE_MULTIPLAYER", "PS4_PHYSICAL"],
            bramble["pending_checks"],
        )

    def test_all_seven_coverage_metrics_and_mandatory_behavior(self) -> None:
        package, _ = self.package()
        metrics = package["components"]["experience-coverage-report.json"]["metrics"]
        self.assertEqual({
            "planned_coverage", "contracted_coverage", "implemented_coverage",
            "static_qualified_coverage", "server_qualified_coverage",
            "client_qualified_coverage", "physical_qualified_coverage",
        }, set(metrics))
        self.assertEqual("SATISFIED", metrics["planned_coverage"]["status"])
        self.assertEqual("SATISFIED", metrics["contracted_coverage"]["status"])
        self.assertEqual("BLOCKED_MANDATORY_NODES", metrics["server_qualified_coverage"]["status"])
        self.assertTrue(set(metrics["server_qualified_coverage"]["mandatory_pending"]) <= MANDATORY)
        for name in (
            "implemented_coverage", "static_qualified_coverage",
            "server_qualified_coverage",
        ):
            self.assertEqual(200, metrics[name]["covered_weight"])
            self.assertEqual(1666, metrics[name]["basis_points"])

    def test_graph_nodes_use_full_spec_record_and_bramblehorn_refs(self) -> None:
        package, _ = self.package()
        nodes = package["components"]["experience-acceptance-graph.json"]["nodes"]
        required = {
            "node_id", "weight", "mandatory", "acceptance_requirements",
            "implementation_refs", "contract_refs", "evidence_refs",
            "qualification_requirements", "current_status", "confidence",
            "blocking_findings",
        }
        self.assertTrue(all(set(node) == required for node in nodes))
        bramble_nodes = [
            node for node in nodes
            if node["node_id"] in {
                "environmental_identity", "secondary_regional_creature",
                "worst_credible_load_qualified",
            }
        ]
        self.assertTrue(all(node["current_status"] == "server_qualified" for node in bramble_nodes))
        self.assertTrue(all(node["evidence_refs"] for node in bramble_nodes))

    def test_authoritative_budget_and_all_dimensions_preserve_reserve(self) -> None:
        package, _ = self.package()
        plan = package["components"]["production-wave-plan.json"]
        self.assertEqual(set(DIMENSIONS), set(plan["hard_caps"]))
        self.assertEqual(12, len(plan["hard_caps"]))
        self.assertEqual({
            "current": 62, "hard_ceiling": 80, "planning_ceiling": 64,
            "reserve": 18, "protected_minimum": 16, "reserve_consumed": False,
        }, plan["authoritative_scope"])
        self.assertEqual("UNCALIBRATED_PS4_PLANNING_PROXY_INPUTS", plan["weights_label"])
        self.assertFalse(plan["physical_ps4_verified"])
        for wave in plan["waves"]:
            for dimension, reserve in plan["required_reserves"].items():
                self.assertGreaterEqual(wave["reserve_preserved"][dimension], reserve)

    def test_planner_fails_closed_on_dimension_and_scope(self) -> None:
        raw = json.loads(FIXTURE.read_text())
        budget = Budget(raw["budget"]["hard_caps"], raw["budget"]["reserves"])
        costs = {dimension: 0 for dimension in DIMENSIONS}
        costs["active_entities"] = budget.planning_cap("active_entities") + 1
        with self.assertRaisesRegex(ValueError, "active_entities"):
            ProductionWavePlanner(budget).plan([
                ForestElement("swarm", 1, costs, 1),
            ])
        zero = {dimension: 0 for dimension in DIMENSIONS}
        with self.assertRaisesRegex(ValueError, "62-unit"):
            ProductionWavePlanner(budget).plan([
                ForestElement("a", 1, zero, 40),
                ForestElement("b", 1, zero, 23),
            ])

    def test_graph_rejects_cycles_and_unknown_dependencies(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown dependencies"):
            AcceptanceGraph([AcceptanceNode("a", 1, ("missing",))])
        with self.assertRaisesRegex(ValueError, "cycle"):
            AcceptanceGraph([
                AcceptanceNode("a", 1, ("b",)),
                AcceptanceNode("b", 1, ("a",)),
            ])

    def test_package_hashes_and_validation_are_deterministic(self) -> None:
        first, first_validation = self.package()
        second, second_validation = self.package()
        self.assertEqual(first, second)
        self.assertEqual(first_validation, second_validation)
        self.assertTrue(first_validation["valid"])
        self.assertEqual(first["package_sha256"], first_validation["package_sha256"])
        self.assertEqual(first["component_hashes"], first_validation["component_hashes"])

    def test_required_documents_match_required_schemas(self) -> None:
        package, validation = self.package()
        cases = (
            ("experience-acceptance-graph.json", "experience-acceptance-graph-1.0.0.json"),
            ("experience-coverage-report.json", "experience-coverage-report-1.0.0.json"),
            ("production-wave-plan.json", "production-wave-plan-1.0.0.json"),
        )
        for component, schema_name in cases:
            schema = json.loads((ROOT / "src/mccompiler/schemas" / schema_name).read_text())
            self.assertEqual([], validate_with_schema(package["components"][component], schema))
        schema = json.loads((ROOT / "src/mccompiler/schemas/production-plan-validation-report-1.0.0.json").read_text())
        self.assertEqual([], validate_with_schema(validation, schema))

    def test_tree_renderer_writes_identical_package_and_validation(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            first = render(ROOT, output)
            first_bytes = tuple(path.read_bytes() for path in first)
            second = render(ROOT, output)
            self.assertEqual(first_bytes, tuple(path.read_bytes() for path in second))

    def test_all_emitted_planning_refs_resolve_after_tree_render(self) -> None:
        render(
            ROOT,
            ROOT / "production/planning/controlled-chaos-forest",
        )
        package, _ = self.package()
        for element in package["components"]["forest-elements.json"]:
            refs = [
                element["clean_room_design_contract"],
                element["gameplay_intent_ir_ref"],
                element["asset_contract"],
                element["behavior_contract"],
                element["qualification_plan"]["reference"],
            ]
            if element["structure_or_encounter_contract"] is not None:
                refs.append(element["structure_or_encounter_contract"])
            for ref in refs:
                self.assertIsInstance(ref, str)
                self.assertTrue((ROOT / ref).is_file(), ref)
        for ref in package["components"]["evidence.json"]["bramblehorn"]["references"].values():
            if ref == "author_blockbench_asset":
                continue
            self.assertTrue((ROOT / ref).is_file(), ref)

    def test_production_tree_excludes_analysis_and_evidence_fields(self) -> None:
        output = ROOT / "production/planning/controlled-chaos-forest"
        render(ROOT, output)
        forbidden_keys = {
            "claims", "rights_source_access",
        }
        for path in output.rglob("*"):
            if not path.is_file():
                continue
            self.assertNotIn("gameplay-intent", path.name)
            if path.suffix != ".json":
                continue
            document = json.loads(path.read_text())
            stack = [document]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    self.assertFalse(forbidden_keys & set(value), path)
                    if "gameplay_intent_ir_ref" in value:
                        self.assertRegex(
                            value["gameplay_intent_ir_ref"],
                            r"^intent:forest:[a-z0-9_]+$",
                        )
                    stack.extend(value.values())
                elif isinstance(value, list):
                    stack.extend(value)
                elif isinstance(value, str):
                    self.assertFalse(value.startswith("analysis/"), (path, value))
                    self.assertNotIn("/analysis/", value, (path, value))

    def test_production_restores_required_safe_metadata_and_components(self) -> None:
        output = ROOT / "production/planning/controlled-chaos-forest"
        package_path, _ = render(ROOT, output)
        exported = json.loads(package_path.read_text())
        self.assertEqual({
            "experience-acceptance-graph.json",
            "experience-coverage-report.json",
            "production-wave-plan.json",
            "forest-elements.json",
            "bramblehorn-evidence.json",
        }, set(exported["components"]))
        restored = {
            "clean_room_design_contract", "gameplay_intent_ir_ref",
            "rights_disposition", "originality_requirements",
            "similarity_screening_requirement", "experience_nodes_satisfied",
            "progression_dependencies", "qualification_plan",
        }
        for element in exported["components"]["forest-elements.json"]:
            self.assertTrue(restored <= set(element))
            self.assertRegex(
                element["gameplay_intent_ir_ref"],
                r"^intent:forest:[a-z0-9_]+$",
            )
        graph = exported["components"]["experience-acceptance-graph.json"]
        for node in graph["nodes"]:
            for ref in node["evidence_refs"]:
                self.assertTrue(
                    ref.startswith("receipt:")
                    or ref.startswith("prototypes/blockbench/bramblehorn/")
                )

    def test_schemas_reject_unknown_versions_and_top_level_fields(self) -> None:
        package, validation = self.package()
        cases = (
            (package["components"]["experience-acceptance-graph.json"], "experience-acceptance-graph-1.0.0.json"),
            (package["components"]["experience-coverage-report.json"], "experience-coverage-report-1.0.0.json"),
            (package["components"]["production-wave-plan.json"], "production-wave-plan-1.0.0.json"),
            (validation, "production-plan-validation-report-1.0.0.json"),
        )
        for document, schema_name in cases:
            schema = json.loads((ROOT / "src/mccompiler/schemas" / schema_name).read_text())
            wrong = {**document, "schema_version": "9.9.9"}
            extra = {**document, "unexpected": True}
            self.assertTrue(validate_with_schema(wrong, schema))
            self.assertTrue(validate_with_schema(extra, schema))


if __name__ == "__main__":
    unittest.main()
