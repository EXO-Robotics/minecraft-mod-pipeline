import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "engineering/native-assets/whisperwood/repair_whisperwood_native.py"
SPEC = importlib.util.spec_from_file_location("whisperwood_native_tool", MODULE_PATH)
assert SPEC and SPEC.loader
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


def model(*, animations=None, groups=None, locators=None, texture_path="/private/source.png"):
    groups = groups or ["root", "body", "head"]
    locators = locators or []
    return {
        "textures": [{"name": "old.png", "path": texture_path, "relative_path": "old.png"}],
        "animations": [{"name": name} for name in (animations or [])],
        "elements": [{"type": "locator", "name": name} for name in locators],
        "outliner": [{"name": name, "children": []} for name in groups],
    }


def geometry(*locator_entries):
    bones = [{"name": "root"}, {"name": "head"}]
    for bone_name, locator_name, transform in locator_entries:
        bone = next(item for item in bones if item["name"] == bone_name)
        bone.setdefault("locators", {})[locator_name] = transform
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {"identifier": "geometry.aionbound.test", "texture_width": 32, "texture_height": 32},
            "bones": bones,
        }],
    }


class WhisperwoodNativeToolTests(unittest.TestCase):
    def test_missing_role_clips_are_exact_and_leaf_names_match(self):
        actual = ["animation.aionbound.mossback_stalker.idle", "animation.aionbound.mossback_stalker.walk"]
        self.assertEqual(TOOL.missing_role_clips(["idle", "walk"], actual), [])
        self.assertEqual(TOOL.missing_role_clips(["idle", "pounce", "death"], actual), ["pounce", "death"])

    def test_locator_plan_uses_required_existing_bones(self):
        value = model()
        exported = TOOL.exported_locator_specs(
            geometry(
                ("root", "effect", [1, 2, 3]),
                ("head", "gaze", {"offset": [4.5, 6, -7], "rotation": [10, 20, 30]}),
                ("head", "projectile", [8, 9, 10]),
            ),
            ["effect", "gaze", "projectile"],
        )
        plan = TOOL.build_locator_plan(["effect", "gaze", "projectile"], TOOL.extract_group_names(value), exported)
        self.assertEqual(plan["effect"]["parent"], "root")
        self.assertEqual(plan["effect"]["position"], [1, 2, 3])
        self.assertEqual(plan["effect"]["rotation"], [0, 0, 0])
        self.assertEqual(plan["gaze"]["parent"], "head")
        self.assertEqual(plan["gaze"]["position"], [4.5, 6, -7])
        self.assertEqual(plan["gaze"]["rotation"], [10, 20, 30])
        self.assertFalse(plan["gaze"]["explicit_parent_override"])

    def test_explicit_locator_mapping_must_reference_existing_bone(self):
        with self.assertRaisesRegex(TOOL.NativeToolError, "EXPLICIT_LOCATOR_BONE_MISSING:projectile:muzzle"):
            TOOL.build_locator_plan(
                ["projectile"],
                ["root", "head"],
                TOOL.exported_locator_specs(geometry(("head", "projectile", [0, 0, 0])), ["projectile"]),
                {"projectile": "muzzle"},
            )

    def test_explicit_mapping_can_approvedly_override_exported_parent(self):
        exported = TOOL.exported_locator_specs(geometry(("root", "projectile", [1, 2, 3])), ["projectile"])
        plan = TOOL.build_locator_plan(["projectile"], ["root", "head"], exported, {"projectile": "head"})
        self.assertEqual(plan["projectile"]["source_parent"], "root")
        self.assertEqual(plan["projectile"]["parent"], "head")
        self.assertTrue(plan["projectile"]["explicit_parent_override"])
        self.assertEqual(plan["projectile"]["position"], [1, 2, 3])

    def test_default_parent_must_match_canonical_export(self):
        exported = TOOL.exported_locator_specs(geometry(("root", "gaze", [0, 1, 2])), ["gaze"])
        with self.assertRaisesRegex(
            TOOL.NativeToolError,
            "EXPORTED_LOCATOR_PARENT_MISMATCH:gaze:expected=head:actual=root",
        ):
            TOOL.build_locator_plan(["gaze"], ["root", "head"], exported)

    def test_native_export_must_preserve_exact_transform(self):
        exported = TOOL.exported_locator_specs(
            geometry(("head", "projectile", {"offset": [1.25, -2, 3], "rotation": [4, 5.5, 6]})),
            ["projectile"],
        )
        plan = TOOL.build_locator_plan(["projectile"], ["root", "head"], exported)
        self.assertEqual(TOOL.locator_export_diagnostics(plan, exported), [])
        changed = json.loads(json.dumps(exported))
        changed["projectile"]["rotation"][1] = 5.5001
        self.assertEqual(
            TOOL.locator_export_diagnostics(plan, changed),
            ["LOCATOR_TRANSFORM_MISMATCH_IN_NATIVE_EXPORT:projectile"],
        )

    def test_missing_exported_locator_is_rejected(self):
        with self.assertRaisesRegex(TOOL.NativeToolError, "EXPORTED_LOCATOR_MISSING:gaze"):
            TOOL.exported_locator_specs(geometry(("root", "effect", [0, 0, 0])), ["effect", "gaze"])

    def test_ambiguous_exported_locator_is_rejected(self):
        with self.assertRaisesRegex(TOOL.NativeToolError, "EXPORTED_LOCATOR_AMBIGUOUS:effect:head,root"):
            TOOL.exported_locator_specs(
                geometry(("root", "effect", [0, 0, 0]), ("head", "effect", [1, 2, 3])),
                ["effect"],
            )

    def test_texture_paths_are_normalized_without_touching_source(self):
        source = model()
        changed = TOOL.normalize_texture_records(source, "mossback_stalker.png")
        self.assertEqual(changed, 3)
        self.assertEqual(source["textures"][0]["path"], "textures/mossback_stalker.png")
        self.assertEqual(source["textures"][0]["relative_path"], "textures/mossback_stalker.png")

    def test_non_loopback_cdp_endpoint_is_rejected(self):
        with self.assertRaisesRegex(TOOL.NativeToolError, "CDP_ENDPOINT_NOT_LOOPBACK"):
            TOOL.assert_loopback_endpoint("http://192.0.2.1:9333")

    def test_animation_withhold_writes_receipt_before_cdp(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bbmodel = root / "copied.bbmodel"
            texture = root / "copied.png"
            canonical_geometry = root / "copied.geo.json"
            brief = root / "brief.json"
            output = root / "evidence"
            bbmodel.write_text(json.dumps(model(animations=["animation.aionbound.test.idle"])), encoding="utf-8")
            texture.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
            canonical_geometry.write_text(json.dumps(geometry(("root", "effect", [1, 2, 3]))), encoding="utf-8")
            brief.write_text(json.dumps({"animations": ["idle", "walk"], "locators": ["effect"]}), encoding="utf-8")
            code, receipt = TOOL.execute(TOOL.Inputs(
                bbmodel=bbmodel,
                texture=texture,
                geometry=canonical_geometry,
                brief=brief,
                output=output,
                cdp_endpoint="http://127.0.0.1:9333",
                locator_map=None,
                screenshot_views=(),
            ))
            self.assertEqual(code, 3)
            self.assertEqual(receipt["status"], "WITHHELD_MISSING_ROLE_ANIMATIONS")
            self.assertEqual(receipt["diagnostics"], ["MISSING_REQUIRED_ROLE_CLIP:walk"])
            self.assertFalse(receipt["native_session_started"])
            self.assertEqual(receipt["canonical_geometry_locator_transforms"]["effect"]["position"], [1, 2, 3])
            self.assertEqual(receipt["inputs"]["canonical_geometry"]["sha256"], TOOL.sha256_file(canonical_geometry))
            stored = json.loads((output / TOOL.RECEIPT_NAME).read_text(encoding="utf-8"))
            self.assertEqual(stored, receipt)
            self.assertFalse((output / "native-project").exists())

    def test_two_pass_export_hash_ignores_json_formatting_only(self):
        compact = '{"minecraft:geometry":[{"bones":[]}],"format_version":"1.12.0"}'
        pretty = json.dumps(json.loads(compact), indent=2)
        changed = '{"minecraft:geometry":[{"bones":[{"name":"root"}]}],"format_version":"1.12.0"}'
        self.assertEqual(TOOL.canonical_export_hash(compact), TOOL.canonical_export_hash(pretty))
        self.assertNotEqual(TOOL.canonical_export_hash(compact), TOOL.canonical_export_hash(changed))

    def test_two_pass_export_hash_accepts_only_tight_float_noise(self):
        first = json.dumps({"description": {"visible_bounds_offset": [0, 0.6, 0]}})
        epsilon = json.dumps({"description": {"visible_bounds_offset": [0.0, 0.6000000000000001, -0.0]}})
        meaningful_bounds_drift = json.dumps({"description": {"visible_bounds_offset": [0, 0.600001, 0]}})
        self.assertEqual(TOOL.canonical_export_hash(first), TOOL.canonical_export_hash(epsilon))
        self.assertNotEqual(TOOL.canonical_export_hash(first), TOOL.canonical_export_hash(meaningful_bounds_drift))

    def test_meaningful_locator_transform_drift_remains_rejected(self):
        authority = {
            "effect": {
                "source_parent": "root",
                "position": [1, 2, 3],
                "rotation": [0, 0, 0],
                "source_representation": "VECTOR",
            }
        }
        plan = TOOL.build_locator_plan(["effect"], ["root"], authority)
        drifted = json.loads(json.dumps(authority))
        drifted["effect"]["position"][2] = 3.000001
        self.assertEqual(
            TOOL.locator_export_diagnostics(plan, drifted),
            ["LOCATOR_TRANSFORM_MISMATCH_IN_NATIVE_EXPORT:effect"],
        )

    def test_nonfinite_export_number_is_rejected(self):
        with self.assertRaisesRegex(TOOL.NativeToolError, "NATIVE_EXPORT_NONFINITE_NUMBER"):
            TOOL.canonical_export_hash('{"value": NaN}')

    def test_native_script_creates_locator_and_uses_both_codecs(self):
        script = TOOL.native_session_script(
            Path("/tmp/project.bbmodel"), Path("/tmp/textures/model.png"),
            {"effect": {"parent": "root", "source_parent": "root", "position": [1, 2, 3], "rotation": [4, 5, 6], "explicit_parent_override": False}},
            Path("/tmp/pass1.geo.json"), Path("/tmp/pass1.animation.json"),
            Path("/tmp/pass2.geo.json"), Path("/tmp/pass2.animation.json"),
        )
        self.assertIn("new Locator", script)
        self.assertIn("Codecs.bedrock", script)
        self.assertIn("AnimationCodec.codecs.bedrock", script)
        self.assertIn("locatorSpec.position.slice()", script)
        self.assertIn("Blockbench.read", script)
        self.assertIn("Blockbench.writeFile", script)
        self.assertNotIn("require('fs')", script)
        self.assertNotIn("fs.readFileSync", script)
        self.assertNotIn("fs.writeFileSync", script)
        self.assertNotIn("parent.origin", script)
        self.assertNotIn("new Animation", script)


if __name__ == "__main__":
    unittest.main()
