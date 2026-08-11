import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "engineering/normalization/whisperwood/import_whisperwood.py"
SPEC = importlib.util.spec_from_file_location("whisperwood_importer", MODULE_PATH)
assert SPEC and SPEC.loader
IMPORTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = IMPORTER
SPEC.loader.exec_module(IMPORTER)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def make_asset(
    root: Path,
    asset_id: str,
    *,
    profile: str = "biped",
    locators: list[str] | None = None,
    clips: list[str] | None = None,
    related_assets: str = "",
    native_locators: list[str] | None = None,
    exported_locators: list[str] | None = None,
    exported_clips: list[str] | None = None,
    full_cube: bool = False,
    flat_icon: bool = False,
) -> None:
    locators = locators or []
    clips = clips or []
    native_locators = native_locators or []
    exported_locators = exported_locators or []
    exported_clips = exported_clips or []
    source_geometry = f"geometry.aionforge_ww.{asset_id}"
    brief = {
        "name": asset_id,
        "tier": "RESOURCE" if profile == "item" else "BLOCK" if profile == "block" else "CREATURE",
        "profile": profile,
        "model_identifier": source_geometry,
        "locators": locators,
        "animations": clips,
        "related_assets": related_assets,
        "editable": f"assets/editable/{asset_id}.bbmodel",
    }
    if flat_icon:
        brief["shipping_representation"] = "flat_inventory_icon"
    bbmodel = {
        "model_identifier": source_geometry,
        "elements": [
            {"type": "locator", "name": name, "uuid": f"locator-{index}"}
            for index, name in enumerate(native_locators)
        ],
        "textures": [{"name": f"{asset_id}.png", "path": "/absolute/source.png", "relative_path": f"{asset_id}.png"}],
        "animations": [
            {"name": f"animation.aionforge_ww.{asset_id}.{clip}"} for clip in exported_clips
        ],
    }
    cube = {"origin": [-8, 0, -8], "size": [16, 16, 16]} if full_cube else {"origin": [-2, 0, -2], "size": [4, 8, 4]}
    geometry = {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {"identifier": source_geometry, "texture_width": 16, "texture_height": 16},
            "bones": [{"name": "root", "pivot": [0, 0, 0], "cubes": [cube], "locators": {name: [0, 0, 0] for name in exported_locators}}],
        }],
    }
    animations = {
        "format_version": "1.8.0",
        "animations": {f"animation.aionforge_ww.{asset_id}.{clip}": {"loop": True} for clip in exported_clips},
    }
    assets = root / "assets"
    write_json(assets / "briefs" / f"{asset_id}.json", brief)
    write_json(assets / "editable" / f"{asset_id}.bbmodel", bbmodel)
    write_json(assets / "export/models" / f"{asset_id}.geo.json", geometry)
    write_json(assets / "export/animations" / f"{asset_id}.animation.json", animations)
    texture = assets / "export/textures" / f"{asset_id}.png"
    texture.parent.mkdir(parents=True, exist_ok=True)
    texture.write_bytes(b"fixture-png-bytes")


class WhisperwoodImporterTests(unittest.TestCase):
    def test_normalizes_valid_custom_asset_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            make_asset(
                root,
                "test_creature",
                locators=["effect"],
                clips=["walk"],
                native_locators=["effect"],
                exported_locators=["effect"],
                exported_clips=["walk"],
            )
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            one = IMPORTER.import_packet(root, first)
            two = IMPORTER.import_packet(root, second)
            self.assertEqual(one, two)
            self.assertEqual(one["status"], "STATIC_STAGING_COMPLETE")
            geo = json.loads((first / "promotable/creatures/test_creature/geometry/test_creature.geo.json").read_text())
            self.assertEqual(geo["minecraft:geometry"][0]["description"]["identifier"], "geometry.aionbound.test_creature")
            anim = json.loads((first / "promotable/creatures/test_creature/animations/test_creature.animation.json").read_text())
            self.assertEqual(list(anim["animations"]), ["animation.aionbound.test_creature.walk"])
            model = json.loads((first / "promotable/creatures/test_creature/editable/test_creature.bbmodel").read_text())
            self.assertEqual(model["textures"][0]["path"], "../textures/test_creature.png")
            self.assertEqual(
                sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file()),
                sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file()),
            )
            for relative in (path.relative_to(first) for path in first.rglob("*") if path.is_file()):
                self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes())

    def test_withholds_custom_asset_missing_locator_and_role_clip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            make_asset(root, "blocked_mob", locators=["effect"], clips=["walk"])
            stage = Path(tmp) / "stage"
            manifest = IMPORTER.import_packet(root, stage)
            record = manifest["assets"][0]
            self.assertEqual(record["disposition"], "NATIVE_REPAIR_REQUIRED_CUSTOM_GEOMETRY")
            self.assertIn("MISSING_NATIVE_BBMODEL_LOCATORS:effect", record["blockers"])
            self.assertIn("MISSING_EXPORTED_GEOMETRY_LOCATORS:effect", record["blockers"])
            self.assertIn("MISSING_REQUIRED_ROLE_CLIPS:walk", record["blockers"])
            self.assertFalse((stage / "promotable").exists())

    def test_withholds_ambiguous_related_asset_even_for_simple_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            make_asset(root, "safe_item", profile="item", related_assets="forest flavor text", flat_icon=True)
            stage = Path(tmp) / "stage"
            manifest = IMPORTER.import_packet(root, stage)
            record = manifest["assets"][0]
            self.assertEqual(record["disposition"], "BLOCKED_SIMPLE_ASSET")
            self.assertEqual(record["blockers"], ["AMBIGUOUS_RELATED_ASSETS"])
            self.assertFalse((stage / "promotable").exists())

    def test_stages_simple_item_without_custom_geometry_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            make_asset(root, "drop_item", profile="item", flat_icon=True)
            stage = Path(tmp) / "stage"
            manifest = IMPORTER.import_packet(root, stage)
            record = manifest["assets"][0]
            self.assertEqual(record["disposition"], "PROMOTABLE_SIMPLE_TEXTURE_ITEM_BLOCKBENCH_NOT_APPLICABLE")
            self.assertEqual(record["blockers"], [])
            self.assertTrue((stage / "promotable/resources/drop_item/textures/drop_item.png").is_file())
            self.assertFalse((stage / "promotable/resources/drop_item/geometry").exists())

    def test_item_uv_atlas_is_not_assumed_to_be_an_inventory_icon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            make_asset(root, "modeled_drop", profile="item", locators=["effect"])
            stage = Path(tmp) / "stage"
            manifest = IMPORTER.import_packet(root, stage)
            record = manifest["assets"][0]
            self.assertEqual(record["disposition"], "NATIVE_REPAIR_REQUIRED_CUSTOM_GEOMETRY")
            self.assertIn("MISSING_NATIVE_BBMODEL_LOCATORS:effect", record["blockers"])
            self.assertFalse((stage / "promotable").exists())

    def test_rejects_nonempty_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            make_asset(root, "drop_item", profile="item", flat_icon=True)
            stage = Path(tmp) / "stage"
            stage.mkdir()
            (stage / "owned.txt").write_text("user data", encoding="utf-8")
            with self.assertRaises(IMPORTER.ImportFailure):
                IMPORTER.import_packet(root, stage)
            self.assertEqual((stage / "owned.txt").read_text(encoding="utf-8"), "user data")


if __name__ == "__main__":
    unittest.main()
