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


class WhisperwoodNativeToolTests(unittest.TestCase):
    def test_missing_role_clips_are_exact_and_leaf_names_match(self):
        actual = ["animation.aionbound.mossback_stalker.idle", "animation.aionbound.mossback_stalker.walk"]
        self.assertEqual(TOOL.missing_role_clips(["idle", "walk"], actual), [])
        self.assertEqual(TOOL.missing_role_clips(["idle", "pounce", "death"], actual), ["pounce", "death"])

    def test_locator_plan_uses_required_existing_bones(self):
        value = model()
        plan = TOOL.choose_locator_bones(
            ["effect", "gaze", "projectile"],
            TOOL.extract_group_names(value),
        )
        self.assertEqual(plan, {"effect": "root", "gaze": "head", "projectile": "head"})

    def test_explicit_locator_mapping_must_reference_existing_bone(self):
        with self.assertRaisesRegex(TOOL.NativeToolError, "EXPLICIT_LOCATOR_BONE_MISSING:projectile:muzzle"):
            TOOL.choose_locator_bones(["projectile"], ["root", "head"], {"projectile": "muzzle"})

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
            brief = root / "brief.json"
            output = root / "evidence"
            bbmodel.write_text(json.dumps(model(animations=["animation.aionbound.test.idle"])), encoding="utf-8")
            texture.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
            brief.write_text(json.dumps({"animations": ["idle", "walk"], "locators": ["effect"]}), encoding="utf-8")
            code, receipt = TOOL.execute(TOOL.Inputs(
                bbmodel=bbmodel,
                texture=texture,
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
            stored = json.loads((output / TOOL.RECEIPT_NAME).read_text(encoding="utf-8"))
            self.assertEqual(stored, receipt)
            self.assertFalse((output / "native-project").exists())

    def test_two_pass_export_hash_ignores_json_formatting_only(self):
        compact = '{"minecraft:geometry":[{"bones":[]}],"format_version":"1.12.0"}'
        pretty = json.dumps(json.loads(compact), indent=2)
        changed = '{"minecraft:geometry":[{"bones":[{"name":"root"}]}],"format_version":"1.12.0"}'
        self.assertEqual(TOOL.canonical_export_hash(compact), TOOL.canonical_export_hash(pretty))
        self.assertNotEqual(TOOL.canonical_export_hash(compact), TOOL.canonical_export_hash(changed))

    def test_native_script_creates_locator_and_uses_both_codecs(self):
        script = TOOL.native_session_script(
            Path("/tmp/project.bbmodel"), Path("/tmp/textures/model.png"), {"effect": "root"},
            Path("/tmp/pass1.geo.json"), Path("/tmp/pass1.animation.json"),
            Path("/tmp/pass2.geo.json"), Path("/tmp/pass2.animation.json"),
        )
        self.assertIn("new Locator", script)
        self.assertIn("Codecs.bedrock", script)
        self.assertIn("AnimationCodec.codecs.bedrock", script)
        self.assertNotIn("new Animation", script)


if __name__ == "__main__":
    unittest.main()
