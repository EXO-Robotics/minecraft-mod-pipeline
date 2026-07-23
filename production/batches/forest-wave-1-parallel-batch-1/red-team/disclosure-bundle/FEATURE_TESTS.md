===== DISCLOSED SOURCE: tests/test_signal_ruin.py =====

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/signal-ruin"
PROTO = ROOT / "prototypes/blockbench/signal_ruin"
BUILD = ROOT / "tools/build_signal_ruin.py"
LABEL = "INTERNAL TEST BUILD / NOT MARKETPLACE APPROVED / NOT PHYSICAL PS4 CERTIFIED / NOT FOR PUBLIC RELEASE"


def run_build() -> None:
    subprocess.run([sys.executable, str(BUILD)], cwd=ROOT, check=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_build_is_deterministic_and_all_json_parses() -> None:
    run_build()
    outputs = [
        FEATURE / "dist/signal-ruin-INTERNAL-TEST.mcaddon",
        FEATURE / "bedrock/behavior_pack/structures/ccoriginal_cc/signal_ruin.mcstructure",
    ]
    first = [digest(p) for p in outputs]
    run_build()
    assert first == [digest(p) for p in outputs]
    for path in list(FEATURE.rglob("*.json")) + list(PROTO.rglob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))


def test_rebuild_preserves_candidate_and_review_evidence() -> None:
    candidate = FEATURE / "reports/candidate-packet.json"
    candidate_before = candidate.read_bytes()
    review = FEATURE / "reports/main-codex-review-evidence.TEST.json"
    review.write_text('{"owner":"MAIN_CODEX","test_fixture":true}\n', encoding="utf-8")
    try:
        review_before = review.read_bytes()
        run_build()
        assert candidate.read_bytes() == candidate_before
        assert review.read_bytes() == review_before
    finally:
        review.unlink(missing_ok=True)


def test_structure_is_original_bounded_and_valid_little_endian_nbt() -> None:
    spec = json.loads((PROTO / "signal_ruin.structure.json").read_text())
    assert spec["size"] == [11, 9, 11]
    assert len(spec["blocks"]) == len({tuple(row["pos"]) for row in spec["blocks"]})
    assert all(0 <= row["pos"][i] < spec["size"][i] for row in spec["blocks"] for i in range(3))
    structure = FEATURE / "bedrock/behavior_pack/structures/ccoriginal_cc/signal_ruin.mcstructure"
    assert structure.stat().st_size < 131072
    raw = structure.read_bytes()
    assert raw[:3] == bytes([10, 0, 0])
    assert b"format_version" in raw and b"block_palette" in raw
    assert b"minecraft:stripped_spruce_log" in raw and b"minecraft:ochre_froglight" in raw


def test_reserved_identity_and_package_contents() -> None:
    bp = json.loads((FEATURE / "bedrock/behavior_pack/manifest.json").read_text())
    rp = json.loads((FEATURE / "bedrock/resource_pack/manifest.json").read_text())
    assert bp["header"]["uuid"] == "556acdce-2ddc-4cbd-b08d-f62681387306"
    assert {m["uuid"] for m in bp["modules"]} == {
        "59c9ac60-a5ba-44a2-8517-c1f7a2fd51e3",
        "45e8f7ad-197e-45ff-99ee-60b6fec7e30d",
    }
    assert rp["header"]["uuid"] == "f15d006f-c77c-45e5-a6d8-84da52a5db0e"
    assert rp["modules"][0]["uuid"] == "214f239c-6fe6-44b1-b69f-38c9b005a3dd"
    entity = json.loads((FEATURE / "bedrock/behavior_pack/entities/signal_ruin_anchor.json").read_text())
    assert entity["minecraft:entity"]["description"]["identifier"] == "ccoriginal_cc:signal_ruin_anchor"
    with zipfile.ZipFile(FEATURE / "dist/signal-ruin-INTERNAL-TEST.mcaddon") as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert "signal_ruin_BP/scripts/signal_ruin.js" in names
        assert "signal_ruin_BP/structures/ccoriginal_cc/signal_ruin.mcstructure" in names


