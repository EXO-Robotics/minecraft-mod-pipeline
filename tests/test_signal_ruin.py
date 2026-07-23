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


def test_structure_is_original_bounded_and_valid_little_endian_nbt() -> None:
    spec = json.loads((PROTO / "signal_ruin.structure.json").read_text())
    assert spec["size"] == [11, 9, 11]
    assert len(spec["blocks"]) == len({tuple(row["pos"]) for row in spec["blocks"]})
    assert all(0 <= row["pos"][i] < spec["size"][i] for row in spec["blocks"] for i in range(3))
    structure = FEATURE / "bedrock/behavior_pack/structures/ccoriginal_cc/signal_ruin.mcstructure"
    assert structure.stat().st_size < 131072
    raw = structure.read_bytes()
    assert raw[0] == 3 and b"format_version" in raw and b"block_palette" in raw
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
    assert "system.runInterval" in script and "},20)" in script
    assert "reward_issued" in script and 'if(get(a,"reward_issued",false))' in script
    assert "playerInteractWithEntity" in script
    assert "absent>=20" in script and 'set(a,"state","READY")' in script
    assert "worldLoad" in script and "spawnWave(a,Math.max" in script
    assert script.count("runTimeout") == 1
    assert "runJob" not in script
    scenarios = json.loads((FEATURE / "tests/scenarios.json").read_text())
    assert len(scenarios["scenarios"]) == 9


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
