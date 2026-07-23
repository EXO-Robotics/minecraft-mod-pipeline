import hashlib
import json
import subprocess
import sys
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


def test_exact_consumption_gift_atomic_contention_and_restart_safe_model():
    entity = load("bedrock/behavior_pack/entities/mossback_forager.json")["minecraft:entity"]
    assert list(entity["description"]["properties"]) == ["ccoriginal_cc:mossback_cooling"]
    interaction = entity["component_groups"]["ccoriginal_cc:ready"]["minecraft:interact"]["interactions"][0]
    assert interaction["use_item"] is True
    assert interaction["on_interact"]["filters"]["value"] == "minecraft:sweet_berries"
    sequence = entity["events"]["ccoriginal_cc:accept_berry"]["sequence"]
    assert sequence[0] == {"remove": {"component_groups": ["ccoriginal_cc:ready"]}}
    assert sum("spawn_loot" in step for step in sequence) == 1
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
