from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks" / "rights-cleared-java-mod"
PIN = "fe097cf9376242eb13d53dc485b61d8b33891392"


def load(relative: str) -> dict[str, object]:
    return json.loads((BENCHMARK / relative).read_text(encoding="utf-8"))


class BenchmarkBContractTests(unittest.TestCase):
    def test_contracts_are_machine_readable_and_bound_to_pin(self) -> None:
        expected = {
            "expected-behaviors.json",
            "contracts/state-schema.json",
            "contracts/save-migration.json",
            "contracts/multiplayer-ownership.json",
            "contracts/controller-first-redesign.json",
            "contracts/unsupported-mixin-mapping.json",
            "expected-quality.json",
            "rights-blockers.json",
        }
        for relative in expected:
            with self.subTest(relative=relative):
                self.assertEqual(load(relative)["schema_version"], "1.0.0")
        self.assertEqual(load("expected-behaviors.json")["source_revision"], PIN)
        self.assertEqual(load("technical-evidence.json")["candidate"]["revision"], PIN)

    def test_behavior_evidence_is_traceable_and_unverified(self) -> None:
        contract = load("expected-behaviors.json")
        behaviors = contract["behaviors"]
        self.assertGreaterEqual(len(behaviors), 5)
        self.assertEqual(contract["runtime_status"], "NOT_RUN")
        ids = {item["id"] for item in behaviors}
        self.assertEqual(len(ids), len(behaviors))
        for behavior in behaviors:
            self.assertEqual(behavior["verification"], "NOT_RUN")
            self.assertTrue(behavior["expected"])
            self.assertTrue(behavior["evidence"])
            for evidence in behavior["evidence"]:
                self.assertTrue(evidence["path"].startswith("src/main/java/"))
                self.assertEqual(len(evidence["lines"]), 2)
                self.assertLessEqual(evidence["lines"][0], evidence["lines"][1])

    def test_state_migration_and_multiplayer_contracts_fail_closed(self) -> None:
        state = load("contracts/state-schema.json")
        migration = load("contracts/save-migration.json")
        multiplayer = load("contracts/multiplayer-ownership.json")
        self.assertEqual(state["status"], "IMPLEMENTED_PROPOSED_REDESIGN_RUNTIME_NOT_VERIFIED")
        self.assertIn("dimension", state["logical_schema"]["locks"]["value"])
        authorizations = state["logical_schema"]["locks"]["value"]["authorization"]["one_of"]
        self.assertEqual({row["authorization_mode"] for row in authorizations}, {"owner_identity", "legacy_credential"})
        self.assertTrue(state["evidence"])
        self.assertTrue(state["unverified"])
        self.assertIn("idempotent", migration["invariants"])
        self.assertEqual("PURE_LOGIC_AND_BDS_NONEMPTY_UPGRADE_VERIFIED", migration["status"])
        self.assertTrue(any(step.get("on_malformed") == "quarantine_with_diagnostic" for step in migration["steps"]))
        self.assertEqual(multiplayer["authority"], "server")
        scenarios = set(multiplayer["required_scenarios"])
        self.assertTrue({"two_players_two_locks", "disconnect_reconnect", "dimension_collision"} <= scenarios)
        self.assertEqual(multiplayer["status"], "PURE_HANDLER_CONCURRENCY_IMPLEMENTED_RUNTIME_NOT_VERIFIED")
        self.assertTrue({"two_players_two_locks", "dimension_collision"} <= set(multiplayer["handler_scenarios_passed"]))
        self.assertTrue(multiplayer["evidence"])
        self.assertIn("real two-player actions", multiplayer["unverified"])

    def test_controller_and_all_observed_mixins_have_explicit_dispositions(self) -> None:
        controller = load("contracts/controller-first-redesign.json")
        mapping = load("contracts/unsupported-mixin-mapping.json")
        self.assertFalse(controller["approval"]["approved"])
        self.assertEqual(controller["runtime_evidence"], "NOT_RUN")
        self.assertEqual(set(controller["console_evidence"].values()), {"UNVERIFIED"})
        sources = {item["source"] for item in mapping["mappings"]}
        self.assertEqual(
            sources,
            {
                "mixin/AnvilScreenHandlerMixin.java",
                "mixin/ChestBlockMixin.java",
                "mixin/DoorBlockMixin.java",
                "mixin/FenceGateBlockMixin.java",
                "mixin/ShulkerBoxBlockMixin.java",
                "mixin/TrapdoorBlockMixin.java",
            },
        )
        self.assertTrue(all(item["classification"] for item in mapping["mappings"]))
        self.assertIn("zero mixin code emitted", mapping["acceptance"])

    def test_quality_and_rights_make_no_success_claims(self) -> None:
        quality = load("expected-quality.json")
        rights = load("rights-blockers.json")
        self.assertEqual(quality["runtime_status"], "NOT_RUN")
        self.assertEqual(quality["console_status"], "UNVERIFIED")
        self.assertEqual(quality["realm_status"], "UNVERIFIED")
        self.assertFalse(quality["thresholds"]["runtime_thresholds_evaluated"])
        self.assertFalse(rights["rights_cleared"])
        self.assertFalse(rights["marketplace_distribution_authorized"])
        self.assertIsNone(rights["human_reviewer"])
        self.assertTrue(all(blocker["status"] in {"UNKNOWN", "REVIEW_REQUIRED"} for blocker in rights["blockers"]))
        self.assertFalse(rights["source_material_policy"]["source_vendored"])
        self.assertFalse(rights["source_material_policy"]["assets_vendored"])

    def test_no_java_or_asset_payload_was_vendored(self) -> None:
        prohibited_suffixes = {".java", ".class", ".jar", ".png", ".tga", ".ogg", ".wav"}
        payloads = [path for path in BENCHMARK.rglob("*") if path.is_file() and path.suffix.lower() in prohibited_suffixes]
        self.assertEqual(payloads, [])


if __name__ == "__main__":
    unittest.main()
