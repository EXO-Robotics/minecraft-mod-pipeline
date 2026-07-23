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
    assert "world.afterEvents.itemUse" in script
    assert "projectileHitEntity" in script and "projectileHitBlock" in script
    assert "setDynamicProperty" not in script
    assert '"@minecraft/server","version":"2.0.0"' in (bp/"manifest.json").read_text().replace(" ","").replace("\n","")

def test_deterministic_internal_packages_exist_and_are_labeled():
    receipt=json.loads((FEATURE/"reports/artifact-manifest.json").read_text())
    assert "NOT PHYSICAL PS4 CERTIFIED" in receipt["labels"]
    for name in ["resonance-sling-INTERNAL-TEST.mcaddon","resonance-sling-INTERNAL-TEST.mcworld"]:
        path=FEATURE/"dist"/name
        assert path.is_file()
        with zipfile.ZipFile(path) as z: assert "world_behavior_packs.json" in z.namelist() or "behavior_pack/manifest.json" in z.namelist()