def test_encounter_contract_is_bounded_idempotent_and_recoverable() -> None:
    script = (FEATURE / "bedrock/behavior_pack/scripts/signal_ruin.js").read_text()
    assert "const CAP = 12" in script
    assert "const INSTANCE_CAP = 2" in script
    assert "const ENCOUNTER_SECONDS_CAP = 80" in script
    assert "system.runInterval" in script and "},20)" in script
    assert "reward_issued" in script and 'if(get(a,"reward_issued",false))' in script
    assert "playerInteractWithEntity" in script
    assert "absent>=20" in script and 'set(a,"state","READY")' in script
    assert "worldLoad" in script and "spawnWave(a,Math.max" in script
    assert 'set(a,"elapsed_seconds",0)' in script
    assert script.count("runTimeout") == 1
    assert "runJob" not in script
    scenarios = json.loads((FEATURE / "tests/scenarios.json").read_text())
    assert len(scenarios["scenarios"]) == 9


def test_third_concurrent_activation_is_rejected_before_mutation() -> None:
    script = (FEATURE / "bedrock/behavior_pack/scripts/signal_ruin.js").read_text()
    function = script[script.index("function activate"):script.index("world.afterEvents.playerInteractWithEntity")]
    cap_check = function.index("activeInstances()>=INSTANCE_CAP")
    feedback = function.index("Only two Signal Ruins may be active at once")
    first_mutation = function.index('set(a,"schema",1)')
    assert cap_check < feedback < first_mutation
    assert function[cap_check:first_mutation].count("set(a,") == 0


def test_encounter_timer_has_hard_80_second_cleanup_model() -> None:
    script = (FEATURE / "bedrock/behavior_pack/scripts/signal_ruin.js").read_text()
    tick = script[script.index("system.runInterval"):]
    timer_check = tick.index("elapsed>=ENCOUNTER_SECONDS_CAP")
    player_query = tick.index("getPlayers")
    assert timer_check < player_query
    timeout_body = tick[timer_check:player_query]
    assert "clean(a)" in timeout_body
    assert 'set(a,"state","READY")' in timeout_body
    assert 'set(a,"elapsed_seconds",0)' in timeout_body
    # One interval is one second; model the boundary independently.
    elapsed = 0
    states = []
    for _ in range(80):
        elapsed += 1
        states.append("READY" if elapsed >= 80 else "ACTIVE")
    assert states[78] == "ACTIVE"
    assert states[79] == "READY"


def test_stress_places_two_spatially_distinct_instances() -> None:
    lines = [
        line for line in
        (FEATURE / "bedrock/behavior_pack/functions/ccoriginal_cc/signal_ruin/stress.mcfunction").read_text().splitlines()
        if line.startswith(("structure load", "summon ccoriginal_cc:signal_ruin_anchor"))
    ]
    structures = [line for line in lines if line.startswith("structure load")]
    anchors = [line for line in lines if line.startswith("summon")]
    assert structures == [
        "structure load ccoriginal_cc:signal_ruin ~ ~ ~",
        "structure load ccoriginal_cc:signal_ruin ~24 ~ ~",
    ]
    assert anchors == [
        "summon ccoriginal_cc:signal_ruin_anchor ~8.5 ~1 ~5.5",
        "summon ccoriginal_cc:signal_ruin_anchor ~32.5 ~1 ~5.5",
    ]


def test_release_labels_and_no_public_claims() -> None:
    for path in [
        FEATURE / "reports/readiness-matrix.json",
        FEATURE / "reports/provenance.json",
        FEATURE / "tests/scenarios.json",
        PROTO / "originality-and-authoring.json",
    ]:
        assert json.loads(path.read_text())["label"] == LABEL
    readiness = json.loads((FEATURE / "reports/readiness-matrix.json").read_text())
    assert readiness["physical_ps4"] == "NOT_PHYSICAL_PS4_CERTIFIED"
    assert readiness["marketplace"] == "NOT_MARKETPLACE_APPROVED"


===== DISCLOSED SOURCE: tests/test_gloamwing_stalker.py =====

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


