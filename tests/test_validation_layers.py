from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from mccompiler.bedrock import ZIP_TIME, compile_bedrock
from mccompiler.planner import plan_conversion
from mccompiler.validate import validate_output


def evidence() -> list[dict[str, object]]:
    return [{"source_file": "Validation.java", "start_line": 1, "end_line": 1, "extraction_rule": "test", "confidence": 1.0}]


def fixture() -> tuple[dict, dict]:
    ir = {
        "schema_version": "1.0.0", "metadata": {"id": "validation"},
        "mods": [{"id": "validation"}], "dependencies": [],
        "content": [
            {"kind": "item", "identifier": "validation:wand", "properties": {}, "evidence": evidence()},
            {"kind": "block", "identifier": "validation:machine", "properties": {}, "evidence": evidence()},
            {"kind": "recipe", "identifier": "validation:wand_recipe", "properties": {"result": "validation:wand"}, "evidence": evidence()},
            {"kind": "entity", "identifier": "validation:golem", "properties": {}, "evidence": evidence()},
            {"kind": "spawn_rule", "identifier": "validation:golem_spawn", "properties": {"entity": "validation:golem"}, "evidence": evidence()},
        ],
        "assets": [], "registries": [], "behaviors": [],
        "state": [{"id": "charge", "scope": "player", "value_type": "number", "default": 0, "persistence": "persistent", "evidence": evidence()}],
        "presentation_requirements": [], "world_requirements": [], "ui_intent": [], "networking_intent": [],
        "unsupported_hooks": [], "diagnostics": [], "tests": [],
        "target": {"script_api_version": "2.0.0", "version_markers": ["1.21.90"]},
    }
    return ir, plan_conversion(ir)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rebuild_archive(root: Path) -> None:
    archive = root / "converted-mod.mcaddon"
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(file for file in root.rglob("*") if file.is_file() and file != archive):
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())


class ValidationLayerTests(unittest.TestCase):
    def generated(self, directory: str) -> tuple[Path, dict, dict]:
        ir, plan = fixture()
        root = Path(directory)
        compile_bedrock(ir, plan, root)
        return root, ir, plan

    def test_valid_output_has_layered_checks_and_no_runtime_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root, ir, plan = self.generated(directory)
            result = validate_output(root, plan, artifacts={"modir": ir, "behavior_ir": [{
                "id": "validation:test", "owner": {}, "trigger": {"type": "item_use"},
                "conditions": [], "actions": [], "evidence": evidence(), "confidence": 1.0, "diagnostics": [],
            }], "overrides": {"schema_version": "1.0.0", "overrides": []}})
            self.assertTrue(result["valid"], result)
            names = {item["name"] for item in result["layers"]["static"]["checks"]}
            self.assertTrue({"ir-and-override-schemas", "identifier-uniqueness", "content-cross-references", "state-schema-consistency", "script-syntax-and-imports"} <= names)
            self.assertEqual("not-run", result["layers"]["runtime"]["status"])
            localization = next(item for item in result["layers"]["static"]["checks"] if item["name"] == "localization-coverage")
            self.assertTrue(localization["passed"])
            self.assertGreater(localization["files"], 0)

    def test_schema_collision_reference_resource_component_and_state_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root, ir, plan = self.generated(directory)
            duplicate = json.loads((root / "behavior_pack/items/validation_wand.json").read_text())
            write_json(root / "behavior_pack/items/duplicate.json", duplicate)
            recipe_path = root / "behavior_pack/recipes/validation_wand_recipe.json"
            recipe = json.loads(recipe_path.read_text())
            recipe["minecraft:recipe_shapeless"]["result"]["item"] = "validation:missing"
            write_json(recipe_path, recipe)
            item_path = root / "behavior_pack/items/validation_wand.json"
            item = json.loads(item_path.read_text())
            components = item["minecraft:item"]["components"]
            components["minecraft:icon"] = "missing_texture"
            components["minecraft:not_a_component"] = {}
            write_json(item_path, item)
            bad_ir = dict(ir)
            bad_ir["state"] = [
                {"id": "charge", "value_type": "number", "default": "wrong", "persistence": "persistent"},
                {"id": "charge", "value_type": "boolean", "default": False, "persistence": "persistent"},
            ]
            rebuild_archive(root)
            result = validate_output(root, plan, artifacts={"modir": bad_ir, "overrides": {"schema_version": "0.0.0", "overrides": []}})
            self.assertFalse(result["valid"])
            combined = "\n".join(result["errors"])
            for phrase in ("Identifier collision", "Missing referenced content", "Missing referenced texture", "Unsupported item component", "State default", "Conflicting state schema", "Unsupported overrides schema version"):
                self.assertIn(phrase, combined)

    def test_script_manifest_dependencies_and_internal_dependency_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root, ir, plan = self.generated(directory)
            main = root / "behavior_pack/scripts/main.js"
            main.write_text(main.read_text() + "\nimport './missing.js';\n", encoding="utf-8")
            manifest_path = root / "behavior_pack/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["dependencies"].append({"module_name": "@minecraft/server-net", "version": "1.0.0-beta"})
            write_json(manifest_path, manifest)
            bad_ir = dict(ir)
            bad_ir["dependencies"] = [{"id": "missing_mod", "required": True, "internal": True}]
            rebuild_archive(root)
            result = validate_output(root, plan, artifacts={"modir": bad_ir})
            self.assertFalse(result["valid"])
            combined = "\n".join(result["errors"])
            self.assertIn("Unresolved script import", combined)
            self.assertIn("experimental Script API module", combined)
            self.assertIn("Missing internal ModIR dependency", combined)

    def test_runtime_evidence_is_parsed_and_must_contain_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, plan = self.generated(directory)
            write_json(root / "reports/runtime-evidence.json", {"status": "passed", "attempted": True, "checks": [{"name": "activation", "passed": True}]})
            rebuild_archive(root)
            result = validate_output(root, plan, runtime=True)
            self.assertFalse(result["valid"])
            self.assertEqual("failed", result["layers"]["runtime"]["status"])
            self.assertTrue(any("lacks runtime-log" in error for error in result["errors"]))

            write_json(root / "reports/runtime-evidence.json", {
                "status": "passed", "attempted": True,
                "logs": ["[mccompiler] runtime initialized", "behavior checks complete"],
                "checks": [{"name": "activation", "passed": True}, {"name": "persistence", "passed": True}],
                "critical_errors": [],
            })
            rebuild_archive(root)
            result = validate_output(root, plan, runtime=True)
            self.assertTrue(result["valid"], result)
            self.assertEqual("passed", result["layers"]["runtime"]["status"])


if __name__ == "__main__":
    unittest.main()
