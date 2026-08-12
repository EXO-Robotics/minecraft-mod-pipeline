#!/usr/bin/env python3
"""Bind ten native-qualified Skyreach plants as bounded Stable custom blocks."""

from __future__ import annotations

import argparse, hashlib, json
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REPRESENTATIVES = {"wind_reed_plant", "hanging_sky_vine"}
ASSETS = ("cliff_flower", "cloud_moss", "cloudpuff_plant", "floating_blossom", "nest_thatch_tuft", "rope_root", "shelf_shrub", "skybloom", "wind_reed_plant", "hanging_sky_vine")
DISPLAY = {a: a.replace("_plant", "").replace("_", " ").title() for a in ASSETS}
GROUND = ("aionbound:cliff_stone", "aionbound:cliff_gravel", "aionbound:pale_shelf_stone", "aionbound:sky_moss_block", "minecraft:stone")
ATTACH = ("aionbound:cliff_stone", "aionbound:pale_shelf_stone", "aionbound:rope_timber", "aionbound:skyreach_log", "aionbound:skyreach_wood")

@dataclass(frozen=True)
class Spec:
    asset: str
    faces: tuple[str, ...]
    supports: tuple[str, ...]
    iterations: int
    denominator: int

SPECS = tuple(Spec(a, ("down", "side"), ATTACH, 1, 96) if a in {"rope_root", "hanging_sky_vine"} else Spec(a, ("up",), GROUND, 1 if a in {"cliff_flower", "floating_blossom", "skybloom"} else 2, 96 if a in {"cliff_flower", "floating_blossom", "skybloom"} else 64) for a in ASSETS)

def encoded(value): return (json.dumps(value, indent=2) + "\n").encode()
def evidence(asset):
    lane = "representative" if asset in REPRESENTATIVES else "plants"
    return REPO / f"engineering/native-assets/skyreach/{lane}/evidence/{asset}"

def block(spec):
    return {"format_version":"1.21.80","minecraft:block":{"description":{"identifier":f"aionbound:{spec.asset}"},"components":{
        "minecraft:display_name":DISPLAY[spec.asset],"minecraft:collision_box":False,
        "minecraft:selection_box":{"origin":[-7,0,-7],"size":[14,16,14]},
        "minecraft:destructible_by_mining":{"seconds_to_destroy":0.1},
        "minecraft:geometry":f"geometry.aionbound.{spec.asset}",
        "minecraft:material_instances":{"*":{"texture":spec.asset,"render_method":"alpha_test","ambient_occlusion":False,"face_dimming":False}},
        "minecraft:placement_filter":{"conditions":[{"allowed_faces":list(spec.faces),"block_filter":list(spec.supports)}]}
    }}}

def feature(spec):
    face = "all" if "side" in spec.faces else "bottom"
    return {"format_version":"1.21.40","minecraft:single_block_feature":{"description":{"identifier":f"aionbound:sr_ecology_{spec.asset}"},"places_block":f"aionbound:{spec.asset}","enforce_placement_rules":True,"enforce_survivability_rules":True,"may_replace":["minecraft:air"],"may_attach_to":{"min_sides_must_attach":1,"auto_rotate":face=="all",face:list(spec.supports)}}}

def rule(spec):
    return {"format_version":"1.21.40","minecraft:feature_rules":{"description":{"identifier":f"aionbound:sr_ecology_{spec.asset}.feature_rule","places_feature":f"aionbound:sr_ecology_{spec.asset}"},"conditions":{"placement_pass":"surface_pass","minecraft:biome_filter":{"all_of":[{"test":"has_biome_tag","operator":"==","value":"overworld"},{"test":"has_biome_tag","operator":"!=","value":"ocean"},{"any_of":[{"test":"has_biome_tag","operator":"==","value":"mountain"},{"test":"has_biome_tag","operator":"==","value":"hills"}]}]}},"distribution":{"coordinate_eval_order":"xzy","iterations":spec.iterations,"scatter_chance":{"numerator":1,"denominator":spec.denominator},"x":{"distribution":"uniform","extent":[0,15]},"y":"q.heightmap(v.worldx, v.worldz)","z":{"distribution":"uniform","extent":[0,15]}}}}

