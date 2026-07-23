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
    assert "materializeCache(a)" in script
    assert 'world.setDynamicProperty("ccoriginal_cc:signal_ruin_completed",true)' in script
    assert 'type:"minecraft:chest_minecart"' in script
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
    reservation = function.index("activeAnchors.set(a.id,a)")
    first_mutation = function.index('set(a,"schema",1)')
    assert cap_check < feedback < reservation < first_mutation
    assert function[cap_check:reservation].count("set(a,") == 0
    assert "activeAnchors.delete(a.id)" in function


def test_interval_uses_only_the_two_entry_active_registry() -> None:
    script = (FEATURE / "bedrock/behavior_pack/scripts/signal_ruin.js").read_text()
    assert "const activeAnchors = new Map()" in script
    assert "function activeInstances(){\n  return activeAnchors.size;" in script
    tick = script[script.index("system.runInterval"):]
    assert "for(const [id,a] of activeAnchors)" in tick
    assert "world.getDimension" not in tick
    assert 'getEntities({type:"ccoriginal_cc:signal_ruin_anchor"})' not in tick


def test_reward_cache_is_a_persistent_idempotent_witness() -> None:
    script = (FEATURE / "bedrock/behavior_pack/scripts/signal_ruin.js").read_text()
    reward = script[script.index("function materializeCache"):script.index("function activate")]
    witness_lookup = reward.index('type:"minecraft:chest_minecart"')
    conditional_spawn = reward.index("if(!cache)")
    inventory_fill = reward.index("container.clearAll()")
    commit = reward.index('set(a,"reward_issued",true)')
    completion_marker = reward.index('world.setDynamicProperty("ccoriginal_cc:signal_ruin_completed",true)')
    assert witness_lookup < conditional_spawn < inventory_fill < commit < completion_marker
    assert 'cache.addTag("ccoriginal_cc_signal_ruin_cache")' in reward
    assert "loot spawn" not in reward


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