def test_editable_source_is_a_real_blockbench_project_and_builder_preserves_it() -> None:
    source = ASSET / "gloamwing_stalker.bbmodel"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    model = read(source)
    assert model["meta"]["model_format"] == "bedrock"
    assert model["model_identifier"] == "ccoriginal_cc.gloamwing_stalker"
    assert len(model["elements"]) == 23
    assert len(model["groups"]) == 10
    assert len(model["outliner"]) == 1
    assert len(model["textures"]) == 1
    assert model["textures"][0]["source"].startswith("data:image/png;base64,")
    assert len(model["animations"]) == 5
    assert len(model["animation_controllers"]) == 1
    outliner = json.dumps(model["outliner"])
    assert all(element["uuid"] in outliner for element in model["elements"])
    build()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


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
    assert len(stress) == 40
    assert sum(line.startswith("summon ccoriginal_cc:gloamwing_stalker ") for line in stress) == 20
    assert sum(line.endswith("add ccoriginal_cc:gloamwing_test") for line in stress) == 20
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


===== DISCLOSED SOURCE: tests/test_forest_attunement.py =====

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/forest-attunement"
BUILD = ROOT / "tools/build_forest_attunement.py"
STATE_JS = FEATURE / "behavior_pack/scripts/state.js"
MAIN_JS = FEATURE / "behavior_pack/scripts/main.js"
PROPERTY = "ccoriginal_cc:forest_attunement_v1"
CANONICAL = '{"version":1,"unlocked":true}'


def decode(raw):
    if raw is None:
        return "empty", False
    if raw is True:
        return "legacy", True
    if not isinstance(raw, str):
        return "corrupt", False
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return "corrupt", False
    if not isinstance(value, dict):
        return "corrupt", False
    if "version" not in value and value.get("unlocked") is True:
        return "legacy", True
    if not isinstance(value.get("version"), int):
        return "corrupt", False
    if value["version"] != 1:
        return "unknown", False
    if value.get("unlocked") is not True:
        return "corrupt", False
    return "current", True


@dataclass
class Player:
    count: int
    raw: object = None
    presentation_errors: int = 0

    def activate(self, presentation_throws=False):
        kind, unlocked = decode(self.raw)
        if unlocked:
            if kind == "legacy":
                self.raw = CANONICAL
            return False
        if kind in {"unknown", "corrupt"} or self.count < 1:
            return False
        self.raw = CANONICAL
        self.count -= 1
        try:
            if presentation_throws:
                raise RuntimeError("simulated particle failure")
        except RuntimeError:
            self.presentation_errors += 1
        return True

    def attuned(self):
        kind, unlocked = decode(self.raw)
        if kind == "legacy":
            self.raw = CANONICAL
        return unlocked

    def reset(self, is_op=True):
        if is_op:
            self.raw = None


