from __future__ import annotations
import json, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FEATURE=ROOT/"production/features/resonance-sling"
MANIFEST=ROOT/"production/reconstruction-waves/forest-wave-1/resonance_sling/original-production-manifest.json"

def test_original_lane_and_limits():
    m=json.loads(MANIFEST.read_text())
    assert m["production_lane"]=="ORIGINAL_BEDROCK_NATIVE"
    assert m["originality"]["java_fidelity_claimed"] is False
    assert m["originality"]["third_party_production_materials"] is False
    assert m["performance_limits"]=={"global_scans_per_tick":0,"persistent_records":0,"particle_count_per_impact":6,"animation_controllers":1,"maximum_active_projectiles":16}

def test_pack_references_and_stable_surface():
    bp=FEATURE/"bedrock/behavior_pack";rp=FEATURE/"bedrock/resource_pack"
    for p in [bp/"manifest.json",bp/"items/resonance_sling.json",bp/"items/resonance_pebble.json",bp/"entities/resonance_pulse.json",rp/"textures/item_texture.json",rp/"models/entity/resonance_pulse.geo.json"]:
        json.loads(p.read_text())
    script=(bp/"scripts/main.js").read_text()
    assert "runInterval" not in script and "getEntities(" not in script
    assert "world.afterEvents.entitySpawn" in script
    assert "world.afterEvents.entityRemove" in script
    assert "setDynamicProperty" not in script
    assert '"@minecraft/server","version":"2.0.0"' in (bp/"manifest.json").read_text().replace(" ","").replace("\n","")
    sling=json.loads((bp/"items/resonance_sling.json").read_text())["minecraft:item"]["components"]
    pebble=json.loads((bp/"items/resonance_pebble.json").read_text())["minecraft:item"]["components"]
    assert sling["minecraft:shooter"]["ammunition"][0]["item"]=="ccoriginal_cc:resonance_pebble"
    assert sling["minecraft:shooter"]["max_draw_duration"]==0.7
    assert pebble["minecraft:projectile"]["projectile_entity"]=="ccoriginal_cc:resonance_pulse"
    pulse=json.loads((bp/"entities/resonance_pulse.json").read_text())["minecraft:entity"]["components"]["minecraft:projectile"]
    assert pulse["on_hit"]["impact_damage"]["damage"]==4
    assert pulse["on_hit"]["remove_on_hit"]=={}
    attachable=json.loads((rp/"attachables/resonance_sling.entity.json").read_text())
    assert attachable["minecraft:attachable"]["description"]["geometry"]["default"]=="geometry.ccoriginal_cc.resonance_sling"
    native=json.loads((ROOT/"prototypes/blockbench/resonance_sling/resonance_sling.geo.json").read_text())
    bones=native["minecraft:geometry"][0]["bones"]
    assert [b["name"] for b in bones]==["root","grip","fork","pouch"]
    assert bones[-1]["locators"]=={"locator.pouch":[0,11,-1.5],"locator.release":[0,12,-2]}

def test_preview_diagnostic_is_separate_and_four_player():
    pack=FEATURE/"diagnostic/preview-simulated-player"
    manifest=json.loads((pack/"manifest.json").read_text())
    assert any(d.get("module_name")=="@minecraft/server-gametest" and "beta" in d["version"] for d in manifest["dependencies"])
    probes=json.loads((pack/"probes.json").read_text())
    assert probes["preview_only"] is True
    source=(pack/"scripts/main.js").read_text()
    assert "for(let i=0;i<4;i++)spawn(i)" in source
    assert "four_player_concurrent_use" in probes["cycle_1_checks"]
    assert "restart_no_persistent_projectiles" in probes["cycle_2_checks"]

def test_deterministic_internal_packages_exist_and_are_labeled():
    receipt=json.loads((FEATURE/"reports/artifact-manifest.json").read_text())
    assert "NOT PHYSICAL PS4 CERTIFIED" in receipt["labels"]
    for name in ["resonance-sling-INTERNAL-TEST.mcaddon","resonance-sling-INTERNAL-TEST.mcworld"]:
        path=FEATURE/"dist"/name
        assert path.is_file()
        with zipfile.ZipFile(path) as z: assert "world_behavior_packs.json" in z.namelist() or "behavior_pack/manifest.json" in z.namelist()
