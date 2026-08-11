import importlib.util
import json
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "validate_wave1", REPO / "tools" / "validate_wave1.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(VALIDATOR)


def load(relative: str):
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


class ClosureRemediationTests(unittest.TestCase):
    def test_successor_validator_passes(self):
        self.assertEqual(VALIDATOR.validate(REPO)["status"], "PASS")

    def test_optional_attachables_are_retired_without_fabricated_geometry(self):
        for asset_id in ("burrowgate_key", "waykeeper_whistle"):
            self.assertFalse(
                (REPO / f"resource_pack/attachables/{asset_id}.attachable.json").exists()
            )
            self.assertFalse(
                (REPO / f"resource_pack/models/aionbound/{asset_id}.geo.json").exists()
            )
            self.assertTrue(
                (REPO / f"resource_pack/textures/aionbound/{asset_id}.png").is_file()
            )

    def test_material_aliases_reuse_existing_paths(self):
        atlas = load("resource_pack/textures/terrain_texture.json")["texture_data"]
        expected = {
            "chaos_crate_prime": "textures/aionbound/chaos_crate_prime",
            "spiral_moth_spire_nest": "textures/aionbound/spiral_moth_spire_nest",
            "prismglass_chest_ruin": "textures/aionbound/prismglass_chest_ruin",
            "first_waystation_arch": "textures/aionbound/first_waystation_arch",
        }
        for alias, path in expected.items():
            self.assertEqual(atlas[alias]["textures"], path)
            self.assertTrue((REPO / "resource_pack" / f"{path}.png").is_file())

    def test_mosskip_reuses_existing_complete_asset_triple(self):
        description = load("resource_pack/entity/mosskip.entity.json")[
            "minecraft:client_entity"
        ]["description"]
        self.assertEqual(
            description["geometry"]["default"], "geometry.aionbound.mosskip_trail"
        )
        self.assertEqual(
            description["textures"]["default"], "textures/aionbound/mosskip_trail"
        )
        self.assertEqual(
            description["animations"]["move"],
            "animation.aionbound.mosskip_trail.idle",
        )

    def test_barkling_has_explicit_no_drop_semantics(self):
        self.assertEqual(
            load("behavior_pack/loot_tables/entities/barkling_familiar.json"),
            {"pools": []},
        )


if __name__ == "__main__":
    unittest.main()