class ForestAttunementTests(unittest.TestCase):
    def test_fresh_activation_consumes_exactly_one_and_duplicate_preserves(self):
        player = Player(3)
        self.assertTrue(player.activate())
        self.assertEqual((player.count, player.raw), (2, CANONICAL))
        self.assertFalse(player.activate())
        self.assertEqual((player.count, player.raw), (2, CANONICAL))

    def test_presentation_failure_after_consumption_preserves_commit(self):
        player = Player(2)
        self.assertTrue(player.activate(presentation_throws=True))
        self.assertEqual(player.presentation_errors, 1)
        self.assertEqual(player.count, 1)
        self.assertEqual(player.raw, CANONICAL)
        self.assertFalse(player.activate())
        self.assertEqual((player.count, player.raw), (1, CANONICAL))

        source = MAIN_JS.read_text()
        presentation = source.split("function presentActivation(player) {", 1)[1].split(
            "\n}\n\nfunction activate", 1
        )[0]
        committed_tail = source.split("presentActivation(player);", 1)[1].split(
            "\n}\n\nworld.afterEvents", 1
        )[0]
        self.assertNotIn("setDynamicProperty", presentation + committed_tail)
        self.assertNotIn("PROPERTY_ID", presentation + committed_tail)

    def test_two_and_four_player_isolation_and_simultaneous_activation(self):
        players = [Player(i + 1) for i in range(4)]
        self.assertTrue(players[0].activate())
        self.assertIsNone(players[1].raw)
        for player in players[1:]:
            self.assertTrue(player.activate())
        self.assertEqual([p.count for p in players], [0, 1, 2, 3])
        players[2].reset()
        self.assertEqual([p.attuned() for p in players], [True, True, False, True])

    def test_death_disconnect_reconnect_and_restart_use_persisted_property(self):
        player = Player(1)
        player.activate()
        persisted = player.raw
        del player
        reconnected = Player(0, persisted)
        self.assertTrue(reconnected.attuned())
        restarted = Player(0, reconnected.raw)
        self.assertTrue(restarted.attuned())
        self.assertEqual(restarted.raw, CANONICAL)

    def test_known_migrations_are_canonical_and_idempotent(self):
        for legacy in (True, '{"unlocked":true}'):
            player = Player(2, legacy)
            self.assertTrue(player.attuned())
            self.assertEqual(player.raw, CANONICAL)
            self.assertTrue(player.attuned())
            self.assertEqual(player.count, 2)

    def test_unknown_and_corrupt_fail_closed_preserved_without_consumption(self):
        states = ('{"version":2,"unlocked":true}', "{broken", False, 17, "null",
                  '{"version":1,"unlocked":false}')
        for state in states:
            player = Player(2, state)
            self.assertFalse(player.activate())
            self.assertEqual(player.raw, state)
            self.assertEqual(player.count, 2)

    def test_admin_reset_is_invoker_only_and_non_operator_refused(self):
        a, b = Player(0, CANONICAL), Player(0, CANONICAL)
        a.reset(is_op=False)
        self.assertEqual(a.raw, CANONICAL)
        a.reset(is_op=True)
        self.assertIsNone(a.raw)
        self.assertEqual(b.raw, CANONICAL)

    def test_runtime_has_one_bounded_interval_and_no_tick_subscription_or_cache(self):
        source = MAIN_JS.read_text()
        self.assertEqual(source.count("system.runInterval("), 1)
        self.assertIn("}, 100);", source)
        self.assertNotIn("runInterval(() =>", source.replace("system.runInterval(() =>", "", 1))
        self.assertNotIn("afterEvents.tick", source)
        self.assertNotIn("beforeEvents.tick", source)
        self.assertNotRegex(source, r"new\s+Map|new\s+WeakMap")
        self.assertEqual(source.count("world.getAllPlayers()"), 1)

    def test_stable_api_version_reserved_ids_and_pack_uuids(self):
        bp = json.loads((FEATURE / "behavior_pack/manifest.json").read_text())
        rp = json.loads((FEATURE / "resource_pack/manifest.json").read_text())
        dependency = next(d for d in bp["dependencies"] if d.get("module_name") == "@minecraft/server")
        self.assertEqual(dependency["version"], "2.0.0")
        self.assertEqual(bp["header"]["uuid"], "43b642d0-a651-45cf-ae20-96a0b853fba5")
        self.assertEqual(bp["modules"][0]["uuid"], "e7798870-c7e2-4522-87bf-d046b08b442f")
        self.assertEqual(bp["modules"][1]["uuid"], "2db423eb-5691-4207-bb37-01751206657d")
        self.assertEqual(rp["header"]["uuid"], "0317044d-9b78-4101-aa2e-cb395af4e948")
        self.assertEqual(rp["modules"][0]["uuid"], "f00200ff-d682-4f87-9873-2e92abe15060")
        self.assertIn(PROPERTY, STATE_JS.read_text())

    def test_all_json_parses_and_icon_is_32px_png(self):
        for path in FEATURE.rglob("*.json"):
            json.loads(path.read_text())
        icon = FEATURE / "resource_pack/textures/items/forest_attunement_sigil.png"
        subprocess.run(["python3", str(BUILD)], cwd=ROOT, check=True, capture_output=True, text=True)
        data = icon.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(tuple(int.from_bytes(data[offset:offset + 4], "big") for offset in (16, 20)), (32, 32))

    def test_deterministic_package_rebuild_and_internal_labels(self):
        subprocess.run(["python3", str(BUILD)], cwd=ROOT, check=True, capture_output=True, text=True)
        outputs = sorted((FEATURE / "dist").glob("*"))
        before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs}
        subprocess.run(["python3", str(BUILD)], cwd=ROOT, check=True, capture_output=True, text=True)
        after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in outputs}
        self.assertEqual(before, after)
        self.assertTrue(all("INTERNAL-TEST" in path.name for path in outputs))
        addon = FEATURE / "dist/forest-attunement-INTERNAL-TEST.mcaddon"
        with zipfile.ZipFile(addon) as archive:
            self.assertTrue(all(info.date_time == (2020, 1, 1, 0, 0, 0) for info in archive.infolist()))
            self.assertIn("ForestAttunement_BP/scripts/main.js", archive.namelist())
            self.assertIn("ForestAttunement_RP/textures/items/forest_attunement_sigil.png", archive.namelist())