def build():
    files={}; blocks=json.loads((REPO/"resource_pack/blocks.json").read_text()); terrain=json.loads((REPO/"resource_pack/textures/terrain_texture.json").read_text()); lang=(REPO/"resource_pack/texts/en_US.lang").read_text().splitlines(); prefixes=tuple(f"tile.aionbound:{a}.name=" for a in ASSETS); lang=[x for x in lang if not x.startswith(prefixes)]; rows=[]
    for spec in SPECS:
        root=evidence(spec.asset); geo=root/"native-exports/pass-2.geo.json"; tex=root/f"native-project/textures/{spec.asset}.png"
        gp=REPO/f"resource_pack/models/aionbound/skyreach/{spec.asset}.geo.json"; tp=REPO/f"resource_pack/textures/aionbound/skyreach/plants/{spec.asset}.png"; bp=REPO/f"behavior_pack/blocks/{spec.asset}.block.json"; fp=REPO/f"behavior_pack/features/sr_ecology_{spec.asset}.feature.json"; rp=REPO/f"behavior_pack/feature_rules/sr_ecology_{spec.asset}.feature_rule.json"
        files[gp]=geo.read_bytes(); files[tp]=tex.read_bytes(); files[bp]=encoded(block(spec)); files[fp]=encoded(feature(spec)); files[rp]=encoded(rule(spec)); blocks[f"aionbound:{spec.asset}"]={"sound":"grass","textures":spec.asset}; terrain["texture_data"][spec.asset]={"textures":f"textures/aionbound/skyreach/plants/{spec.asset}"}; lang.append(f"tile.aionbound:{spec.asset}.name={DISPLAY[spec.asset]}")
        rows.append({"asset":spec.asset,"native_lane":"representative" if spec.asset in REPRESENTATIVES else "plants","geometry_sha256":hashlib.sha256(geo.read_bytes()).hexdigest(),"texture_sha256":hashlib.sha256(tex.read_bytes()).hexdigest(),"iterations":spec.iterations,"denominator":spec.denominator,"attempts_per_chunk_before_filters":spec.iterations/spec.denominator})
    files[REPO/"resource_pack/blocks.json"]=encoded(blocks); files[REPO/"resource_pack/textures/terrain_texture.json"]=encoded(terrain); files[REPO/"resource_pack/texts/en_US.lang"]=("\n".join(lang)+"\n").encode()
    report={"schema":"aionbound.wave1.skyreach.plant-product.v1","status":"PASS_STATIC_SOURCE_BINDING","base_commit":"13c3ddd67aa11bc0fecd3f592601ad0264dc1b2b","scope":list(ASSETS),"assets":rows,"density":{"aggregate_attempts_per_chunk_before_filters":sum(x["attempts_per_chunk_before_filters"] for x in rows),"regional_proxy":"overworld non-ocean mountain-or-hills"},"constraints":{"exact_pass_2_geometry_bytes":True,"exact_native_texture_bytes":True,"loot_or_acquisition_added":False,"recipes_added":False,"script_animation_added":False,"authority_gated_surfaces_added":False},"proof_boundary":["static source only","not live worldgen survivability rendering BDS client console Marketplace or release proof"]}; files[OUT/"SKYREACH_PLANT_PRODUCT_REPORT.json"]=encoded(report); return files,report

def main():
    p=argparse.ArgumentParser(); p.add_argument("--check",action="store_true"); args=p.parse_args(); files,_=build(); bad=[]
    for path,data in files.items():
        if args.check:
            if not path.is_file() or path.read_bytes()!=data: bad.append(str(path.relative_to(REPO)))
        else: path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    print(json.dumps({"status":"FAIL" if bad else "PASS","mismatches":bad,"outputs":len(files)},indent=2)); return bool(bad)
if __name__=="__main__": raise SystemExit(main())
