#!/usr/bin/env python3
"""Author the ratified Whisperwood loot, crafting, and acquisition economy.

This lane is intentionally declarative. Thorn Court session ownership, durable
reward entitlement, persistence, and physical trophy fulfillment belong to the
runtime/persistence lane. The files authored here give that lane bounded loot
tables to invoke; natural Thorn Stalkers can never roll the chapter trophy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
OUT = Path(__file__).resolve().parent


NEW_ITEMS = {
    "mosskip_crown_fragment": "Mosskip Crown Fragment",
    "thorn_barb": "Thorn Barb",
    "stalker_claw": "Stalker Claw",
    "hollow_venom_sac": "Hollow Venom Sac",
    "moss_bind_glue": "Moss Bind Glue",
    "amber_core": "Amber Core",
    "thorn_cord": "Thorn Cord",
    "cleaver_blank": "Cleaver Blank",
    "living_root_focus": "Living Root Focus",
}


def ingredient(item: str, count: int = 1) -> dict:
    value = {"item": item}
    if count != 1:
        value["count"] = count
    return value


RECIPES = {
    # Ratified derived components.
    "moss_bind_glue": ([ingredient("aionbound:moss_resin"), ingredient("aionbound:glow_spore")], "aionbound:moss_bind_glue"),
    "amber_core": ([ingredient("aionbound:hollow_amber"), ingredient("aionbound:moon_sap")], "aionbound:amber_core"),
    "thorn_cord": ([ingredient("aionbound:widow_silk"), ingredient("aionbound:briar_vine")], "aionbound:thorn_cord"),
    "cleaver_blank": ([ingredient("aionbound:briar_antler"), ingredient("aionbound:stalker_claw")], "aionbound:cleaver_blank"),
    "living_root_focus": ([ingredient("aionbound:root_heart"), ingredient("aionbound:amber_core")], "aionbound:living_root_focus"),
    # Five Packet 006 Whisperwood weapons.
    "mossfang_spear": ([ingredient("aionbound:pale_reed"), ingredient("aionbound:thorn_barb"), ingredient("aionbound:moss_bind_glue")], "aionbound:mossfang_spear"),
    "widow_fang_dagger": ([ingredient("aionbound:widow_silk", 2), ingredient("aionbound:hollow_venom_sac")], "aionbound:widow_fang_dagger"),
    "thorn_whip": ([ingredient("aionbound:thorn_cord"), ingredient("aionbound:thorn_barb")], "aionbound:thorn_whip"),
    "briar_cleaver": ([ingredient("aionbound:cleaver_blank"), ingredient("aionbound:moss_bind_glue")], "aionbound:briar_cleaver"),
    "moon_sap_staff": ([ingredient("aionbound:stripped_whisperwood_log"), ingredient("aionbound:living_root_focus"), ingredient("aionbound:moon_sap")], "aionbound:moon_sap_staff"),
    # Three tools. Vanilla inputs implement Creative's explicit stone/metal scrap words.
    "root_knife": ([ingredient("minecraft:stick"), ingredient("minecraft:flint")], "aionbound:root_knife"),
    "whisperwood_hatchet": ([ingredient("aionbound:whisperwood_planks", 2), ingredient("aionbound:moss_bind_glue"), ingredient("minecraft:cobblestone")], "aionbound:whisperwood_hatchet"),
    "lantern_hook": ([ingredient("aionbound:whisperwood_planks"), ingredient("aionbound:lantern_fur"), ingredient("minecraft:iron_nugget")], "aionbound:lantern_hook"),
    # Four-piece light set. Approved Thick Hide / moss plate aliases are whisper_bark.
    "whisperwood_helmet": ([ingredient("aionbound:whisper_bark", 3), ingredient("aionbound:widow_silk"), ingredient("aionbound:moss_bind_glue")], "aionbound:whisperwood_helmet"),
    "whisperwood_chest": ([ingredient("aionbound:whisper_bark", 5), ingredient("aionbound:widow_silk", 2), ingredient("aionbound:moss_bind_glue")], "aionbound:whisperwood_chest"),
    "whisperwood_legs": ([ingredient("aionbound:whisper_bark", 4), ingredient("aionbound:widow_silk", 2), ingredient("aionbound:moss_bind_glue")], "aionbound:whisperwood_legs"),
    "whisperwood_boots": ([ingredient("aionbound:whisper_bark", 2), ingredient("aionbound:widow_silk"), ingredient("aionbound:moss_bind_glue")], "aionbound:whisperwood_boots"),
    # Five accessories. Copper is the stable vanilla realization of Creative's brass scrap.
    "moss_charm": ([ingredient("aionbound:moss_resin"), ingredient("aionbound:glow_moss")], "aionbound:moss_charm"),
    "root_bracelet": ([ingredient("aionbound:root_flower"), ingredient("aionbound:whisperwood_roots"), ingredient("aionbound:hollow_amber")], "aionbound:root_bracelet"),
    "lantern_badge": ([ingredient("aionbound:lantern_fur"), ingredient("minecraft:copper_ingot")], "aionbound:lantern_badge"),
    "moon_sap_pendant": ([ingredient("aionbound:moon_sap"), ingredient("aionbound:widow_silk")], "aionbound:moon_sap_pendant"),
    "briar_ring": ([ingredient("aionbound:briar_vine"), ingredient("aionbound:briar_antler")], "aionbound:briar_ring"),
    # Optional mastery/display crafts only. Thorn Stalker skull is arena fulfillment only.
    "mosskip_trophy": ([ingredient("aionbound:mosskip_crown_fragment", 3)], "aionbound:mosskip_trophy"),
    "briar_elk_trophy": ([ingredient("aionbound:briar_antler", 2), ingredient("aionbound:whisperwood_planks", 3)], "aionbound:briar_elk_trophy"),
    "ancient_acorn_display": ([ingredient("aionbound:ancient_acorn"), ingredient("aionbound:whisperwood_planks", 3)], "aionbound:ancient_acorn_display"),
    # Reconcile the existing G7 ration identity to the approved WW plant-food loop.
    "waystone_ration": ([ingredient("aionbound:star_grass"), ingredient("aionbound:mooncap_mushroom"), ingredient("minecraft:bread")], "aionbound:waystone_ration"),
}


REPAIR = {
    "mossfang_spear": ("aionbound:moss_bind_glue", 72),
    "widow_fang_dagger": ("aionbound:widow_silk", 64),
    "thorn_whip": ("aionbound:thorn_cord", 72),
    "briar_cleaver": ("aionbound:briar_antler", 80),
    "moon_sap_staff": ("aionbound:amber_core", 72),
    "root_knife": ("aionbound:whisper_bark", 48),
    "whisperwood_hatchet": ("aionbound:moss_bind_glue", 64),
    "lantern_hook": ("aionbound:lantern_fur", 48),
}


def set_count(minimum: int, maximum: int | None = None) -> list[dict]:
    count: int | dict = minimum if maximum is None or maximum == minimum else {"min": minimum, "max": maximum}
    return [{"function": "set_count", "count": count}]


def pool(name: str, chance: float, minimum: int = 1, maximum: int | None = None) -> dict:
    value = {
        "rolls": 1,
        "entries": [{"type": "item", "name": name, "weight": 1, "functions": set_count(minimum, maximum)}],
    }
    if chance < 1.0:
        value["conditions"] = [{"condition": "random_chance", "chance": chance}]
    return value


# Values are deliberately inside the ratified closed intervals: C=1.0,
# U=.40/.50/.55, normal R=.12, elite R=.50, elite E=.12.
ENTITY_LOOT = {
    "mosskip_fawn": [("aionbound:moss_resin", 1.0, 1, 1), ("aionbound:star_grass", .40, 1, 1)],
    "mosskip_doe": [("aionbound:moss_resin", 1.0, 1, 2), ("aionbound:whisper_bark", .40, 1, 1)],
    "mosskip_buck": [("aionbound:moss_resin", 1.0, 2, 2), ("aionbound:whisper_bark", .40, 1, 1), ("aionbound:mosskip_crown_fragment", .12, 1, 1)],
    "lantern_hare": [("aionbound:glow_spore", 1.0, 1, 1), ("aionbound:lantern_fur", .40, 1, 1)],
    "rootback_boar": [("aionbound:whisper_bark", 1.0, 1, 2), ("aionbound:briar_antler", .40, 1, 1), ("aionbound:root_heart", .12, 1, 1)],
    "briar_elk": [("aionbound:whisper_bark", 1.0, 1, 2), ("aionbound:briar_antler", .55, 1, 2), ("aionbound:ancient_acorn", .12, 1, 1)],
    "rot_wolf": [("aionbound:whisper_bark", 1.0, 1, 1), ("aionbound:widow_silk", .40, 1, 1)],
    "thorn_stalker": [("aionbound:briar_vine", 1.0, 1, 2), ("aionbound:thorn_barb", .50, 1, 2), ("aionbound:stalker_claw", .50, 1, 1)],
    "hollow_widow_spider": [("aionbound:widow_silk", 1.0, 1, 2), ("aionbound:hollow_venom_sac", .50, 1, 1)],
    "bark_wraith": [("aionbound:whisper_bark", 1.0, 1, 2), ("aionbound:hollow_amber", .50, 1, 2), ("aionbound:moon_sap", .50, 1, 1), ("aionbound:ancient_acorn", .12, 1, 1)],
}


# Each chest's total rolls and guaranteed regional rolls sit inside W1-004.
CHESTS = {
    "hunter_camp": {"band": "standard_structure", "guaranteed": 1, "random": 3, "entries": [("aionbound:moss_resin", 40), ("aionbound:pale_reed", 30), ("aionbound:lantern_fur", 15), ("aionbound:widow_silk", 10), ("aionbound:hollow_amber", 5)]},
    "broken_wagon": {"band": "minor_cache", "guaranteed": 1, "random": 1, "entries": [("aionbound:whisperwood_planks", 50), ("aionbound:moss_resin", 30), ("aionbound:lantern_fur", 15), ("aionbound:hollow_amber", 5)]},
    "root_bridge": {"band": "minor_cache", "guaranteed": 1, "random": 1, "entries": [("aionbound:briar_vine", 50), ("aionbound:whisper_bark", 30), ("aionbound:widow_silk", 15), ("aionbound:hollow_amber", 5)]},
    "owl_shrine": {"band": "landmark_structure", "guaranteed": 2, "random": 3, "entries": [("aionbound:moon_sap", 40), ("aionbound:hollow_amber", 30), ("aionbound:root_heart", 15), ("aionbound:ancient_acorn", 5), ("aionbound:widow_silk", 10)]},
    "hollow_cave_entrance": {"band": "standard_structure", "guaranteed": 1, "random": 3, "entries": [("aionbound:glow_spore", 40), ("aionbound:hollow_amber", 30), ("aionbound:widow_silk", 15), ("aionbound:root_heart", 10), ("aionbound:hollow_venom_sac", 5)]},
    "ancient_totem": {"band": "landmark_structure", "guaranteed": 2, "random": 3, "entries": [("aionbound:whisper_bark", 40), ("aionbound:root_heart", 30), ("aionbound:hollow_amber", 15), ("aionbound:moon_sap", 10), ("aionbound:ancient_acorn", 5)]},
    "fallen_giant_tree": {"band": "landmark_structure", "guaranteed": 2, "random": 4, "entries": [("aionbound:whisper_bark", 40), ("aionbound:moss_resin", 30), ("aionbound:hollow_amber", 15), ("aionbound:root_heart", 10), ("aionbound:ancient_acorn", 5)]},
}


PLANT_IDS = ["star_grass", "whisper_fern", "pale_reed", "glow_moss", "mooncap_mushroom", "lantern_bloom", "hollow_lily", "root_flower", "briar_vine", "ember_thistle"]
BLOCK_SELF_IDS = ["forest_brick", "hollow_wood", "moss_bark", "stripped_whisperwood_log", "whisperwood_log", "whisperwood_planks", "whisperwood_roots", "whisperwood_wood"]
BLOCK_BONUS = {
    "hollow_wood": [("aionbound:hollow_amber", .25, 1, 1)],
    "moss_bark": [("aionbound:moss_resin", .75, 1, 2)],
    "whisperwood_log": [("aionbound:whisper_bark", .75, 1, 1)],
    "whisperwood_roots": [("aionbound:root_heart", .08, 1, 1)],
    "glow_moss": [("aionbound:glow_spore", .25, 1, 1)],
    "mooncap_mushroom": [("aionbound:glow_spore", .25, 1, 1)],
    "hollow_lily": [("aionbound:moon_sap", .12, 1, 1)],
}


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def item_doc(item_id: str, name: str) -> dict:
    return {
        "format_version": "1.21.80",
        "minecraft:item": {
            "description": {"identifier": f"aionbound:{item_id}", "menu_category": {"category": "items"}},
            "components": {
                "minecraft:display_name": {"value": name},
                "minecraft:icon": {"textures": {"default": item_id}},
                "minecraft:max_stack_size": 64,
            },
        },
    }


def recipe_doc(recipe_id: str, inputs: list[dict], result: str) -> dict:
    expanded_inputs = []
    for value in inputs:
        for _ in range(value.get("count", 1)):
            expanded_inputs.append({"item": value["item"]})
    if len(expanded_inputs) > 9:
        raise ValueError(f"crafting-grid overflow: {recipe_id}")
    return {
        "format_version": "1.20.10",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": f"aionbound:{recipe_id}_recipe"},
            "tags": ["crafting_table"],
            "ingredients": expanded_inputs,
            "result": {"item": result, "count": 1},
            "unlock": [{"item": inputs[0]["item"]}],
        },
    }


def weighted_entry(name: str, weight: int) -> dict:
    return {"type": "item", "name": name, "weight": weight, "functions": set_count(1, 2)}


def chest_doc(spec: dict) -> dict:
    guaranteed_entries = [weighted_entry(name, weight) for name, weight in spec["entries"] if name.startswith("aionbound:")]
    random_entries = [weighted_entry(name, weight) for name, weight in spec["entries"]]
    return {"pools": [
        {"rolls": spec["guaranteed"], "entries": guaranteed_entries},
        {"rolls": spec["random"], "entries": random_entries},
    ]}


def expected_outputs() -> dict[Path, bytes]:
    outputs: dict[Path, bytes] = {}
    for item_id, name in NEW_ITEMS.items():
        outputs[BP / "items" / f"{item_id}.item.json"] = json_bytes(item_doc(item_id, name))
    for recipe_id, (inputs, result) in RECIPES.items():
        outputs[BP / "recipes" / f"{recipe_id}.recipe.json"] = json_bytes(recipe_doc(recipe_id, inputs, result))
    for entity_id, drops in ENTITY_LOOT.items():
        outputs[BP / "loot_tables" / "entities" / f"{entity_id}.json"] = json_bytes({"pools": [pool(*drop) for drop in drops]})
    for structure_id, spec in CHESTS.items():
        outputs[BP / "loot_tables" / "chests" / "whisperwood" / f"{structure_id}.json"] = json_bytes(chest_doc(spec))

    # Runtime/persistence invokes this only after a valid arena death. It contains
    # materials, never the seal item or entitlement itself.
    outputs[BP / "loot_tables" / "encounters" / "whisperwood" / "thorn_court_materials.json"] = json_bytes({"pools": [
        pool("aionbound:widow_silk", 1.0, 1, 3),
        pool("aionbound:thorn_barb", 1.0, 1, 3),
        pool("aionbound:hollow_amber", 1.0, 1, 2),
        pool("aionbound:root_heart", .50, 1, 1),
        pool("aionbound:moon_sap", .50, 1, 1),
        pool("aionbound:ancient_acorn", .12, 1, 1),
    ]})
    outputs[BP / "loot_tables" / "chests" / "whisperwood" / "thorn_court.json"] = json_bytes(chest_doc({
        "guaranteed": 2,
        "random": 3,
        "entries": [("aionbound:widow_silk", 40), ("aionbound:thorn_barb", 30), ("aionbound:hollow_amber", 15), ("aionbound:root_heart", 10), ("aionbound:ancient_acorn", 5)],
    }))

    for block_id in [*PLANT_IDS, *BLOCK_SELF_IDS]:
        drops = [(f"aionbound:{block_id}", 1.0, 1, 1), *BLOCK_BONUS.get(block_id, [])]
        outputs[BP / "loot_tables" / "blocks" / f"{block_id}.json"] = json_bytes({"pools": [pool(*drop) for drop in drops]})
    outputs[BP / "loot_tables" / "blocks" / "lantern_post.json"] = json_bytes({"pools": [pool("aionbound:glow_spore", 1.0), pool("aionbound:lantern_fur", .25)]})
    outputs[BP / "loot_tables" / "blocks" / "moss_cairn.json"] = json_bytes({"pools": [pool("minecraft:bone", 1.0), pool("aionbound:hollow_amber", .25)]})
    return outputs


def mutate_existing() -> None:
    for entity_id in ENTITY_LOOT:
        path = BP / "entities" / f"{entity_id}.entity.json"
        doc = json.loads(path.read_text())
        components = doc["minecraft:entity"]["components"]
        components["minecraft:loot"] = {"table": f"loot_tables/entities/{entity_id}.json"}
        path.write_bytes(json_bytes(doc))
    for item_id, (repair_item, amount) in REPAIR.items():
        path = BP / "items" / f"{item_id}.item.json"
        doc = json.loads(path.read_text())
        doc["minecraft:item"]["components"]["minecraft:repairable"] = {
            "repair_items": [{"items": [repair_item], "repair_amount": amount}]
        }
        path.write_bytes(json_bytes(doc))
    for block_id in [*PLANT_IDS, *BLOCK_SELF_IDS, "lantern_post", "moss_cairn"]:
        path = BP / "blocks" / f"{block_id}.block.json"
        doc = json.loads(path.read_text())
        doc["minecraft:block"]["components"]["minecraft:loot"] = f"loot_tables/blocks/{block_id}.json"
        path.write_bytes(json_bytes(doc))

    atlas_path = RP / "textures" / "item_texture.json"
    atlas = json.loads(atlas_path.read_text())
    for item_id in NEW_ITEMS:
        atlas["texture_data"][item_id] = {"textures": f"textures/aionbound/whisperwood/items/{item_id}"}
    atlas_path.write_bytes(json_bytes(atlas))
    lang_path = RP / "texts" / "en_US.lang"
    stale_keys = {f"item.aionbound:{item_id}.name" for item_id in NEW_ITEMS}
    lines = [line for line in lang_path.read_text().splitlines() if line.split("=", 1)[0] not in stale_keys]
    keys = {line.split("=", 1)[0] for line in lines if "=" in line}
    for item_id, name in NEW_ITEMS.items():
        key = f"item.aionbound:{item_id}"
        if key not in keys:
            lines.append(f"{key}={name}")
    lang_path.write_text("\n".join(lines) + "\n")


def report() -> dict:
    outputs = expected_outputs()
    return {
        "schema": "aionbound.wave1.whisperwood.economy.v1",
        "status": "STATIC_CLOSURE_PASS",
        "base_commit": "00840aaae36a0cfb83955ca7b416c1d2886a6261",
        "authority": ["W1-001-WW_APPROVED_AS_WRITTEN", "W1-004-WW-CH1_APPROVED_AS_WRITTEN", "Creative LOOT_WHISPERWOOD / LOOT_SYSTEM / LOOT_BOSSES / CRAFTING_TREE"],
        "ratified_proposals": [
            {"tranche": "W1-001-WW", "path": "engineering/authority/support-proposals/W1-CREATIVE-001/nonwarehouse_identity_proposal.json", "sha256": "a9bc8133f8a0aacf7db258ffe76fc04dd9fcc6d07713bef630e074bd48588786"},
            {"tranche": "W1-004-WW-CH1", "path": "engineering/authority/support-proposals/W1-CREATIVE-004/loot_envelope_proposal.json", "sha256": "4412b24ad680a30e5548c731f8acba94e8fd858e4bb94f701a16eb17141f5ab7"},
        ],
        "counts": {
            "new_items": len(NEW_ITEMS), "recipes": len(RECIPES), "entity_tables": len(ENTITY_LOOT),
            "structure_chests": len(CHESTS), "encounter_material_tables": 1, "apex_chests": 1,
            "block_and_plant_tables": len(PLANT_IDS) + len(BLOCK_SELF_IDS) + 2,
            "repair_bindings": len(REPAIR),
        },
        "tuning": {"C": 1.0, "U": [.40, .50, .55], "R_normal": .12, "R_elite": .50, "E_elite": .12, "structure_rolls": {key: value["guaranteed"] + value["random"] for key, value in CHESTS.items()}, "thorn_court_chest_rolls": 5},
        "guards": {
            "natural_thorn_stalker_skull": "FORBIDDEN_AND_ABSENT",
            "thorn_court_material_table_contains_seal": False,
            "thorn_court_chest_contains_seal": False,
            "seal_and_physical_trophy_fulfillment": "RUNTIME_PERSISTENCE_LANE_ONLY",
            "mastery_trophies": ["aionbound:briar_elk_trophy", "aionbound:mosskip_trophy"],
            "mastery_trophies_progression_required": False,
            "sidegrades": "W1-CREATIVE-005_DEFERRED_NO_SIBLING_IDS",
        },
        "output_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(data).hexdigest() for path, data in sorted(outputs.items())},
        "proof_boundary": {"proves": ["deterministic authored JSON", "ratified ID and recipe relation closure", "bounded loot values", "natural stalker seal exclusion"], "does_not_prove": ["BDS acceptance", "client chest population", "runtime entitlement or recovery", "balance", "Checkpoint 1"]},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = expected_outputs()
    if not args.check:
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        mutate_existing()
        (OUT / "WHISPERWOOD_ECONOMY_REPORT.json").write_bytes(json_bytes(report()))
        print(json.dumps({"status": "PASS", "outputs": len(outputs)}))
        return 0
    mismatches = [str(path.relative_to(ROOT)) for path, data in outputs.items() if not path.exists() or path.read_bytes() != data]
    expected_report = json_bytes(report())
    if not (OUT / "WHISPERWOOD_ECONOMY_REPORT.json").exists() or (OUT / "WHISPERWOOD_ECONOMY_REPORT.json").read_bytes() != expected_report:
        mismatches.append("engineering/whisperwood-intake/economy/WHISPERWOOD_ECONOMY_REPORT.json")
    print(json.dumps({"status": "PASS" if not mismatches else "FAIL", "mismatches": mismatches}, indent=2))
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