if __name__ == "__main__":
    unittest.main()


===== DISCLOSED SOURCE: tests/test_mossback_forager.py =====

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/mossback-forager"
PROTO = ROOT / "prototypes/blockbench/mossback_forager"
BUILD = ROOT / "tools/build_mossback_forager.py"


def load(relative):
    return json.loads((FEATURE / relative).read_text())


def test_all_json_parses_and_reserved_identity_is_consistent():
    for path in [*FEATURE.rglob("*.json"), *PROTO.rglob("*.json"), *PROTO.rglob("*.bbmodel")]:
        json.loads(path.read_text())
    text = "\n".join(p.read_text(errors="ignore") for p in FEATURE.rglob("*") if p.is_file())
    assert "ccoriginal_cc:mossback_forager" in text
    manifests = [load("bedrock/behavior_pack/manifest.json"), load("bedrock/resource_pack/manifest.json")]
    uuids = {m["header"]["uuid"] for m in manifests}
    assert uuids == {"6a67bb25-2953-4be9-9b32-611cf09be04a", "698f7eac-f081-49f9-8e82-1e0f362d704d"}


def test_geometry_texture_animation_and_controller_budgets_and_references():
    geo = load("bedrock/resource_pack/models/entity/mossback_forager.geo.json")["minecraft:geometry"][0]
    bones = geo["bones"]
    assert len(bones) == 9
    assert sum(len(b.get("cubes", [])) for b in bones) <= 22
    assert geo["description"]["texture_width"] == geo["description"]["texture_height"] == 64
    assert bones[-1]["locators"]["gift"] == [0, 7, -13]
    assert (FEATURE / "bedrock/resource_pack/textures/ccoriginal_cc/entity/mossback_forager.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    anim = load("bedrock/resource_pack/animations/mossback_forager.animation.json")["animations"]
    assert len(anim) == 4
    assert {key.rsplit(".", 1)[-1] for key in anim} == {"idle", "walk", "forage", "flee"}
    ctl = load("bedrock/resource_pack/animation_controllers/mossback_forager.controller.json")["animation_controllers"]
    assert len(ctl) == 1
    client = load("bedrock/resource_pack/entity/mossback_forager.entity.json")["minecraft:client_entity"]["description"]
    assert client["geometry"]["default"] == geo["description"]["identifier"]
    assert set(client["animations"]) == {"idle", "walk", "forage", "flee", "controller"}


def test_editable_blockbench_source_has_real_native_project_content():
    project = json.loads((PROTO / "mossback_forager.bbmodel").read_text())
    assert project["meta"]["model_format"] == "bedrock"
    assert len(project["elements"]) == 19
    assert sum(element["type"] == "cube" for element in project["elements"]) == 18
    locators = [element for element in project["elements"] if element["type"] == "locator"]
    assert [(item["name"], item["position"]) for item in locators] == [("gift", [0, 7, -13])]
    assert len(project["groups"]) == 9
    assert len(project["outliner"]) == 1 and project["outliner"][0]["children"]
    assert len(project["textures"]) == 1
    assert project["textures"][0]["internal"] is True
    assert project["textures"][0]["source"].startswith("data:image/png;base64,")
    assert len(project["animations"]) == 4
    assert len(project["animation_controllers"]) == 1


def test_exact_consumption_gift_atomic_contention_and_restart_safe_model():
    entity = load("bedrock/behavior_pack/entities/mossback_forager.json")["minecraft:entity"]
    assert list(entity["description"]["properties"]) == ["ccoriginal_cc:mossback_cooling"]
    interaction = entity["component_groups"]["ccoriginal_cc:ready"]["minecraft:interact"]["interactions"][0]
    assert interaction["use_item"] is True
    assert interaction["on_interact"]["filters"]["value"] == "minecraft:sweet_berries"
    assert interaction["spawn_items"] == {
        "table": "loot_tables/ccoriginal_cc/entities/mossback_forager_gift.json",
        "y_offset": 1,
    }
    sequence = entity["events"]["ccoriginal_cc:accept_berry"]["sequence"]
    assert sequence[0] == {"remove": {"component_groups": ["ccoriginal_cc:ready"]}}
    assert all("spawn_loot" not in step for step in sequence)
    gift = load("bedrock/behavior_pack/loot_tables/ccoriginal_cc/entities/mossback_forager_gift.json")
    assert gift["pools"][0]["rolls"] == 1
    assert all("count" not in e or e["count"] == 1 for e in gift["pools"][0]["entries"])
    cooling = entity["component_groups"]["ccoriginal_cc:cooling"]["minecraft:timer"]
    assert cooling["time"] == 45.0 and cooling["looping"] is False
    complete = entity["events"]["ccoriginal_cc:cooldown_complete"]["sequence"]
    assert complete[-1] == {"add": {"component_groups": ["ccoriginal_cc:ready"]}}
    # One entity property, no player record, no scripts: shared contention and four-player observation isolation.
    assert not list((FEATURE / "bedrock/behavior_pack").rglob("*.js"))
    assert "player" not in json.dumps(entity["description"]["properties"]).lower()


def test_disabled_spawn_stress20_and_cleanup_scope():
    spawn = load("bedrock/behavior_pack/spawn_rules/mossback_forager.disabled.json")
    assert spawn["minecraft:spawn_rules"]["description"]["conditions"] == []
    base = FEATURE / "bedrock/behavior_pack/functions/ccoriginal_cc/mossback"
    assert sum(line.startswith("summon ") for line in (base / "stress_1.mcfunction").read_text().splitlines()) == 1
    assert sum(line.startswith("summon ") for line in (base / "stress_10.mcfunction").read_text().splitlines()) == 10
    stress = (base / "stress_20.mcfunction").read_text().splitlines()
    assert sum(line.startswith("summon ") for line in stress) == 20
    assert sum(line.endswith("add ccoriginal_cc:mossback_test") for line in stress) == 20
    cleanup = (base / "cleanup.mcfunction").read_text().strip()
    assert cleanup == "kill @e[type=ccoriginal_cc:mossback_forager,tag=ccoriginal_cc:mossback_test]"


def test_damage_death_and_flee_states_exist():
    entity = load("bedrock/behavior_pack/entities/mossback_forager.json")["minecraft:entity"]
    assert entity["components"]["minecraft:loot"]["table"].endswith("mossback_forager_death.json")
    assert "minecraft:entity_hurt" in entity["events"]
    fleeing = entity["component_groups"]["ccoriginal_cc:fleeing"]
    assert fleeing["minecraft:behavior.panic"]["force"] is True
    timer = fleeing["minecraft:timer"]
    assert timer["looping"] is False and 0 < timer["time"] <= 10
    assert timer["time_down_event"] == {"event": "ccoriginal_cc:end_flee", "target": "self"}
    assert entity["events"]["ccoriginal_cc:end_flee"] == {
        "remove": {"component_groups": ["ccoriginal_cc:fleeing"]}}


def test_controller_forage_is_bounded_and_all_states_are_reachable():
    controller = load("bedrock/resource_pack/animation_controllers/mossback_forager.controller.json")
    states = next(iter(controller["animation_controllers"].values()))["states"]
    assert set(states) == {"idle", "walk", "forage", "cooling_idle", "flee"}
    forage_transitions = states["forage"]["transitions"]
    assert {"cooling_idle": "query.any_animation_finished"} in forage_transitions
    assert states["cooling_idle"]["animations"] == ["idle"]
    assert {"idle": "!query.property('ccoriginal_cc:mossback_cooling')"} in states["cooling_idle"]["transitions"]
    # Directed reachability from initial idle, based on declared transition targets.
    reached, pending = {"idle"}, ["idle"]
    while pending:
        state = pending.pop()
        for transition in states[state].get("transitions", []):
            target = next(iter(transition))
            if target not in reached:
                reached.add(target)
                pending.append(target)
    assert reached == set(states)


def test_deterministic_package_rebuild():
    package = FEATURE / "dist/mossback-forager-INTERNAL-TEST.mcaddon"
    before = hashlib.sha256(package.read_bytes()).hexdigest()
    subprocess.run([sys.executable, str(BUILD)], cwd=ROOT, check=True)
    after = hashlib.sha256(package.read_bytes()).hexdigest()
    assert before == after


def test_candidate_packet_metadata_is_stable_outside_assigned_checkout():
    report = FEATURE / "reports/candidate-packet.json"
    expected_worktree = (
        "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/"
        "parallel-batch-1/mossback-forager"
    )
    before = report.read_bytes()
    with tempfile.TemporaryDirectory() as outside:
        subprocess.run([sys.executable, str(BUILD)], cwd=outside, check=True)
    after_first = report.read_bytes()
    subprocess.run([sys.executable, str(BUILD)], cwd="/private/tmp", check=True)
    after_second = report.read_bytes()
    assert before == after_first == after_second
    assert json.loads(after_second)["worktree"] == expected_worktree


===== DISCLOSED SOURCE: tests/test_barkguard_charm.py =====

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "production/features/barkguard-charm"
BP = FEATURE / "bedrock/behavior_pack"
RP = FEATURE / "bedrock/resource_pack"
ASSETS = ROOT / "prototypes/blockbench/barkguard_charm"


class PlayerModel:
    def __init__(self, durability=0, offhand=True):
        self.damage = durability
        self.offhand = offhand
        self.cooldown = 0
        self.effects = []
        self.last_tick = None

    def hurt(self, amount, tick):
        if amount < 2 or not self.offhand or self.cooldown > 0 or self.last_tick == tick:
            return False
        self.last_tick = tick
        self.effects.append(("resistance", 60, 0))
        self.cooldown = 240
        self.damage += 1
        if self.damage >= 96:
            self.offhand = False
        return True


class BarkguardCharmTests(unittest.TestCase):
    def test_references_reserved_ids_and_stable_api(self):
        for path in list(BP.rglob("*.json")) + list(RP.rglob("*.json")) + list(ASSETS.glob("*.json")) + list(ASSETS.glob("*.bbmodel")):
            json.loads(path.read_text())
        manifest = json.loads((BP / "manifest.json").read_text())
        self.assertIn({"module_name": "@minecraft/server", "version": "2.0.0"}, manifest["dependencies"])
        item = json.loads((BP / "items/barkguard_charm.json").read_text())["minecraft:item"]
        self.assertEqual(item["description"]["identifier"], "ccoriginal_cc:barkguard_charm")
        self.assertTrue(item["components"]["minecraft:allow_off_hand"])
        self.assertEqual(item["components"]["minecraft:durability"]["max_durability"], 96)
        attachable = json.loads((RP / "attachables/barkguard_charm.entity.json").read_text())
        self.assertEqual(attachable["minecraft:attachable"]["description"]["geometry"]["default"], "geometry.ccoriginal_cc.barkguard_charm")

    def test_offhand_threshold_effect_cooldown_and_duplicate(self):
        p = PlayerModel(offhand=False)
        self.assertFalse(p.hurt(2, 1))
        p.offhand = True
        self.assertFalse(p.hurt(1.999, 2))
        self.assertTrue(p.hurt(2, 3))
        self.assertEqual(p.effects, [("resistance", 60, 0)])
        self.assertEqual(p.cooldown, 240)
        self.assertEqual(p.damage, 1)
        p.cooldown = 0
        self.assertFalse(p.hurt(8, 3), "duplicate event path in the same server tick")
        self.assertEqual(p.damage, 1)

    def test_exact_durability_and_break(self):
        p = PlayerModel(durability=94)
        self.assertTrue(p.hurt(2, 1))
        self.assertTrue(p.offhand)
        self.assertEqual(p.damage, 95)
        p.cooldown = 0
        self.assertTrue(p.hurt(2, 2))
        self.assertFalse(p.offhand)
        self.assertEqual(p.damage, 96)

    def test_two_and_four_player_isolation(self):
        for count in (2, 4):
            players = [PlayerModel() for _ in range(count)]
            for player in players:
                self.assertTrue(player.hurt(2, 10))
            self.assertEqual([p.damage for p in players], [1] * count)
            players[0].cooldown = 0
            self.assertTrue(players[0].hurt(2, 11))
            self.assertEqual([p.damage for p in players], [2] + [1] * (count - 1))

    def test_death_reconnect_and_restart_model(self):
        p = PlayerModel(durability=12)
        p.cooldown = 37
        inventory_damage = p.damage
        reconnected = PlayerModel(durability=inventory_damage)
        self.assertEqual(reconnected.damage, 12)
        self.assertEqual(reconnected.cooldown, 0)
        self.assertTrue(reconnected.hurt(2, 1))
        restarted = PlayerModel(durability=reconnected.damage)
        self.assertEqual(restarted.damage, 13)
        self.assertEqual(restarted.last_tick, None)

    def test_no_scan_callbacks_or_custom_persistence(self):
        script = (BP / "scripts/main.js").read_text()
        self.assertIn("world.afterEvents.entityHurt.subscribe", script)
        self.assertIn("EquipmentSlot.Offhand", script)
        for forbidden in ("runInterval", "getPlayers(", "getEntities(", "setDynamicProperty", "getDynamicProperty", "runTimeout"):
            self.assertNotIn(forbidden, script)
        self.assertEqual(script.count("entityHurt.subscribe"), 1)

    def test_geometry_animation_icon_recipe_and_grant(self):
        geo = json.loads((ASSETS / "barkguard_charm.geo.json").read_text())["minecraft:geometry"][0]
        self.assertEqual(geo["description"]["texture_width"], 32)
        self.assertEqual(sum(len(b.get("cubes", [])) for b in geo["bones"]), 7)
        for bone in geo["bones"]:
            for cube in bone.get("cubes", []):
                self.assertTrue(
                    all(dimension >= 1 for dimension in cube["size"]),
                    f"Box UV cube has a sub-unit dimension: {cube}",
                )
        animations = json.loads((RP / "animations/barkguard_charm.animation.json").read_text())["animations"]
        self.assertEqual(len(animations), 2)
        self.assertTrue((RP / "textures/items/barkguard_charm.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        recipe = json.loads((BP / "recipes/barkguard_charm.json").read_text())["minecraft:recipe_shaped"]
        self.assertEqual(recipe["result"]["item"], "ccoriginal_cc:barkguard_charm")
        self.assertEqual((BP / "functions/barkguard_test.mcfunction").read_text(), "give @s ccoriginal_cc:barkguard_charm 1\n")

    def test_deterministic_build_hashes_and_labels(self):
        builder = ROOT / "tools/build_barkguard_charm.py"
        packet_path = FEATURE / "reports/candidate-packet.json"
        committed_packet = packet_path.read_bytes()
        subprocess.run(["python3", str(builder)], cwd=ROOT, check=True, capture_output=True)
        package = FEATURE / "dist/barkguard-charm-INTERNAL-TEST.mcaddon"
        first = hashlib.sha256(package.read_bytes()).hexdigest()
        subprocess.run(["python3", str(builder)], cwd=ROOT, check=True, capture_output=True)
        second = hashlib.sha256(package.read_bytes()).hexdigest()
        self.assertEqual(first, second)
        self.assertEqual(packet_path.read_bytes(), committed_packet)
        packet = json.loads(packet_path.read_text())
        self.assertEqual(packet["package"]["sha256"], first)
        self.assertEqual(
            packet["worktree"],
            "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/barkguard-charm",
        )
        self.assertIn("NOT PHYSICAL PS4 CERTIFIED", packet["labels"])
        with zipfile.ZipFile(package) as archive:
            self.assertIn("behavior_pack/manifest.json", archive.namelist())
            self.assertIn("resource_pack/manifest.json", archive.namelist())


if __name__ == "__main__":
    unittest.main()
