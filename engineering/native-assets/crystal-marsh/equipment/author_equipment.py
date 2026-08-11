#!/usr/bin/env python3
"""Native-repair the exact eleven Crystal-facing Packet 006 projects."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
CREATURES = HERE.parents[1] / "ashen" / "creatures"
sys.path.insert(0, str(CREATURES))
import author_creatures as creature_engine  # noqa: E402
for injected in (str(CREATURES), str(CREATURES.parent / "representative")):
    while injected in sys.path:
        sys.path.remove(injected)

engine = creature_engine.engine
frames = engine.frames
clip = engine.clip
ZERO = engine.ZERO
INTEGRATION_COMMIT = "d6c1ab2c18ac0ec21a0218bf2c807d4177071673"
INTEGRATION_TREE = "52e0b9bde38158dc1287579931e0d86ce98aa4d8"
RECEIPT_NAME = "crystal-equipment-native-receipt.json"


def hold(bone: str, duration: float = 3.0, amount: float = 2.0):
    quarter = duration / 4
    return clip(duration, True, quarter, {bone: [frames("rotation", (0.0, ZERO), (quarter, [0.0, 0.0, amount]), (duration / 2, ZERO), (quarter * 3, [0.0, 0.0, -amount]), (duration, ZERO))]})


def pose(duration: float, proof: float, bone: str, value: list[float]):
    return clip(duration, False, proof, {bone: [frames("rotation", (0.0, ZERO), (proof, value), (duration, ZERO))]})


def pulse(duration: float, proof: float, bone: str, amount: float):
    return clip(duration, True, proof, {bone: [frames("scale", (0.0, [1.0, 1.0, 1.0]), (proof, [amount, amount, amount]), (duration / 2, [1.0, 1.0, 1.0]), (duration - proof, [amount, amount, amount]), (duration, [1.0, 1.0, 1.0]))]})


def sway(duration: float, proof: float, bone: str, amount: float):
    return clip(duration, True, proof, {bone: [frames("rotation", (0.0, ZERO), (proof, [amount, 0.0, amount / 2]), (duration / 2, ZERO), (duration - proof, [-amount, 0.0, -amount / 2]), (duration, ZERO))]})


SPECS = {
    "crystal_pike": {"class": "equipment_weapon", "clips": {"idle_hold": hold("grip", 3.2, 1.6), "thrust_pose": pose(0.72, 0.34, "chassis", [-16.0, 0.0, 0.0])}},
    "prism_bow": {"class": "equipment_ranged_weapon", "clips": {"idle_hold": hold("grip", 3.0, 1.4), "draw_pose": pose(0.82, 0.43, "head", [0.0, 0.0, -18.0]), "fire_pose": clip(0.48, False, 0.2, {"chassis": [frames("position", (0.0, ZERO), (0.2, [0.0, 0.0, 0.45]), (0.48, ZERO))]})}},
    "crystal_circlet": {"class": "equipment_armor", "clips": {"pulse": pulse(2.8, 0.7, "detail", 1.045)}},
    "explorer_cloak": {"class": "equipment_armor", "clips": {"idle_sway": sway(3.6, 0.9, "body", 2.8)}},
    "crystal_shovel": {"class": "equipment_tool", "clips": {"hold": hold("grip", 3.0, 1.3), "dig": pose(0.66, 0.34, "chassis", [34.0, 0.0, 0.0])}},
    "marsh_sickle": {"class": "equipment_tool", "clips": {"hold": hold("grip", 3.0, 1.2), "reap": pose(0.62, 0.31, "chassis", [0.0, 0.0, -32.0])}},
    "crystal_talisman": {"class": "equipment_accessory", "clips": {"pulse": pulse(2.7, 0.675, "head", 1.055)}},
    "marsh_idol": {"class": "equipment_accessory", "clips": {"idle": sway(3.4, 0.85, "head", 2.2)}},
    "marsh_wight_mask": {"class": "equipment_trophy", "clips": {"eye_glow": pulse(2.6, 0.65, "display", 1.05)}},
    "moon_pearl_pedestal": {"class": "equipment_trophy", "clips": {"soft_pulse": pulse(3.0, 0.75, "display", 1.04)}},
    "crystal_obelisk_fragment": {"class": "equipment_trophy", "clips": {"pulse": pulse(2.8, 0.7, "display", 1.05)}},
}


def configure_engine() -> None:
    engine.SPECS = SPECS
    engine.INTEGRATION_COMMIT = INTEGRATION_COMMIT
    engine.RECEIPT_NAME = RECEIPT_NAME


def execute(inputs: engine.Inputs):
    configure_engine()
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
    receipt["integration_authority"] = {"commit": INTEGRATION_COMMIT, "tree": INTEGRATION_TREE}
    receipt["packet_brief_identity"] = source_brief["model_identifier"]
    receipt["shared_codec_preflight_identity_shim"] = "EPHEMERAL_NOT_RETAINED"
    receipt["schema"] = "aionforge.wave1.crystal_marsh.equipment_native.v1"
    receipt["proof_scope"] = "BLOCKBENCH_NATIVE_EQUIPMENT_EDITABLE_AND_CODEC_REPAIR_ONLY"
    receipt["portfolio_class"] = receipt.pop("representative_class")
    receipt["texture_policy"] = "EXACT_PACKET_32X32_BYTES_PRESERVED_NO_RESAMPLE_OR_UPSCALE"
    receipt["texture_contract_note"] = "Packet brief permits or declares up to 64x64, but the authoritative editable and export PNG are exact byte-identical 32x32 RGBA; no source authority requests an upscale."
    receipt["non_claims"] = ["BP_RP", "ICONS", "GAMEPLAY", "RECIPES", "LOOT", "AUTHORITY", "BDS", "BEDROCK_CLIENT", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"]
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
