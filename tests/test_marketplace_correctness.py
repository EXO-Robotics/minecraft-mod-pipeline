from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from mccompiler.bedrock import compile_bedrock
from mccompiler.planner import plan_conversion
from mccompiler.validate import validate_output


def evidence():
    return [{"source_file": "Fixture.java", "start_line": 1, "end_line": 1, "extraction_rule": "test", "confidence": 1.0}]


def ir(*, target=None, trigger="item_use", forms=False):
    return {
        "schema_version": "1.0.0", "metadata": {"id": "market"}, "mods": [{"id": "market"}],
        "dependencies": [], "content": [{"kind": "item", "identifier": "market:wand", "properties": {}, "evidence": evidence()}],
        "assets": [], "behaviors": [{"id": "market:wand/use", "owner": {"kind": "item", "identifier": "market:wand"}, "trigger": {"type": trigger}, "conditions": [], "actions": [{"type": "send_player_feedback"}], "evidence": evidence(), "confidence": 1.0, "diagnostics": []}],
        "state": [], "presentation_requirements": [], "ui_intent": ([{"id": "menu", "title": "Menu", "controls": ["OK"], "evidence": evidence()}] if forms else []),
        "networking_intent": [], "unsupported_hooks": [], "tests": [], "target": target,
    }


class MarketplaceCorrectnessTests(unittest.TestCase):
    def test_marketplace_resolves_only_emitted_modules_and_has_no_debug_mirrors(self):
        with tempfile.TemporaryDirectory() as directory:
            document = ir()
            plan = plan_conversion(document)
            compile_bedrock(document, plan, directory)
            root = Path(directory)
            manifest = json.loads((root / "behavior_pack/manifest.json").read_text())
            dependencies = {row.get("module_name"): row.get("version") for row in manifest["dependencies"] if row.get("module_name")}
            self.assertEqual({"@minecraft/server": "2.0.0"}, dependencies)
            self.assertFalse((root / "behavior_pack/scripts/tests").exists())
            self.assertFalse((root / "scripts").exists())
            usage = json.loads((root / "reports/api-usage.json").read_text())
            self.assertEqual(dependencies, usage["resolved_modules"])
            self.assertTrue(validate_output(root, plan)["valid"])
            marketplace = validate_output(root, plan, marketplace=True)
            self.assertTrue(marketplace["valid"], marketplace["errors"])
            self.assertTrue(usage["complete"])
            self.assertEqual([], usage["uncatalogued_symbols"])
            with zipfile.ZipFile(root / "converted-mod.mcaddon") as bundle:
                self.assertTrue(bundle.namelist())
                self.assertTrue(all(name.startswith(("behavior_pack/", "resource_pack/")) for name in bundle.namelist()))
                self.assertNotIn("reports/api-usage.json", bundle.namelist())
            self.assertTrue((root / "reports/api-usage.json").is_file())

    def test_forms_add_independently_resolved_server_ui(self):
        with tempfile.TemporaryDirectory() as directory:
            document = ir(forms=True)
            plan = plan_conversion(document)
            compile_bedrock(document, plan, directory)
            manifest = json.loads((Path(directory) / "behavior_pack/manifest.json").read_text())
            dependencies = {row.get("module_name"): row.get("version") for row in manifest["dependencies"] if row.get("module_name")}
            self.assertEqual("2.0.0", dependencies["@minecraft/server"])
            self.assertEqual("2.0.0", dependencies["@minecraft/server-ui"])

    def test_data_only_emits_no_script_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            document = ir(target="DATA_ONLY_FALLBACK")
            plan = plan_conversion(document)
            compile_bedrock(document, plan, directory)
            root = Path(directory)
            manifest = json.loads((root / "behavior_pack/manifest.json").read_text())
            self.assertFalse(any(row.get("type") == "script" for row in manifest["modules"]))
            self.assertFalse(any(row.get("module_name") for row in manifest["dependencies"]))
            self.assertFalse((root / "behavior_pack/scripts").exists())
            self.assertTrue(validate_output(root, plan)["valid"])

    def test_unmapped_required_trigger_fails_compilation(self):
        document = ir(trigger="imaginary_event")
        plan = plan_conversion(document)
        feature = next(row for row in plan["features"] if row["id"] == "market:wand/use")
        feature["classification"] = "SCRIPTED_EQUIVALENT"
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(ValueError, "unmapped required trigger"):
            compile_bedrock(document, plan, directory)

    def test_marketplace_validation_rejects_beta_bds_and_profile_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            document = ir()
            plan = plan_conversion(document)
            compile_bedrock(document, plan, directory)
            root = Path(directory)
            manifest_path = root / "behavior_pack/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["dependencies"].append({"module_name": "@minecraft/server-net", "version": "1.0.0-beta"})
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            usage_path = root / "reports/api-usage.json"
            usage = json.loads(usage_path.read_text())
            usage["target_profile"] = "BDS_DIAGNOSTIC"
            usage_path.write_text(json.dumps(usage), encoding="utf-8")
            result = validate_output(root, plan)
            self.assertFalse(result["valid"])
            combined = "\n".join(result["errors"])
            self.assertIn("prohibits BDS/unsupported module @minecraft/server-net", combined)
            self.assertIn("prohibits non-stable module @minecraft/server-net 1.0.0-beta", combined)
            self.assertIn("API usage evidence target differs", combined)

    def test_ticking_lifecycle_signals_are_recorded_as_requirements(self):
        with tempfile.TemporaryDirectory() as directory:
            document = ir(trigger="object_tick")
            plan = plan_conversion(document)
            compile_bedrock(document, plan, directory)
            usage = json.loads((Path(directory) / "reports/api-usage.json").read_text())
            catalogued = {row["symbol"] for row in usage["symbols"]}
            self.assertTrue({
                "system.runInterval", "world.beforeEvents.playerInteractWithBlock",
                "world.afterEvents.playerBreakBlock", "world.afterEvents.entitySpawn",
                "world.afterEvents.entityDie",
            } <= catalogued)

    def test_event_specific_context_normalizers_are_catalogued_and_emitted(self):
        expected = {
            "projectile_impact": "ProjectileHitEntityAfterEvent.getEntityHit",
            "entity_hurt": "EntityDamageSource.damagingEntity",
            "entity_death": "EntityDamageSource.damagingEntity",
        }
        for trigger, required_symbol in expected.items():
            with self.subTest(trigger=trigger), tempfile.TemporaryDirectory() as directory:
                document = ir(trigger=trigger)
                plan = plan_conversion(document)
                compile_bedrock(document, plan, directory)
                root = Path(directory)
                generated = (root / "behavior_pack/scripts/events/generated.js").read_text()
                usage = json.loads((root / "reports/api-usage.json").read_text())
                symbols = {row["symbol"] for row in usage["symbols"]}
                self.assertIn(required_symbol, symbols)
                self.assertIn("normalizeEvent(b.trigger.type,raw)", generated)
                self.assertIn("system.run(()=>dispatch(b,ctx))", generated)
                self.assertIn("contextComplete(b.trigger.type,ctx)", generated)
                self.assertIn("missing required event context", generated)
                self.assertIn("type==='item_use_on_block'", generated)
                self.assertNotIn("type==='item_use_on'", generated)
                if trigger == "projectile_impact":
                    self.assertIn("raw.getEntityHit()", generated)
                    self.assertIn("hitEntity:hit?.entity", generated)
                    self.assertIn("projectile:raw.projectile", generated)
                    self.assertIn("c.projectile?.typeId", generated)
                else:
                    self.assertIn("raw.damageSource?.damagingEntity", generated)
                self.assertTrue(validate_output(root, plan)["valid"])

    def test_projectile_actions_use_stable_source_aware_projectile_component(self):
        with tempfile.TemporaryDirectory() as directory:
            document = ir()
            document["behaviors"][0]["actions"] = [{"type": "spawn_projectile", "entity": "market:bolt"}]
            plan = plan_conversion(document)
            compile_bedrock(document, plan, directory)
            root = Path(directory)
            generated = (root / "behavior_pack/scripts/runtime/actions.js").read_text()
            self.assertIn("const stateOwner=c=>c.block?world:", generated)
            scheduler = (root / "behavior_pack/scripts/runtime/scheduler.js").read_text()
            events = (root / "behavior_pack/scripts/events/generated.js").read_text()
            self.assertIn("world.getDimension(c.dimensionId).getBlock(c.blockLocation)", scheduler)
            self.assertIn("blockLocation:{...e.block.location}", events)
            self.assertNotIn("{block:e.block,owner:", events)
            usage = json.loads((root / "reports/api-usage.json").read_text())
            symbols = {row["symbol"] for row in usage["symbols"]}
            self.assertTrue({
                "Entity.getHeadLocation", "Entity.getViewDirection",
                "EntityProjectileComponent.owner", "EntityProjectileComponent.shoot",
            } <= symbols)
            self.assertIn("projectile.owner=a", generated)
            self.assertIn("projectile.shoot(velocity)", generated)
            self.assertIn("effectId(x.effect)", generated)
            self.assertIn("phase write failed", generated)
            self.assertNotIn("e.applyImpulse?.(x.velocity", generated)
            self.assertTrue(validate_output(root, plan)["valid"])

    def test_marketplace_archive_rejects_internal_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            document = ir()
            plan = plan_conversion(document)
            archive = compile_bedrock(document, plan, directory)
            with zipfile.ZipFile(archive, "a") as bundle:
                bundle.writestr("reports/private-analysis.json", "{}")
            result = validate_output(directory, plan)
            self.assertFalse(result["valid"])
            self.assertTrue(any("consumer archive contains internal artifacts" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
