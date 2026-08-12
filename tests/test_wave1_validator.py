import importlib.util
import json
from pathlib import Path
import struct
import subprocess
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
            "blocks": ["aionbound:new_block"], "items": ["aionbound:new_item"], "recipes": [], "structures": [],
            "features": [], "feature_rules": [],
        },
        "minimum_engine_version": [1, 21, 80],
        "allowed_script_modules": ["@minecraft/server", "@minecraft/server-ui"],
        "allowed_script_module_versions": {"@minecraft/server": "2.0.0", "@minecraft/server-ui": "2.0.0"},
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
    (rp / "texts").mkdir(parents=True)
    (rp / "texts" / "en_US.lang").write_text(
        "item.aionbound:new_item=New Item\n"
        "tile.aionbound:new_block.name=New Block\n",
        encoding="utf-8",
    )
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

    def require_fixture_content_closure(self):
        item_path = self.root / "behavior_pack/items/new_item.item.json"
        item = json.loads(item_path.read_text())
        item["minecraft:item"]["components"]["minecraft:icon"] = {
            "textures": {"default": "new_item"}
        }
        write_json(item_path, item)
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_content_closure"] = {
            "items": [{
                "identifier": "aionbound:new_item",
                "definition": "behavior_pack/items/new_item.item.json",
                "atlas_key": "new_item",
                "texture": "textures/items/new_item",
                "png_sha256": VALIDATOR.sha256(
                    self.root / "resource_pack/textures/items/new_item.png"
                ),
                "lang_key": "item.aionbound:new_item",
            }],
            "blocks": [{
                "identifier": "aionbound:new_block",
                "definition": "behavior_pack/blocks/new_block.block.json",
                "atlas_key": "new_block",
                "texture": "textures/blocks/new_block",
                "png_sha256": VALIDATOR.sha256(
                    self.root / "resource_pack/textures/blocks/new_block.png"
                ),
                "lang_key": "tile.aionbound:new_block.name",
            }],
        }
        write_json(authority_path, authority)

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

    def test_required_content_closure_emits_definition_atlas_lang_and_png_hash_receipts(self):
        self.require_fixture_content_closure()
        receipts = VALIDATOR.validate(self.root)["required_content_closure_receipts"]
        self.assertEqual([row["identifier"] for row in receipts], [
            "aionbound:new_item", "aionbound:new_block",
        ])
        self.assertTrue(all(len(row["definition_sha256"]) == 64 for row in receipts))
        self.assertTrue(all(len(row["atlas_sha256"]) == 64 for row in receipts))
        self.assertTrue(all(len(row["lang_sha256"]) == 64 for row in receipts))
        self.assertTrue(all(len(row["png_sha256"]) == 64 for row in receipts))
        self.assertEqual(receipts[0]["lang_value"], "New Item")

    def test_required_content_closure_fails_on_lang_atlas_or_png_hash_drift(self):
        self.require_fixture_content_closure()
        lang_path = self.root / "resource_pack/texts/en_US.lang"
        lang_path.write_text("tile.aionbound:new_block.name=New Block\n", encoding="utf-8")
        atlas_path = self.root / "resource_pack/textures/item_texture.json"
        atlas = json.loads(atlas_path.read_text())
        atlas["texture_data"]["new_item"]["textures"] = "textures/items/wrong"
        write_json(atlas_path, atlas)
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_content_closure"]["blocks"][0]["png_sha256"] = "0" * 64
        write_json(authority_path, authority)
        findings = self.findings()
        self.assertIn(
            "content_closure_missing_lang:aionbound:new_item:item.aionbound:new_item",
            findings,
        )
        self.assertTrue(any(value.startswith(
            "content_closure_atlas_path:items:aionbound:new_item:"
        ) for value in findings))
        self.assertTrue(any(value.startswith(
            "content_closure_png_sha256:aionbound:new_block:"
        ) for value in findings))

    def test_required_native_evidence_is_hash_bound_and_narrowly_classified(self):
        evidence_path = self.root / "engineering/native/report.json"
        write_json(evidence_path, {
            "status": "PASS_NATIVE_REPAIR_GATE",
            "scope": ["one"],
            "totals": {"assets": 1},
        })
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_evidence_artifacts"] = [{
            "path": "engineering/native/report.json",
            "sha256": VALIDATOR.sha256(evidence_path),
            "classification": "native_editable_asset_evidence_only_not_bp_rp_or_client_proof",
            "required_json_values": {
                "status": "PASS_NATIVE_REPAIR_GATE",
                "totals.assets": 1,
            },
            "required_scope": ["one"],
        }]
        write_json(authority_path, authority)
        report = VALIDATOR.validate(self.root)
        self.assertEqual(
            report["required_evidence_artifacts_verified"][0]["classification"],
            "native_editable_asset_evidence_only_not_bp_rp_or_client_proof",
        )
        self.assertIn(
            "native_evidence_artifact_presence_and_hash_only_not_bp_rp_or_client_proof",
            report["proof_boundaries"],
        )
        write_json(evidence_path, {"status": "FAIL", "scope": ["one"], "totals": {"assets": 1}})
        self.assertTrue(any(value.startswith(
            "required_evidence_artifact_sha256:engineering/native/report.json:"
        ) for value in self.findings()))

    def test_required_artifact_manifest_is_exact_hash_bound_and_reports_groups(self):
        source = self.root / "behavior_pack/items/new_item.item.json"
        manifest_path = self.root / "engineering/validation/wave1/exact.json"
        write_json(manifest_path, {
            "schema": "test.exact.v1",
            "groups": {"implemented": [{"path": "behavior_pack/items/new_item.item.json", "sha256": VALIDATOR.sha256(source)}]},
            "pending_follow_up": {"equipment": []},
        })
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_artifact_manifest"] = {
            "path": "engineering/validation/wave1/exact.json",
            "sha256": VALIDATOR.sha256(manifest_path),
            "schema": "test.exact.v1",
            "classification": "source_tree_hash_closure_only",
        }
        write_json(authority_path, authority)
        receipt = VALIDATOR.validate(self.root)["required_artifact_manifest_verified"]
        self.assertEqual(receipt["groups"], {"implemented": 1})
        source.write_text(source.read_text() + "\n", encoding="utf-8")
        self.assertTrue(any(value.startswith(
            "required_source_artifact_sha256:implemented:behavior_pack/items/new_item.item.json:"
        ) for value in self.findings()))

    def test_required_artifact_manifest_rejects_parent_traversal(self):
        manifest_path = self.root / "engineering/validation/wave1/exact.json"
        write_json(manifest_path, {
            "schema": "test.exact.v1",
            "groups": {"implemented": [{"path": "../outside", "sha256": "0" * 64}]},
        })
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_artifact_manifest"] = {
            "path": "engineering/validation/wave1/exact.json",
            "sha256": VALIDATOR.sha256(manifest_path),
            "schema": "test.exact.v1",
        }
        write_json(authority_path, authority)
        self.assertIn("unsafe_required_source_artifact_path:implemented:../outside", self.findings())

    def test_repository_authority_names_exact_ashen_resource_and_full_cube_block_sets(self):
        authority = json.loads((REPO / VALIDATOR.AUTHORITY_REL).read_text())
        expected_items = {
            "aionbound:ash_crystal", "aionbound:basalt_core", "aionbound:charbone",
            "aionbound:ember_resin", "aionbound:fire_bloom_seed", "aionbound:furnace_chitin",
            "aionbound:heatstone", "aionbound:smolder_bark", "aionbound:sulfur_cluster",
            "aionbound:volcanic_glass_shard",
        }
        expected_blocks = {
            "aionbound:ash_log", "aionbound:ash_soil", "aionbound:basalt_brick",
            "aionbound:basalt_pillar", "aionbound:char_planks", "aionbound:cinder_gravel",
            "aionbound:ember_moss", "aionbound:heat_bark", "aionbound:smolder_stone",
            "aionbound:volcanic_glass_block",
        }
        self.assertTrue(expected_items.issubset(authority["required_successor_ids"]["items"]))
        self.assertTrue(expected_blocks.issubset(authority["required_successor_ids"]["blocks"]))
        self.assertEqual(
            {row["identifier"] for row in authority["required_content_closure"]["items"]},
            expected_items,
        )
        self.assertEqual(
            {row["identifier"] for row in authority["required_content_closure"]["blocks"]},
            expected_blocks,
        )
        self.assertGreaterEqual(authority["minimum_inventory"]["items"], 56)
        self.assertGreaterEqual(authority["minimum_inventory"]["blocks"], 49)

    def test_repository_ashen_closure_manifest_is_deterministic_complete_and_narrow(self):
        authority = json.loads((REPO / VALIDATOR.AUTHORITY_REL).read_text())
        manifest_path = REPO / authority["required_artifact_manifest"]["path"]
        before = manifest_path.read_bytes()
        subprocess.run(
            ["python3", "engineering/validation/wave1/build_ashen_implemented_closure.py"],
            cwd=REPO, check=True,
        )
        self.assertEqual(manifest_path.read_bytes(), before)
        self.assertEqual(VALIDATOR.sha256(manifest_path), authority["required_artifact_manifest"]["sha256"])
        manifest = json.loads(before)
        self.assertEqual({name: len(rows) for name, rows in manifest["groups"].items()}, {
            "resources_blocks_plants": 53,
            "entity_client_spawn_runtime": 30,
            "ecology_structures_features_rules": 53,
            "loot_and_acquisition_economy": 44,
            "decision_ledger_v3_and_codex_runtime": 12,
            "equipment_13_plus_derived_4_and_crafting": 104,
            "kiln_sky_dedicated_service_activation_withheld": 6,
            "functional_equipment_dedicated_activation_withheld": 9,
            "native_aggregate_receipts": 5,
        })
        paths = [row["path"] for rows in manifest["groups"].values() for row in rows]
        self.assertEqual(316, len(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual("WITHHELD_BY_DEDICATED_EVIDENCE", manifest["pending_follow_up"]["kiln_sky_shared_runtime_activation"])
        self.assertEqual("WITHHELD_BY_DEDICATED_EVIDENCE", manifest["pending_follow_up"]["functional_equipment_shared_runtime_activation"])
        self.assertEqual("W1-CREATIVE-005_DEFERRED", manifest["pending_follow_up"]["creative"])
        self.assertIn("NO BUILD, PACKAGE, BDS, CLIENT", manifest["proof_boundary"])

    def test_repository_crystal_closure_manifest_is_deterministic_complete_and_narrow(self):
        authority = json.loads((REPO / VALIDATOR.AUTHORITY_REL).read_text())
        requirement = authority["additional_required_artifact_manifests"][0]
        manifest_path = REPO / requirement["path"]
        before = manifest_path.read_bytes()
        subprocess.run(
            ["python3", "engineering/validation/wave1/build_crystal_implemented_closure.py"],
            cwd=REPO, check=True,
        )
        self.assertEqual(manifest_path.read_bytes(), before)
        self.assertEqual(VALIDATOR.sha256(manifest_path), requirement["sha256"])
        manifest = json.loads(before)
        self.assertEqual({name: len(rows) for name, rows in manifest["groups"].items()}, {
            "resources_and_full_cube_blocks": 44,
            "plants_and_bounded_ecology": 52,
            "creature_ai_client_motion_spawn_and_loot_binding": 80,
            "structures_world_discovery_and_protected_cache_binding": 34,
            "loot_crafting_and_acquisition_economy": 53,
            "equipment_presentation_and_existing_handler_roles": 72,
            "codex_progression_pearl_depths_persistence_and_shared_composition": 17,
            "shared_atlas_localization_and_block_registry": 4,
            "native_editable_asset_aggregate_receipts": 4,
        })
        paths = [row["path"] for rows in manifest["groups"].values() for row in rows]
        self.assertEqual(360, len(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(4, manifest["invariants"]["persistence_schema"])
        self.assertEqual(40, manifest["invariants"]["natural_entity_target"])
        self.assertEqual(["aionbound:marsh_wight"], manifest["invariants"]["natural_spawn_exclusions"])
        self.assertFalse(manifest["invariants"]["ashen_dormant_service_activation"])
        self.assertIn("NO BUILD, PACKAGE, BDS, CLIENT", manifest["proof_boundary"])

    def test_repository_ashen_ids_and_growth_floors_cover_current_implementation(self):
        authority = json.loads((REPO / VALIDATOR.AUTHORITY_REL).read_text())
        required = {key: set(value) for key, value in authority["required_successor_ids"].items()}
        creatures = {f"aionbound:{value}" for value in (
            "ash_drake", "ash_mite", "ash_ram", "basalt_tortoise", "char_wolf",
            "cinder_lynx", "ember_crow", "furnace_beetle", "magma_lizard", "soot_stag",
        )}
        self.assertTrue(creatures.issubset(required["entities"]))
        self.assertEqual(creatures, required["client_entities"])
        self.assertEqual(creatures - {"aionbound:ash_drake"}, required["spawn_rules"])
        self.assertTrue({"aionbound:ash_drake_horn", "aionbound:ember_forge_core"}.issubset(required["blocks"]))
        equipment_and_derived_items = {f"aionbound:{value}" for value in (
            "basalt_hammer", "ember_great_axe", "ash_repeater", "ashen_helmet",
            "ashen_chest", "ashen_legs", "ashen_boots", "basalt_pick", "ember_hammer",
            "ore_chisel", "ember_totem", "heat_core", "heavy_head", "chitin_plate", "ember_heart",
        )}
        self.assertTrue(equipment_and_derived_items.issubset(required["items"]))
        self.assertEqual(authority["minimum_inventory"], {
            "blocks": 97, "entities": 44, "client_entities": 44, "items": 118,
            "loot_tables": 110, "recipes": 101, "spawn_rules": 29, "structures": 34,
            "features": 76, "feature_rules": 75, "attachables": 60, "geometries": 144,
            "animations": 266, "animation_controllers": 21, "render_controllers": 21,
            "png_files": 307, "script_files": 26,
        })

    def test_repository_functional_equipment_evidence_is_exact_and_activation_withheld(self):
        authority = json.loads((REPO / VALIDATOR.AUTHORITY_REL).read_text())
        evidence = next(
            row for row in authority["required_evidence_artifacts"]
            if row["path"].endswith("ASHEN_EQUIPMENT_FUNCTIONAL_EVIDENCE.json")
        )
        path = REPO / evidence["path"]
        document = json.loads(path.read_text())
        self.assertEqual("3b68295e4ef5f282537e0110e35292898536f1496e764494153926d40477883e", VALIDATOR.sha256(path))
        self.assertEqual("DEDICATED_SERVICE_AND_DECLARATIVE_COMPONENTS_PASS_ACTIVATION_WITHHELD", document["status"])
        self.assertTrue(document["proof"]["declarative_components"])
        self.assertTrue(document["proof"]["dedicated_service_semantics"])
        self.assertFalse(document["proof"]["shared_runtime_activation"])
        self.assertEqual("DEFERRED", document["preserved_boundaries"]["W1-CREATIVE-005"])

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

    def test_required_successor_structure_is_named_not_counted(self):
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_successor_ids"]["structures"] = ["aionbound:hunter_camp"]
        write_json(authority_path, authority)
        self.assertIn(
            "missing_required_successor_id:structures:aionbound:hunter_camp",
            self.findings(),
        )

    def test_required_successor_feature_and_rule_are_named(self):
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_successor_ids"]["features"] = ["aionbound:forest_node"]
        authority["required_successor_ids"]["feature_rules"] = ["aionbound:forest_node.feature_rule"]
        write_json(authority_path, authority)
        findings = self.findings()
        self.assertIn("missing_required_successor_id:features:aionbound:forest_node", findings)
        self.assertIn("missing_required_successor_id:feature_rules:aionbound:forest_node.feature_rule", findings)

    def test_required_successor_client_entity_and_spawn_rule_are_named(self):
        authority_path = self.root / VALIDATOR.AUTHORITY_REL
        authority = json.loads(authority_path.read_text())
        authority["required_successor_ids"]["client_entities"] = ["aionbound:missing_client"]
        authority["required_successor_ids"]["spawn_rules"] = ["aionbound:missing_spawn"]
        write_json(authority_path, authority)
        findings = self.findings()
        self.assertIn("missing_required_successor_id:client_entities:aionbound:missing_client", findings)
        self.assertIn("missing_required_successor_id:spawn_rules:aionbound:missing_spawn", findings)

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

    def test_duplicate_shapeless_ingredient_multiset_fails(self):
        for name, identifier, ingredients in (
            ("first.json", "aionbound:first_recipe", ["minecraft:stick", "minecraft:apple"]),
            ("second.json", "aionbound:second_recipe", ["minecraft:apple", "minecraft:stick"]),
        ):
            write_json(self.root / "behavior_pack/recipes" / name, {
                "format_version": "1.20.10",
                "minecraft:recipe_shapeless": {
                    "description": {"identifier": identifier},
                    "tags": ["crafting_table"],
                    "ingredients": [{"item": item} for item in ingredients],
                    "result": {"item": "aionbound:new_item"},
                },
            })
        self.assertTrue(any(
            value.startswith("duplicate_recipe_ingredients:")
            for value in self.findings()
        ))

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

    def test_exact_stable_server_ui_dependency_and_import_are_allowed(self):
        path = self.root / "behavior_pack/manifest.json"
        document = json.loads(path.read_text())
        document["dependencies"].append({"module_name": "@minecraft/server-ui", "version": "2.0.0"})
        write_json(path, document)
        (self.root / "behavior_pack/scripts/main.js").write_text(
            'import { world } from "@minecraft/server";\nimport { ActionFormData } from "@minecraft/server-ui";\nvoid world; void ActionFormData;\n',
            encoding="utf-8",
        )
        self.assertEqual(VALIDATOR.validate(self.root)["status"], "PASS")

    def test_unapproved_server_ui_version_fails_closed(self):
        path = self.root / "behavior_pack/manifest.json"
        document = json.loads(path.read_text())
        document["dependencies"].append({"module_name": "@minecraft/server-ui", "version": "2.1.0"})
        write_json(path, document)
        self.assertIn(
            "manifest_unapproved_script_module_version:@minecraft/server-ui:2.1.0!=2.0.0",
            self.findings(),
        )

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

    def test_attachable_may_be_backed_by_a_placeable_inventory_block(self):
        write_json(self.root / "resource_pack/attachables/new_block.attachable.json", {
            "format_version": "1.10.0",
            "minecraft:attachable": {"description": {"identifier": "aionbound:new_block"}},
        })
        self.assertEqual(VALIDATOR.validate(self.root)["status"], "PASS")

    def test_attachable_without_item_or_block_still_fails(self):
        write_json(self.root / "resource_pack/attachables/orphan.attachable.json", {
            "format_version": "1.10.0",
            "minecraft:attachable": {"description": {"identifier": "aionbound:orphan"}},
        })
        self.assertIn("attachable_without_item_or_block:aionbound:orphan", self.findings())


if __name__ == "__main__":
    unittest.main()
