import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_wave1", REPO / "tools" / "validate_wave1.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(VALIDATOR)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


PNG = (
    b"\x89PNG\r\n\x1a\n"
    + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00"))
    + png_chunk(b"IEND", b"")
)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def fixture(root: Path) -> None:
    bp, rp = root / "behavior_pack", root / "resource_pack"
    authority = {
        "schema_version": 1,
        "namespace": "aionbound",
        "minimum_inventory": {
            "blocks": 1, "entities": 0, "items": 1, "loot_tables": 0,
            "recipes": 0, "spawn_rules": 0, "structures": 0,
        },
        "required_successor_ids": {
            "blocks": ["aionbound:new_block"], "items": ["aionbound:new_item"], "recipes": [],
        },
        "minimum_engine_version": [1, 21, 80],
        "allowed_script_modules": ["@minecraft/server"],
    }
    write_json(root / VALIDATOR.AUTHORITY_REL, authority)
    bp_uuid, rp_uuid = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"
    bp_version = rp_version = [2, 0, 0]
    write_json(bp / "manifest.json", {
        "format_version": 2,
        "header": {"uuid": bp_uuid, "version": bp_version, "min_engine_version": [1, 21, 80]},
        "modules": [
            {"type": "data", "uuid": "33333333-3333-3333-3333-333333333333", "version": bp_version},
            {"type": "script", "language": "javascript", "entry": "scripts/main.js", "uuid": "44444444-4444-4444-4444-444444444444", "version": bp_version},
        ],
        "dependencies": [
            {"uuid": rp_uuid, "version": rp_version},
            {"module_name": "@minecraft/server", "version": "2.0.0"},
        ],
    })
    write_json(rp / "manifest.json", {
        "format_version": 2,
        "header": {"uuid": rp_uuid, "version": rp_version, "min_engine_version": [1, 21, 80]},
        "modules": [{"type": "resources", "uuid": "55555555-5555-5555-5555-555555555555", "version": rp_version}],
        "dependencies": [{"uuid": bp_uuid, "version": bp_version}],
    })
    write_json(bp / "items" / "new_item.item.json", {
        "format_version": "1.21.80",
        "minecraft:item": {"description": {"identifier": "aionbound:new_item"}, "components": {}},
    })
    write_json(bp / "blocks" / "new_block.block.json", {
        "format_version": "1.21.80",
        "minecraft:block": {
            "description": {"identifier": "aionbound:new_block"},
            "components": {
                "minecraft:geometry": "minecraft:geometry.full_block",
                "minecraft:material_instances": {"*": {"texture": "new_block"}},
            },
        },
    })
    write_json(rp / "textures" / "item_texture.json", {
        "resource_pack_name": "test", "texture_data": {"new_item": {"textures": "textures/items/new_item"}},
    })
    write_json(rp / "textures" / "terrain_texture.json", {
        "resource_pack_name": "test", "texture_data": {"new_block": {"textures": "textures/blocks/new_block"}},
    })
    (rp / "textures" / "items").mkdir(parents=True)
    (rp / "textures" / "blocks").mkdir(parents=True)
    (rp / "textures" / "items" / "new_item.png").write_bytes(PNG)
    (rp / "textures" / "blocks" / "new_block.png").write_bytes(PNG)
    (bp / "scripts").mkdir(parents=True)
    (bp / "scripts" / "main.js").write_text('import { world } from "@minecraft/server";\nvoid world;\n', encoding="utf-8")


