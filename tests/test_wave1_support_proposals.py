import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPOSALS = ROOT / "engineering" / "authority" / "support-proposals"
TICKET_FILES = {
    "W1-CREATIVE-001": PROPOSALS / "W1-CREATIVE-001" / "nonwarehouse_identity_proposal.json",
    "W1-CREATIVE-003": PROPOSALS / "W1-CREATIVE-003" / "thorn_court_behavior_proposal.json",
    "W1-CREATIVE-004": PROPOSALS / "W1-CREATIVE-004" / "loot_envelope_proposal.json",
    "W1-CREATIVE-005": PROPOSALS / "W1-CREATIVE-005" / "sidegrade_identity_proposal.json",
    "W1-CREATIVE-006": PROPOSALS / "W1-CREATIVE-006" / "whisperwood_sapling_regrowth_proposal.json",
}


def load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def all_runtime_ids(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from all_runtime_ids(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_runtime_ids(item)
    elif isinstance(value, str):
        yield from re.findall(r"aionbound:[a-z0-9_]+", value)


class SupportProposalTests(unittest.TestCase):
    def test_declared_schema_matches_enforced_contract(self):
        schema = load(PROPOSALS / "schema" / "support_proposal.schema.json")
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["status"]["const"], "PROPOSED_NOT_RATIFIED")
        self.assertEqual(schema["properties"]["authority_effect"]["const"], "NONE_UNTIL_RATIFIED")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            set(schema["required"]),
            {"ticket_id", "status", "schema_version", "authority_effect", "source_authorities", "proposal", "approval_required"},
        )

    def test_index_is_exact_and_nonbinding(self):
        index = load(PROPOSALS / "PROPOSAL_INDEX.json")
        self.assertEqual(index["status"], "PROPOSED_NOT_RATIFIED")
        self.assertEqual(index["tickets"], list(TICKET_FILES))
        self.assertEqual(index["binding_effect"], "NONE_UNTIL_HUMAN_OR_CREATIVE_APPROVAL_AND_REPLACEMENT_LEDGER")

    def test_common_schema_contract(self):
        for ticket, path in TICKET_FILES.items():
            with self.subTest(ticket=ticket):
                proposal = load(path)
                self.assertEqual(proposal["ticket_id"], ticket)
                self.assertEqual(proposal["status"], "PROPOSED_NOT_RATIFIED")
                self.assertEqual(proposal["schema_version"], 1)
                self.assertEqual(proposal["authority_effect"], "NONE_UNTIL_RATIFIED")
                self.assertTrue(proposal["source_authorities"])
                self.assertIsInstance(proposal["proposal"], dict)
                self.assertTrue(proposal["approval_required"])
                decision_ids = [row["decision_id"] for row in proposal["approval_required"]]
                self.assertEqual(len(decision_ids), len(set(decision_ids)))

    def test_json_is_canonically_formatted_and_ids_are_namespaced(self):
        for path in [PROPOSALS / "PROPOSAL_INDEX.json", *TICKET_FILES.values()]:
            with self.subTest(path=path.name):
                value = load(path)
                expected = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
                self.assertEqual(path.read_text(encoding="utf-8"), expected)
                for runtime_id in all_runtime_ids(value):
                    self.assertRegex(runtime_id, r"^aionbound:[a-z0-9_]+$")

    def test_new_and_sibling_ids_are_unique(self):
        identities = load(TICKET_FILES["W1-CREATIVE-001"])["proposal"]
        sidegrades = load(TICKET_FILES["W1-CREATIVE-005"])["proposal"]
        ids = [row["id"] for row in identities["new_required_items"]]
        ids += [row["id"] for row in sidegrades["sibling_sidegrades"]]
        ids += [row["id"] for row in sidegrades["sibling_unique_finishes"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(identities["new_required_items"]), 9)

    def test_ticketed_nonwarehouse_terms_have_dispositions(self):
        identities = load(TICKET_FILES["W1-CREATIVE-001"])["proposal"]
        classified = {row["term"] for row in identities["new_required_items"]}
        for row in identities["aliases"]:
            classified.update(row["terms"])
        classified.update(identities["narrative_codex_only"])
        classified.update(identities["removed_or_context_only"])
        expected = {
            "Boar Tusk", "Boar Tusk Shard", "Root Plate", "Thick Hide", "Briar Crown",
            "Rot Fang", "Tainted Pelt", "Marrow Scrap", "Thorn Barb", "Stalker Claw",
            "Hollow Venom Sac", "Chitin Shard", "Wraith Mask Fragment", "Mosskip Crown Fragment",
            "Hardened Moss Plate", "Glow Soft Pellet", "Lantern-adjacent hide scrap", "Ash Dust",
            "Ash Wool", "Beetle Core Fragment", "Char Feather", "Char Hide", "Char Pelt",
            "Cinder Beak", "Cinder Pelt", "Drake Scale", "Ember Fang", "Ember Sinew",
            "Heat Scale", "Lynx Claw", "Mite Mandible", "Pack Cinder Mark", "Ram Horn Curve",
            "Shell Plate", "Smolder Gland", "Soot Antler", "Stag Heart Cinder",
            "Swarm Queen Scale", "Warm Blood Vial", "Algae Scrap", "Bog Tendril",
            "Crab Pearl Grain", "Croc Eye Pearl", "Croc Hide", "Glass Feather",
            "Heron Nest Token", "Iridescent Dust", "Long Beak Shard", "Marsh Resin Blob",
            "Mire Shell Plate", "Newt Tail Crystal", "Prism Mucus", "Prism Wing",
            "Serpent Scale", "Shed Skin Ribbon", "Silt Fang", "Tiny Prism Chip",
            "Venom Crystal", "Watcher Lens", "Wight Shroud", "Wight Shroud Cloth",
            "Cliff Hoof Keratin", "Dense Muscle Strip", "Drake Membrane", "Fox Whisker Cord",
            "Gale Membrane", "Glide Scale", "Hawk Talon", "Navigation Oil", "Nest Crown Plume",
            "Nest Twig", "Ram Horn Spiral", "Roc Primary Feather", "Ropewing Membrane",
            "Ruin Talon", "Sky Ruin Key Fragment", "Soft Sky Fur", "Stone Beak",
            "Storm Salt", "Vulture Crop Stone", "Wing Bone Stay", "Concord Spark",
            "Drowned Choir Tablet", "Hunter's Final Page", "Perfect Prism Pearl",
            "Sky Ruin Master Key", "Surviving Smith's Notes"
        }
        self.assertEqual(expected - classified, set())

    def test_thorn_court_thresholds_and_caps_are_bounded(self):
        proposal = load(TICKET_FILES["W1-CREATIVE-003"])["proposal"]
        phases = proposal["phases"]
        self.assertEqual([row["enter_at_health_fraction"] for row in phases], [1.0, 0.70, 0.35, 0.10])
        self.assertEqual([row["exit_at_health_fraction"] for row in phases], [0.70, 0.35, 0.10, 0.0])
        self.assertLessEqual(max(row["add_cap"] for row in phases), proposal["multiplayer"]["global_session_add_cap"])
        self.assertLessEqual(proposal["health"]["participant_cap"], 4)

    def test_loot_intervals_are_closed_probabilities_and_positive_quantities(self):
        envelopes = load(TICKET_FILES["W1-CREATIVE-004"])["proposal"]["probability_and_quantity_envelopes"]
        for rarity, envelope in envelopes.items():
            with self.subTest(rarity=rarity):
                for key, bounds in envelope.items():
                    if key.startswith("chance"):
                        self.assertEqual(len(bounds), 2)
                        self.assertLessEqual(0.0, bounds[0])
                        self.assertLessEqual(bounds[0], bounds[1])
                        self.assertLessEqual(bounds[1], 1.0)
                    elif key in {"quantity", "rolls"}:
                        self.assertEqual(len(bounds), 2)
                        self.assertGreaterEqual(bounds[0], 1)
                        self.assertLessEqual(bounds[0], bounds[1])

    def test_alternate_seal_is_unambiguous(self):
        resolution = load(TICKET_FILES["W1-CREATIVE-004"])["proposal"]["alternate_seal_resolution"]
        self.assertFalse(resolution["briar_elk_trophy_replaces_thorn_stalker_skull"])
        self.assertFalse(resolution["mosskip_trophy_replaces_thorn_stalker_skull"])
        self.assertEqual(resolution["chapter_1_critical_seal"], "aionbound:thorn_stalker_skull")

    def test_sapling_regrowth_uses_only_existing_whisperwood_blocks(self):
        proposal = load(TICKET_FILES["W1-CREATIVE-006"])["proposal"]
        self.assertEqual(proposal["new_inventory_identities"], [])
        self.assertEqual(
            set(proposal["assembly_palette"]),
            {
                "aionbound:whisperwood_log",
                "aionbound:whisperwood_leaves",
                "aionbound:whisperwood_roots",
                "aionbound:moss_bark",
            },
        )
        self.assertLessEqual(proposal["growth_envelope"]["maximum_loaded_minutes"], 30)
        self.assertEqual(proposal["blocked_growth_behavior"], "retain_sapling_and_retry_later")


if __name__ == "__main__":
    unittest.main()
