from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.build_gloamwing_stalker import ASSET, BP, FEATURE, PACKAGES, RP, build


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_geometry_texture_and_animation_budgets() -> None:
    build()
    geo = read(ASSET / "gloamwing_stalker.geo.json")["minecraft:geometry"][0]
    bones = geo["bones"]
    assert len(bones) == 10
    assert sum(len(b.get("cubes", [])) for b in bones) == 23
    assert geo["description"]["texture_width"] <= 64 and geo["description"]["texture_height"] <= 64
    assert (ASSET / "gloamwing_stalker.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    clips = read(RP / "animations/gloamwing_stalker.animation.json")["animations"]
    controllers = read(RP / "animation_controllers/gloamwing_stalker.animation_controllers.json")["animation_controllers"]
    assert len(clips) == 5 and len(controllers) == 1
    assert {"idle", "stalk", "telegraph", "pounce", "landing"} <= {name.rsplit(".", 1)[-1] for name in clips}


def test_cross_file_references_and_stable_behavior() -> None:
    build()
    client = read(RP / "entity/gloamwing_stalker.entity.json")["minecraft:client_entity"]["description"]
    behavior = read(BP / "entities/gloamwing_stalker.json")["minecraft:entity"]
    assert client["identifier"] == behavior["description"]["identifier"] == "ccoriginal_cc:gloamwing_stalker"
    assert client["geometry"]["default"] == "geometry.ccoriginal_cc.gloamwing_stalker"
    components_text = json.dumps(behavior)
    for state in ("idle", "stalk", "telegraph", "pounce", "landing", "damage", "death"):
        assert state in (json.dumps(client) + components_text)
    assert "minecraft:navigation.walk" in behavior["components"]
    assert behavior["components"]["minecraft:follow_range"]["max"] == 16
    assert "minecraft:behavior.leap_at_target" in behavior["component_groups"]["ccoriginal_cc:pounce"]
    assert all(module["type"] != "script" for module in read(BP / "manifest.json")["modules"])


def test_attack_cycle_is_structurally_reachable_and_cooldown_is_bounded() -> None:
    build()
    entity = read(BP / "entities/gloamwing_stalker.json")["minecraft:entity"]
    groups, events = entity["component_groups"], entity["events"]

    # Walk actual native trigger edges: spawn -> ready sensor -> telegraph timer ->
    # pounce timer -> recovery timer -> cooldown timer -> ready.
    def group_trigger(group: str, component: str) -> str:
        value = groups[group][component]
        if component == "minecraft:environment_sensor":
            return value["triggers"][0]["event"]
        return value["time_down_event"]["event"]

    assert "ccoriginal_cc:ready" in events["minecraft:entity_spawned"]["add"]["component_groups"]
    cycle = [
        ("ccoriginal_cc:ready", "minecraft:environment_sensor", "ccoriginal_cc:begin_telegraph", "ccoriginal_cc:telegraph"),
        ("ccoriginal_cc:telegraph", "minecraft:timer", "ccoriginal_cc:pounce", "ccoriginal_cc:pounce"),
        ("ccoriginal_cc:pounce", "minecraft:timer", "ccoriginal_cc:land", "ccoriginal_cc:recovery"),
        ("ccoriginal_cc:recovery", "minecraft:timer", "ccoriginal_cc:begin_cooldown", "ccoriginal_cc:cooldown"),
        ("ccoriginal_cc:cooldown", "minecraft:timer", "ccoriginal_cc:arm", "ccoriginal_cc:ready"),
    ]
    for source_group, component, event_name, destination_group in cycle:
        assert group_trigger(source_group, component) == event_name
        transition = events[event_name]
        assert source_group in transition["remove"]["component_groups"]
        assert destination_group in transition["add"]["component_groups"]
        assert source_group != destination_group

    sensor_filters = groups["ccoriginal_cc:ready"]["minecraft:environment_sensor"]["triggers"][0]["filters"]["all_of"]
    assert {"test": "has_target", "subject": "self", "value": True} in sensor_filters
    assert any(row.get("test") == "distance_to_nearest_player" and row.get("value") == 16 for row in sensor_filters)
    cooldown = groups["ccoriginal_cc:cooldown"]["minecraft:timer"]
    assert cooldown["time"] == [4.0, 7.0] and cooldown["looping"] is False


def test_spawn_stress_cleanup_and_multiplayer_fallback_contracts() -> None:
    build()
    spawn = read(BP / "spawn_rules/gloamwing_stalker.json")
    assert spawn["minecraft:spawn_rules"]["conditions"] == []
    assert spawn["_ccoriginal_cc"]["natural_spawn_enabled"] is False
    stress = (BP / "functions/ccoriginal_cc/gloamwing/stress_20.mcfunction").read_text().splitlines()
    assert len(stress) == 20 and all("ccoriginal_cc:gloamwing_test" in line for line in stress)
    cleanup = (BP / "functions/ccoriginal_cc/gloamwing/cleanup.mcfunction").read_text()
    assert cleanup == "kill @e[type=ccoriginal_cc:gloamwing_stalker,tag=ccoriginal_cc:gloamwing_test]\n"
    target = read(BP / "entities/gloamwing_stalker.json")["minecraft:entity"]["components"]["minecraft:behavior.nearest_attackable_target"]
    assert target["reselect_targets"] is True and target["within_radius"] == 16


def test_deterministic_package_and_claim_labels() -> None:
    build()
    output = PACKAGES / "gloamwing_stalker.mcaddon"
    first = hashlib.sha256(output.read_bytes()).hexdigest()
    build()
    assert first == hashlib.sha256(output.read_bytes()).hexdigest()
    report = read(FEATURE / "reports/build-report.json")
    assert report["hashes"]["mcaddon"] == first
    assert report["labels"] == {"marketplace_approved": False, "ps4_verified": False}
