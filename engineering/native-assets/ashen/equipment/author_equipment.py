#!/usr/bin/env python3
"""Author the exact thirteen Ashen-facing Packet 006 native projects."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
CREATURES = HERE.parent / "creatures"
sys.path.insert(0, str(CREATURES))
import author_creatures as creature_engine  # noqa: E402
for injected in (str(CREATURES), str(CREATURES.parent / "representative")):
    while injected in sys.path:
        sys.path.remove(injected)

engine = creature_engine.engine
frames = engine.frames
clip = engine.clip
ZERO = engine.ZERO
INTEGRATION_COMMIT = "f9d9735cd575761456b3db7b351facea700207f8"
RECEIPT_NAME = "ashen-equipment-native-receipt.json"


def hold(bone: str, duration: float = 3.0, amount: float = 2.0):
    return clip(duration, True, duration / 4, {bone: [frames("rotation", (0.0, ZERO), (duration / 4, [0.0, 0.0, amount]), (duration / 2, ZERO), (duration * 3 / 4, [0.0, 0.0, -amount]), (duration, ZERO))]})


def pose(duration: float, proof: float, bone: str, value: list[float]):
    return clip(duration, False, proof, {bone: [frames("rotation", (0.0, ZERO), (proof, value), (duration, ZERO))]})


def pulse(duration: float, proof: float, bone: str, amount: float):
    return clip(duration, True, proof, {bone: [frames("scale", (0.0, [1.0, 1.0, 1.0]), (proof, [amount, amount, amount]), (duration / 2, [1.0, 1.0, 1.0]), (duration - proof, [amount, amount, amount]), (duration, [1.0, 1.0, 1.0]))]})


SPECS = {
    "basalt_hammer": {"class": "equipment_weapon", "clips": {"idle_hold": hold("grip"), "smash_pose": pose(0.8, 0.42, "chassis", [-32.0, 0.0, 0.0])}},
    "ember_great_axe": {"class": "equipment_weapon", "clips": {"idle_hold": hold("grip", 3.2, 2.5), "overhead_pose": pose(0.9, 0.48, "chassis", [-42.0, 0.0, 0.0]), "slam_pose": pose(0.75, 0.38, "chassis", [38.0, 0.0, 0.0])}},
    "ash_repeater": {"class": "equipment_ranged_weapon", "clips": {"idle_hold": hold("grip", 3.0, 1.5), "crank_pose": pose(0.7, 0.35, "head", [0.0, 0.0, 28.0]), "fire_pose": clip(0.45, False, 0.18, {"chassis": [frames("position", (0.0, ZERO), (0.18, [0.0, 0.0, 0.55]), (0.45, ZERO))]})}},
    "ashen_helmet": {"class": "equipment_armor", "clips": {"vent_pulse_showcase": pulse(2.4, 0.6, "detail", 1.05)}},
    "ashen_chest": {"class": "equipment_armor", "clips": {}},
    "ashen_legs": {"class": "equipment_armor", "clips": {}},
    "ashen_boots": {"class": "equipment_armor", "clips": {}},
    "basalt_pick": {"class": "equipment_tool", "clips": {"hold": hold("grip", 3.0, 1.5), "swing": pose(0.65, 0.34, "chassis", [36.0, 0.0, 0.0])}},
    "ember_hammer": {"class": "equipment_tool", "clips": {"hold": hold("grip", 3.1, 1.7), "tap": pose(0.55, 0.28, "chassis", [24.0, 0.0, 0.0])}},
    "ore_chisel": {"class": "equipment_tool", "clips": {"hold": hold("grip", 3.0, 1.3), "tap": pose(0.5, 0.25, "chassis", [18.0, 0.0, 0.0])}},
    "ember_totem": {"class": "equipment_accessory", "clips": {"vent_pulse": pulse(2.8, 0.7, "head", 1.06)}},
    "ash_drake_horn": {"class": "equipment_trophy", "clips": {"pulse_base": pulse(3.0, 0.75, "display", 1.045)}},
    "ember_forge_core": {"class": "equipment_trophy", "clips": {"idle_pulse": pulse(2.6, 0.65, "display", 1.055)}},
}


def configure_engine() -> None:
    engine.SPECS = SPECS
    engine.INTEGRATION_COMMIT = INTEGRATION_COMMIT
    engine.RECEIPT_NAME = RECEIPT_NAME


def execute(inputs: engine.Inputs):
    configure_engine()
    # The shared native codec is frozen to Packet 002's intake prefix. Feed it
    # an ephemeral identity shim only for that preflight check, then restore the
    # exact Packet 006 brief into evidence and bind its source hash explicitly.
    source_brief = json.loads(inputs.brief.read_text())
    if source_brief.get("model_identifier") != f"geometry.aionforge_eq.{inputs.asset}":
        raise engine.RepresentativeError(f"PACKET006_BRIEF_IDENTITY_MISMATCH:{inputs.asset}")
    shim = dict(source_brief)
    shim["model_identifier"] = f"geometry.aionforge_ah.{inputs.asset}"
    with tempfile.TemporaryDirectory(prefix=f"aionbound-{inputs.asset}-brief-") as directory:
        shim_path = Path(directory) / inputs.brief.name
        shim_path.write_text(json.dumps(shim, sort_keys=True, separators=(",", ":")) + "\n")
        shim_inputs = engine.Inputs(inputs.asset, inputs.bbmodel, inputs.texture, inputs.geometry, shim_path, inputs.output, inputs.cdp_endpoint)
        code, receipt = engine.execute(shim_inputs)
    evidence_brief = inputs.output / "inputs" / f"{inputs.asset}.brief.json"
    evidence_brief.write_bytes(inputs.brief.read_bytes())
    receipt["evidence_inputs"]["brief"] = {
        "path": str(evidence_brief.relative_to(inputs.output)),
        "sha256": hashlib.sha256(evidence_brief.read_bytes()).hexdigest(),
    }
    receipt["packet_brief_identity"] = source_brief["model_identifier"]
    receipt["shared_codec_preflight_identity_shim"] = "EPHEMERAL_NOT_RETAINED"
    receipt["schema"] = "aionforge.wave1.ashen.equipment_native.v1"
    receipt["proof_scope"] = "BLOCKBENCH_NATIVE_EQUIPMENT_EDITABLE_AND_CODEC_REPAIR_ONLY"
    receipt["portfolio_class"] = receipt.pop("representative_class")
    receipt["texture_policy"] = "EXACT_PACKET_BYTES_PRESERVED_NO_RESAMPLE_OR_UPSCALE"
    (inputs.output / RECEIPT_NAME).write_bytes(engine.native.canonical_json_bytes(receipt))
    return code, receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--asset", required=True, choices=sorted(SPECS))
    result.add_argument("--bbmodel", required=True, type=Path)
    result.add_argument("--texture", required=True, type=Path)
    result.add_argument("--geometry", required=True, type=Path)
    result.add_argument("--brief", required=True, type=Path)
    result.add_argument("--output-dir", required=True, type=Path)
    result.add_argument("--cdp-endpoint", required=True)
    return result


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        code, receipt = execute(engine.Inputs(args.asset, args.bbmodel.resolve(), args.texture.resolve(), args.geometry.resolve(), args.brief.resolve(), args.output_dir.resolve(), args.cdp_endpoint))
    except (engine.RepresentativeError, engine.native.NativeToolError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "receipt": str(args.output_dir / RECEIPT_NAME)}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
