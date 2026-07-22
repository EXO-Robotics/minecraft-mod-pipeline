from __future__ import annotations

import unittest

from mccompiler.api_catalog import ApiCatalog
from mccompiler.targets import DEFAULT_TARGET, get_target


class TargetProfileTests(unittest.TestCase):
    def test_marketplace_is_default_and_excludes_extended_capabilities(self) -> None:
        target = get_target(None)
        self.assertEqual(DEFAULT_TARGET, "MARKETPLACE_ADDON_STABLE")
        self.assertTrue(target.production)
        self.assertTrue(target.scripts)
        self.assertTrue(target.stable_scripts_only)
        self.assertFalse(target.external_services)
        self.assertFalse(target.bds_only_modules)
        self.assertFalse(target.experiments)
        self.assertFalse(target.debug_content)

    def test_data_only_rejects_scripts(self) -> None:
        self.assertFalse(get_target("DATA_ONLY_FALLBACK").scripts)

    def test_unknown_target_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown target profile"):
            get_target("MAGICAL_CONSOLE")


class ApiCatalogTests(unittest.TestCase):
    def test_versions_resolve_independently_per_module(self) -> None:
        catalog = ApiCatalog.load_default()
        versions, evidence = catalog.resolve_versions(
            [
                ("@minecraft/server", "world.afterEvents.itemUse"),
                ("@minecraft/server-ui", "ActionFormData"),
            ],
            marketplace=True,
        )
        self.assertEqual(versions["@minecraft/server"], "2.0.0")
        self.assertEqual(versions["@minecraft/server-ui"], "2.0.0")
        self.assertEqual(len(evidence), 2)

    def test_unknown_symbol_fails_instead_of_silent_fallback(self) -> None:
        catalog = ApiCatalog.load_default()
        with self.assertRaisesRegex(ValueError, "uncatalogued Script API symbol"):
            catalog.resolve_versions(
                [("@minecraft/server", "world.afterEvents.imaginaryEvent")],
                marketplace=True,
            )

    def test_stable_before_events_are_catalogued_at_their_introduction_versions(self) -> None:
        catalog = ApiCatalog.load_default()
        versions, evidence = catalog.resolve_versions([
            ("@minecraft/server", "world.beforeEvents.playerInteractWithBlock"),
            ("@minecraft/server", "world.beforeEvents.playerBreakBlock"),
        ], marketplace=True)
        self.assertEqual("1.15.0", versions["@minecraft/server"])
        self.assertEqual({"world.beforeEvents.playerInteractWithBlock", "world.beforeEvents.playerBreakBlock"}, {row["symbol"] for row in evidence})
        self.assertTrue(all(row["stability"] == "stable" and not row["experiments_required"] for row in evidence))
        self.assertTrue(all(row["restricted_execution"] for row in evidence))
        self.assertTrue(all(str(row["source_documentation"]).startswith("https://learn.microsoft.com/") for row in evidence))


if __name__ == "__main__":
    unittest.main()
