from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Any

from mccompiler.bedrock import compile_bedrock
from mccompiler.planner import plan_conversion
from mccompiler.scan import scan_path
from mccompiler.validate import validate_output


ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "benchmarks" / "original-marketplace-showcase"
FIXTURE = SHOWCASE / "fixture"


def load_json(relative: str) -> dict[str, Any]:
    return json.loads((SHOWCASE / relative).read_text(encoding="utf-8"))


def expected_content(document: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (kind, identifier)
        for kind, identifiers in document["content"].items()
        for identifier in identifiers
    }


class OriginalMarketplaceShowcaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.expected = load_json("expected-ir.json")
        cls.quality = load_json("expected-quality.json")
        cls.contracts = load_json("test-contracts.json")
        cls.ir = scan_path(FIXTURE)
        cls.ir["target"] = cls.expected["target_profile"]
        cls.plan = plan_conversion(cls.ir)

    def test_original_source_fixture_is_valid_java_when_javac_is_available(self) -> None:
        javac = shutil.which("javac")
        if javac is None:
            self.skipTest("javac is not installed")
        source = FIXTURE / "src/showcase/clockwork/ClockworkGardensShowcase.java"
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [javac, "-d", directory, str(source)],
                text=True,
                capture_output=True,
                check=False,
            )
        if "Unable to locate a Java Runtime" in result.stderr:
            self.skipTest("javac launcher exists but no Java runtime is installed")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_scan_produces_complete_evidence_backed_ir(self) -> None:
        actual_content = {(row["kind"], row["identifier"]) for row in self.ir["content"]}
        self.assertEqual(expected_content(self.expected), actual_content)

        behaviors = {row["id"]: row for row in self.ir["behaviors"]}
        self.assertEqual(set(self.expected["behaviors"]), set(behaviors))
        for identifier, expected_actions in self.expected["behaviors"].items():
            self.assertEqual(expected_actions, [row["type"] for row in behaviors[identifier]["actions"]])
            self.assertTrue(behaviors[identifier]["evidence"], identifier)
            self.assertFalse(behaviors[identifier]["diagnostics"], identifier)
            self.assertIn("fingerprint", behaviors[identifier])

        actual_state: dict[str, set[str]] = {}
        for row in self.ir["state"]:
            actual_state.setdefault(row["scope"], set()).add(row["id"])
        self.assertEqual(
            {scope: set(ids) for scope, ids in self.expected["state"].items()},
            actual_state,
        )
        self.assertTrue(all(row["persistence"] == "persistent" for row in self.ir["state"]))
        self.assertEqual(set(self.expected["ui"]), {row["id"] for row in self.ir["ui_intent"]})
        self.assertEqual(
            set(self.expected["networking_redesign"]),
            {row["id"] for row in self.ir["networking_intent"]},
        )
        self.assertEqual(
            set(self.expected["unsupported"]),
            {row["feature"] for row in self.ir["unsupported_hooks"]},
        )
        evidence_records = (
            self.ir["content"]
            + self.ir["behaviors"]
            + self.ir["state"]
            + self.ir["ui_intent"]
            + self.ir["networking_intent"]
            + self.ir["unsupported_hooks"]
        )
        self.assertTrue(all(row.get("evidence") for row in evidence_records))

    def test_feature_matrix_and_non_runtime_records_are_machine_readable(self) -> None:
        required = set(self.quality["required_feature_families"])
        self.assertEqual(21, len(required))
        self.assertEqual("PARTIAL_EVENT_ADAPTER_DIAGNOSTIC", self.quality["runtime_status"])
        self.assertEqual("UNVERIFIED", self.quality["console_status"])
        self.assertFalse(self.quality["thresholds"]["runtime_thresholds_evaluated"])

        multiplayer = load_json("contracts/multiplayer-isolation.json")
        migration = load_json("contracts/save-migration.json")
        redesign = load_json("decisions/approved-redesign.json")
        self.assertEqual("DEFINED_NOT_RUN", multiplayer["status"])
        self.assertEqual("player", multiplayer["owner_scope"])
        self.assertEqual("DEFINED_NOT_RUN", migration["status"])
        self.assertEqual((1, 2), (migration["from_schema"], migration["to_schema"]))
        self.assertIn("idempotent", migration["invariants"])
        self.assertEqual("ACCEPTABLE_REDESIGN", next(
            row["quality_classification"]
            for row in self.quality["mechanics"]
            if row["id"] == redesign["feature_id"]
        ))
        self.assertEqual("static benchmark design only", redesign["approval_scope"])
        self.assertEqual("NOT_RUN", redesign["runtime_validation"])
        self.assertTrue(all(row["status"] == "NOT_RUN" for row in self.contracts["required_future_checks"]))

        bds = load_json("bds-diagnostic-validation.json")
        self.assertEqual("BDS_DIAGNOSTIC_BOOT_VERIFIED", bds["status"])
        self.assertTrue(bds["claims"]["bds_boot_verified"])
        self.assertFalse(bds["claims"]["gameplay_verified"])
        self.assertFalse(bds["claims"]["console_verified"])
        self.assertFalse(bds["claims"]["marketplace_approval_implied"])
        self.assertIn("physical-player item-use and generated launcher action chain", bds["unverified_scope"])
        adapter = bds["automated_adapter_validation"]
        self.assertTrue(adapter["passed"])
        self.assertTrue(adapter["script_initialized"])
        self.assertFalse(adapter["published_ports"])
        self.assertEqual(bds["artifact"]["world_hash"], adapter["world_sha256"])
        self.assertIn("@sha256:", adapter["image"])
        preview = bds["preview_simulated_action_validation"]
        self.assertTrue(preview["passed"])
        self.assertEqual("1.26.50.20", preview["bedrock_version"])
        self.assertTrue(preview["simulated_item_use_event_observed"])
        self.assertFalse(preview["stable_pack_item_source_available"])
        self.assertTrue(preview["entity_spawn_phase_write_read_verified"])
        self.assertTrue(preview["projectile_hit_entity_adapter_verified"])
        self.assertTrue(preview["entity_hit_adapter_observed"])
        self.assertFalse(preview["gameplay_verified"])
        self.assertFalse(preview["console_verified"])
        self.assertTrue(all(row["status"] == "PASSED" for row in self.contracts["diagnostic_checks"]))

        rights = (SHOWCASE / "rights/original-authorship-declaration.yaml").read_text(encoding="utf-8")
        self.assertIn("ORIGINAL_FIXTURE_DECLARED_NOT_MARKETPLACE_CLEARED", rights)
        self.assertIn("marketplace_cleared: false", rights)
        self.assertIn("commercial_marketplace_clearance: NOT_REVIEWED", rights)

    def test_preview_action_diagnostic_covers_remaining_real_action_families(self) -> None:
        script = (SHOWCASE / "diagnostic/simulated-actions/scripts/main.js").read_text(encoding="utf-8")
        self.assertIn("world.beforeEvents.playerInteractWithBlock", script)
        self.assertIn("useItemInSlotOnBlock(0, MACHINE_BLOCK)", script)
        self.assertIn("world.afterEvents.projectileHitBlock", script)
        self.assertIn("world.afterEvents.projectileHitEntity", script)
        self.assertIn("effect_api_invocation", script)
        self.assertIn("boss_phase_3", script)
        self.assertNotIn("registerActive(", script)
        self.assertNotIn("dispatch(", script)
        probes = load_json("simulated-action-log-probes.json")["probes"]
        check_ids = {row["check_id"] for row in probes}
        self.assertTrue({
            "showcase-block-interaction-adapter",
            "showcase-projectile-entity-impact",
            "showcase-projectile-block-impact",
            "showcase-effect-api-invocation",
            "showcase-machine-cycle",
            "showcase-entity-hit",
            "showcase-entity-hurt",
            "showcase-entity-death",
            "showcase-boss-phase-1",
            "showcase-boss-phase-2",
            "showcase-boss-phase-3",
            "showcase-persistence-after-restart",
        } <= check_ids)
        self.assertTrue(all(row["classification"] != "gameplay" for row in probes))

    def test_plan_covers_every_feature_and_all_required_outcomes(self) -> None:
        features = {(row["kind"], row["id"]): row for row in self.plan["features"]}
        expected_keys = {(f"content.{kind}", identifier) for kind, identifier in expected_content(self.expected)}
        expected_keys.update(
            (f"behavior.{row['trigger']['type']}", row["id"])
            for row in self.ir["behaviors"]
        )
        expected_keys.update(("ui.form", identifier) for identifier in self.expected["ui"])
        expected_keys.update(("networking.intent", identifier) for identifier in self.expected["networking_redesign"])
        expected_keys.update(("unsupported.mixin", identifier) for identifier in self.expected["unsupported"])
        self.assertEqual(expected_keys, set(features), "planner silently added or omitted a showcase feature")
        self.assertEqual("MARKETPLACE_ADDON_STABLE", self.plan["target_profile"])
        self.assertTrue(
            set(self.expected["required_plan_classifications"])
            <= {row["classification"] for row in self.plan["features"]}
        )
        unsupported = features[("unsupported.mixin", "clockwork_gardens:desktop_shader_portal")]
        self.assertEqual("UNSUPPORTED", unsupported["classification"])
        form = features[("ui.form", "clockwork_gardens:lumen_press_controls")]
        self.assertEqual("BEHAVIORAL_APPROXIMATION", form["classification"])

    def test_generate_validate_and_report_without_silent_omissions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "showcase"
            archive = compile_bedrock(self.ir, self.plan, output)
            validation = validate_output(output, self.plan, marketplace=True)
            self.assertTrue(validation["valid"], validation)

            manifest = json.loads((output / "conversion-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {row["id"] for row in self.plan["features"]},
                set(manifest["plan_feature_ids"]),
            )
            generated_content = {
                row["id"] for row in manifest["generated"] if row.get("id")
            }
            omitted_content = {row["id"] for row in manifest["omitted"] if row.get("id")}
            expected_ids = {identifier for _, identifier in expected_content(self.expected)}
            self.assertEqual(expected_ids, generated_content | omitted_content)
            self.assertFalse(generated_content & omitted_content)

            behavior_plan = json.loads((output / "tests/behavior-plan.json").read_text(encoding="utf-8"))
            self.assertEqual(set(self.expected["behaviors"]), set(behavior_plan["approved"]))
            self.assertEqual([], behavior_plan["omitted"])

            report = json.loads((output / "reports/unsupported-and-approximations.json").read_text(encoding="utf-8"))
            reported_unsupported = {row.get("id") for row in report["unsupported"]}
            self.assertIn("clockwork_gardens:desktop_shader_portal", reported_unsupported)
            report_json = json.loads((output / "reports/conversion-report.json").read_text(encoding="utf-8"))
            self.assertEqual("not-run", report_json["validation"]["runtime"])
            self.assertEqual("generated_pending_runtime_validation", report_json["result"])

            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                self.assertTrue(names)
                self.assertTrue(all(name.startswith(("behavior_pack/", "resource_pack/")) for name in names))
                payload = b"\n".join(bundle.read(name) for name in names)
            self.assertNotIn(b"clockwork_gardens:desktop_shader_portal", payload)
            self.assertNotIn(b"reports/", payload)
            self.assertNotIn(b"tests/behavior-plan.json", payload)


if __name__ == "__main__":
    unittest.main()