class Wave1ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def findings(self):
        with self.assertRaises(VALIDATOR.ValidationFailure) as caught:
            VALIDATOR.validate(self.root)
        return caught.exception.findings

    def test_valid_successor_tree_passes_with_proof_boundaries(self):
        report = VALIDATOR.validate(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["inventory"]["items"], 1)
        self.assertIn("not_bedrock_schema_or_stable_bds_proof", report["proof_boundaries"])

    def test_growth_above_minimum_is_accepted_without_exact_count_assertion(self):
        original = json.loads((self.root / "behavior_pack/items/new_item.item.json").read_text())
        original["minecraft:item"]["description"]["identifier"] = "aionbound:second_item"
        write_json(self.root / "behavior_pack/items/second_item.item.json", original)
        atlas_path = self.root / "resource_pack/textures/item_texture.json"
        atlas = json.loads(atlas_path.read_text())
        atlas["texture_data"]["second_item"] = {"textures": "textures/items/new_item"}
        write_json(atlas_path, atlas)
        self.assertEqual(VALIDATOR.validate(self.root)["inventory"]["items"], 2)

    def test_malformed_json_fails_closed(self):
        (self.root / "behavior_pack/items/new_item.item.json").write_text("{", encoding="utf-8")
        self.assertTrue(any(value.startswith("malformed_json:") for value in self.findings()))

    def test_missing_explicit_successor_id_fails(self):
        (self.root / "behavior_pack/items/new_item.item.json").unlink()
        findings = self.findings()
        self.assertIn("missing_required_successor_id:items:aionbound:new_item", findings)
        self.assertIn("inventory_below_minimum:items:0<1", findings)

    def test_required_successor_recipe_is_named_not_counted(self):
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_successor_ids"]["recipes"] = ["aionbound:foundation_recipe"]
        write_json(authority_path, authority)
        self.assertIn(
            "missing_required_successor_id:recipes:aionbound:foundation_recipe",
            self.findings(),
        )

    def test_unresolved_recipe_reference_fails(self):
        write_json(self.root / "behavior_pack/recipes/bad.json", {
            "format_version": "1.20.10",
            "minecraft:recipe_shapeless": {
                "description": {"identifier": "aionbound:bad_recipe"},
                "ingredients": [{"item": "aionbound:missing"}],
                "result": {"item": "aionbound:new_item"},
            },
        })
        self.assertIn("unresolved_custom_item_reference:aionbound:missing", self.findings())

    def test_missing_texture_and_forbidden_runtime_fail(self):
        (self.root / "resource_pack/textures/items/new_item.png").unlink()
        (self.root / "behavior_pack/scripts/main.js").write_text(
            'import { world } from "@minecraft/server";\nconst fs = require("fs");\n', encoding="utf-8"
        )
        findings = self.findings()
        self.assertTrue(any(value.startswith("atlas_missing_texture:items:new_item") for value in findings))
        self.assertTrue(any(value.startswith("forbidden_runtime:commonjs_require:") for value in findings))
        self.assertTrue(any(value.startswith("forbidden_runtime:filesystem:") for value in findings))

    def test_manifest_dependency_must_match_exact_peer_version(self):
        path = self.root / "resource_pack/manifest.json"
        document = json.loads(path.read_text())
        document["dependencies"][0]["version"] = [9, 9, 9]
        write_json(path, document)
        self.assertIn("manifest_missing_exact_rp_to_bp_dependency", self.findings())

    def test_feature_references_must_resolve(self):
        write_json(self.root / "behavior_pack/features/bad.feature.json", {
            "format_version": "1.13.0",
            "minecraft:single_block_feature": {
                "description": {"identifier": "aionbound:bad_feature"},
                "places_block": "aionbound:missing_block",
            },
        })
        self.assertIn(
            "feature_missing_block:aionbound:bad_feature:aionbound:missing_block",
            self.findings(),
        )

    def test_attachable_model_references_must_resolve(self):
        write_json(self.root / "resource_pack/attachables/new_item.attachable.json", {
            "format_version": "1.10.0",
            "minecraft:attachable": {
                "description": {
                    "identifier": "aionbound:new_item",
                    "geometry": {"default": "geometry.aionbound.missing"},
                    "textures": {"default": "textures/items/new_item"},
                },
            },
        })
        self.assertIn(
            "attachable_missing_geometry:aionbound:new_item:geometry.aionbound.missing",
            self.findings(),
        )


if __name__ == "__main__":
    unittest.main()
