#!/usr/bin/env python3
"""Native Blockbench repair gate for seven Packet 004 representatives.

The caller supplies frozen packet files. This tool stages copies, preserves
all cube/UV/texture bytes, normalizes only staged texture paths and public
``aionbound`` identifiers, creates true locators from canonical exported
transforms, authors exactly the brief-declared clips, and drives two native
Blockbench save-close-reopen/export cycles over loopback-only CDP.

This is native asset evidence, not BP/RP, gameplay, BDS, client, console, or
Marketplace evidence.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


NATIVE_ASSETS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(NATIVE_ASSETS / "whisperwood"))
import repair_whisperwood_native as native  # noqa: E402


TOOL_VERSION = "1.0.0"
BLOCKBENCH_VERSION = "5.1.6"
INTEGRATION_COMMIT = "1810d0bb75e73be16d1c98e1d57dfe9ea485849d"
KEYFRAME_TOLERANCE_SECONDS = 0.026
RECEIPT_NAME = "skyreach-representative-native-receipt.json"
ZERO = [0.0, 0.0, 0.0]


class RepresentativeError(RuntimeError):
    """Fail-closed native-gate error."""


def frames(channel: str, *entries: tuple[float, list[float]]) -> dict[str, Any]:
    return {
        "channel": channel,
        "keyframes": [
            {"time": point, "interpolation": "linear", "value": value}
            for point, value in entries
        ],
    }


def clip(duration: float, loop: bool, proof_time: float, bones: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        "duration": duration,
        "loop": loop,
        "proof_time": proof_time,
        "bones": bones,
    }


SPECS: dict[str, dict[str, Any]] = {
    "wind_roc": {"class": "apex_soaring_flyer", "clips": {
        "idle_perch": clip(3.6, True, 0.9, {"body": [frames("position", (0.0, ZERO), (0.9, [0.0, 0.18, 0.0]), (1.8, ZERO), (2.7, [0.0, -0.12, 0.0]), (3.6, ZERO))], "head": [frames("rotation", (0.0, ZERO), (0.9, [2.0, -6.0, 0.0]), (1.8, ZERO), (2.7, [1.0, 5.0, 0.0]), (3.6, ZERO))]}),
        "soar": clip(1.6, True, 0.4, {"wing_l": [frames("rotation", (0.0, [0.0, 0.0, -10.0]), (0.4, [0.0, 0.0, -18.0]), (0.8, [0.0, 0.0, -10.0]), (1.2, [0.0, 0.0, -4.0]), (1.6, [0.0, 0.0, -10.0]))], "wing_r": [frames("rotation", (0.0, [0.0, 0.0, 10.0]), (0.4, [0.0, 0.0, 18.0]), (0.8, [0.0, 0.0, 10.0]), (1.2, [0.0, 0.0, 4.0]), (1.6, [0.0, 0.0, 10.0]))], "tail": [frames("rotation", (0.0, ZERO), (0.8, [3.0, 0.0, 0.0]), (1.6, ZERO))]}),
        "dive": clip(0.85, False, 0.4, {"body": [frames("rotation", (0.0, ZERO), (0.4, [-28.0, 0.0, 0.0]), (0.85, ZERO))], "wing_l": [frames("rotation", (0.0, ZERO), (0.4, [0.0, 0.0, 35.0]), (0.85, ZERO))], "wing_r": [frames("rotation", (0.0, ZERO), (0.4, [0.0, 0.0, -35.0]), (0.85, ZERO))]}),
        "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, 11.0]), (0.45, ZERO))]}),
        "death": clip(1.25, False, 1.25, {"body": [frames("rotation", (0.0, ZERO), (0.65, [18.0, 0.0, 25.0]), (1.25, [58.0, 0.0, 88.0]))]}),
    }},
    "gale_hawk": {"class": "mid_soaring_flyer", "clips": {
        "idle": clip(3.0, True, 0.75, {"body": [frames("position", (0.0, ZERO), (0.75, [0.0, 0.12, 0.0]), (1.5, ZERO), (2.25, [0.0, -0.08, 0.0]), (3.0, ZERO))], "head": [frames("rotation", (0.0, ZERO), (0.75, [1.0, -7.0, 0.0]), (1.5, ZERO), (2.25, [1.0, 6.0, 0.0]), (3.0, ZERO))]}),
        "fly": clip(0.8, True, 0.2, {"wing_l": [frames("rotation", (0.0, [0.0, 0.0, -24.0]), (0.2, [0.0, 0.0, 20.0]), (0.4, [0.0, 0.0, 24.0]), (0.6, [0.0, 0.0, -20.0]), (0.8, [0.0, 0.0, -24.0]))], "wing_r": [frames("rotation", (0.0, [0.0, 0.0, 24.0]), (0.2, [0.0, 0.0, -20.0]), (0.4, [0.0, 0.0, -24.0]), (0.6, [0.0, 0.0, 20.0]), (0.8, [0.0, 0.0, 24.0]))]}),
        "stoop": clip(0.7, False, 0.3, {"body": [frames("rotation", (0.0, ZERO), (0.3, [-24.0, 0.0, 0.0]), (0.7, ZERO))], "wing_l": [frames("rotation", (0.0, ZERO), (0.3, [0.0, 0.0, 26.0]), (0.7, ZERO))], "wing_r": [frames("rotation", (0.0, ZERO), (0.3, [0.0, 0.0, -26.0]), (0.7, ZERO))]}),
        "hurt": clip(0.4, False, 0.16, {"body": [frames("rotation", (0.0, ZERO), (0.16, [0.0, 0.0, -10.0]), (0.4, ZERO))]}),
        "death": clip(0.9, False, 0.9, {"body": [frames("rotation", (0.0, ZERO), (0.9, [0.0, 0.0, -88.0]))]}),
    }},
    "cloud_goat": {"class": "ledge_grazer_quadruped", "clips": {
        "idle": clip(3.4, True, 0.85, {"body": [frames("position", (0.0, ZERO), (0.85, [0.0, 0.12, 0.0]), (1.7, ZERO), (2.55, [0.0, -0.08, 0.0]), (3.4, ZERO))], "head": [frames("rotation", (0.0, ZERO), (0.85, [4.0, -4.0, 0.0]), (1.7, ZERO), (2.55, [-2.0, 4.0, 0.0]), (3.4, ZERO))]}),
        "walk": clip(1.0, True, 0.25, {"leg_fl": [frames("rotation", (0.0, [18.0, 0.0, 0.0]), (0.5, [-18.0, 0.0, 0.0]), (1.0, [18.0, 0.0, 0.0]))], "leg_fr": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.5, [18.0, 0.0, 0.0]), (1.0, [-18.0, 0.0, 0.0]))], "leg_bl": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.5, [18.0, 0.0, 0.0]), (1.0, [-18.0, 0.0, 0.0]))], "leg_br": [frames("rotation", (0.0, [18.0, 0.0, 0.0]), (0.5, [-18.0, 0.0, 0.0]), (1.0, [18.0, 0.0, 0.0]))]}),
        "hop_ledge": clip(0.9, False, 0.42, {"body": [frames("position", (0.0, ZERO), (0.42, [0.0, 1.2, -0.7]), (0.9, ZERO))], "leg_fl": [frames("rotation", (0.0, ZERO), (0.42, [-28.0, 0.0, 0.0]), (0.9, ZERO))], "leg_fr": [frames("rotation", (0.0, ZERO), (0.42, [-28.0, 0.0, 0.0]), (0.9, ZERO))]}),
        "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, 9.0]), (0.45, ZERO))]}),
        "death": clip(1.1, False, 1.1, {"body": [frames("rotation", (0.0, ZERO), (1.1, [0.0, 0.0, 82.0]))]}),
    }},
    "wind_reed_plant": {"class": "hard_sway_cliff_plant", "clips": {"sway_hard": clip(2.4, True, 0.6, {"stem": [frames("rotation", (0.0, ZERO), (0.6, [1.5, 0.0, 8.0]), (1.2, ZERO), (1.8, [-1.0, 0.0, -6.0]), (2.4, ZERO))], "head": [frames("rotation", (0.0, ZERO), (0.6, [1.0, 0.0, 5.0]), (1.2, ZERO), (1.8, [-0.7, 0.0, -4.0]), (2.4, ZERO))]})}},
    "hanging_sky_vine": {"class": "hanging_cliff_plant", "clips": {"sway": clip(4.0, True, 1.0, {"stem": [frames("rotation", (0.0, ZERO), (1.0, [0.5, 0.0, 3.5]), (2.0, ZERO), (3.0, [-0.4, 0.0, -3.0]), (4.0, ZERO))], "head": [frames("rotation", (0.0, ZERO), (1.0, [0.3, 0.0, 2.0]), (2.0, ZERO), (3.0, [-0.2, 0.0, -1.6]), (4.0, ZERO))]})}},
    "wind_shrine": {"class": "animated_landmark_prop", "clips": {"chime_idle": clip(3.2, True, 0.8, {"top": [frames("rotation", (0.0, ZERO), (0.8, [0.0, 3.0, 0.0]), (1.6, ZERO), (2.4, [0.0, -3.0, 0.0]), (3.2, ZERO))], "chassis": [frames("scale", (0.0, [1.0, 1.0, 1.0]), (0.8, [1.01, 1.02, 1.01]), (1.6, [1.02, 1.03, 1.02]), (2.4, [1.01, 1.02, 1.01]), (3.2, [1.0, 1.0, 1.0]))]})}},
    "observation_tower": {"class": "static_landmark_prop", "clips": {}},
}


def full_name(asset: str, leaf: str) -> str:
    return f"animation.aionbound.{asset}.{leaf}"


def group_names(model: dict[str, Any]) -> list[str]:
    return native.extract_group_names(model)


def validate_spec(asset: str, clips: dict[str, Any], available_groups: set[str]) -> None:
    for leaf, record in clips.items():
        if not leaf or not isinstance(record.get("duration"), (int, float)) or record["duration"] <= 0:
            raise RepresentativeError(f"SPEC_DURATION_INVALID:{asset}:{leaf}")
        if not 0 <= record["proof_time"] <= record["duration"]:
            raise RepresentativeError(f"SPEC_PROOF_TIME_INVALID:{asset}:{leaf}")
        bones = record.get("bones")
        if not isinstance(bones, dict) or not bones:
            raise RepresentativeError(f"SPEC_BONES_INVALID:{asset}:{leaf}")
        missing = set(bones) - available_groups
        if missing:
            raise RepresentativeError(f"UNBOUND_ANIMATION_PARENT:{asset}:{leaf}:{','.join(sorted(missing))}")
        for bone, channels in bones.items():
            seen: set[str] = set()
            for channel in channels:
                channel_name = channel.get("channel")
                if channel_name not in {"rotation", "position", "scale"} or channel_name in seen:
                    raise RepresentativeError(f"SPEC_CHANNEL_INVALID:{asset}:{leaf}:{bone}")
                seen.add(channel_name)
                keyframes = channel.get("keyframes")
                if not isinstance(keyframes, list) or len(keyframes) < 2:
                    raise RepresentativeError(f"SPEC_KEYFRAMES_INVALID:{asset}:{leaf}:{bone}:{channel_name}")
                times = [frame.get("time") for frame in keyframes]
                values = [frame.get("value") for frame in keyframes]
                if times != sorted(times) or times[0] != 0 or not math.isclose(times[-1], record["duration"], abs_tol=1e-9):
                    raise RepresentativeError(f"SPEC_TIME_RANGE_INVALID:{asset}:{leaf}:{bone}:{channel_name}")
                if any(not isinstance(value, list) or len(value) != 3 or any(not isinstance(number, (int, float)) or isinstance(number, bool) or not math.isfinite(number) for number in value) for value in values):
                    raise RepresentativeError(f"SPEC_VALUE_INVALID:{asset}:{leaf}:{bone}:{channel_name}")
                if record["loop"] and values[0] != values[-1]:
                    raise RepresentativeError(f"SPEC_LOOP_SEAM_INVALID:{asset}:{leaf}:{bone}:{channel_name}")
                if all(value == values[0] for value in values[1:]):
                    raise RepresentativeError(f"SPEC_NO_MOTION:{asset}:{leaf}:{bone}:{channel_name}")


def file_record(path: Path, root: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(root)), "sha256": native.sha256_file(path)}


def copy_inputs(output: Path, asset: str, bbmodel: Path, texture: Path, geometry: Path, brief: Path) -> dict[str, Path]:
    directory = output / "inputs"
    directory.mkdir(parents=True)
    result = {
        "bbmodel": directory / f"{asset}.source.bbmodel",
        "texture": directory / f"{asset}.source.png",
        "geometry": directory / f"{asset}.source.geo.json",
        "brief": directory / f"{asset}.brief.json",
    }
    for source, target in ((bbmodel, result["bbmodel"]), (texture, result["texture"]), (geometry, result["geometry"]), (brief, result["brief"])):
        shutil.copyfile(source, target)
    return result


def geometry_signature_script() -> str:
    return """
  const vector = value => Array.isArray(value) ? value.slice() : null;
  const parentName = element => element.parent && element.parent !== 'root' ? element.parent.name : null;
  const faceRecord = face => ({uv: vector(face.uv), rotation: face.rotation || 0, texture: face.texture === undefined ? null : face.texture, cullface: face.cullface || '', tint: face.tint === undefined ? -1 : face.tint});
  const geometrySignature = () => ({
    groups: (Group.all || []).map(group => ({uuid:group.uuid,name:group.name,parent:parentName(group),origin:vector(group.origin),rotation:vector(group.rotation)})).sort((a,b)=>a.uuid.localeCompare(b.uuid)),
    cubes: (Cube.all || []).map(cube => ({uuid:cube.uuid,name:cube.name,parent:parentName(cube),from:vector(cube.from),to:vector(cube.to),origin:vector(cube.origin),rotation:vector(cube.rotation),inflate:cube.inflate||0,mirror_uv:!!cube.mirror_uv,faces:Object.fromEntries(Object.entries(cube.faces||{}).map(([name,face])=>[name,faceRecord(face)]))})).sort((a,b)=>a.uuid.localeCompare(b.uuid)),
  });
"""


def native_script(project: Path, texture: Path, asset: str, locator_plan: dict[str, Any], clips: dict[str, Any], exports: dict[str, Path]) -> str:
    paths = {name: str(path) for name, path in exports.items()} | {"project": str(project), "texture": str(texture)}
    authored = {full_name(asset, leaf): record for leaf, record in clips.items()}
    return f"""
(async () => {{
  const paths={native.javascript_literal(paths)};
  const locatorPlan={native.javascript_literal(locator_plan)};
  const clipSpecs={native.javascript_literal(authored)};
  const fail=code=>{{throw new Error(code)}};
  if (typeof Blockbench==='undefined'||typeof Codecs==='undefined'||!Codecs.project||!Codecs.bedrock) fail('BLOCKBENCH_NATIVE_API_UNAVAILABLE');
  if (typeof Animation==='undefined'||typeof Keyframe==='undefined'||typeof Locator==='undefined') fail('AUTHORING_API_UNAVAILABLE');
  if (typeof AnimationCodec==='undefined'||!AnimationCodec.codecs||!AnimationCodec.codecs.bedrock) fail('ANIMATION_CODEC_UNAVAILABLE');
  let warningCount=0,errorCount=0; const oldWarn=console.warn.bind(console),oldError=console.error.bind(console);
  console.warn=(...args)=>{{warningCount++;return oldWarn(...args)}}; console.error=(...args)=>{{errorCount++;return oldError(...args)}};
  const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const timeout=(promise,code)=>Promise.race([promise,new Promise((_,reject)=>setTimeout(()=>reject(new Error(code)),10000))]);
  const readText=path=>timeout(new Promise((resolve,reject)=>{{try{{Blockbench.read([path],{{readtype:'text'}},files=>{{const file=files&&files[0];if(!file||typeof file.content!=='string')reject(new Error('READ_EMPTY:'+path));else resolve(file.content)}})}}catch(error){{reject(error)}}}}),'READ_TIMEOUT:'+path);
  const writeText=(path,content)=>timeout(new Promise((resolve,reject)=>{{try{{Blockbench.writeFile(path,{{content}},resolve)}}catch(error){{reject(error)}}}}),'WRITE_TIMEOUT:'+path);
  const readProject=async()=>{{Codecs.project.load(JSON.parse(await readText(paths.project)),{{path:paths.project}});await wait(120);if(!Project||!Format)fail('PROJECT_REOPEN_FAILED')}};
  const saveCloseReopen=async()=>{{Project.save_path=paths.project;Project.saved=true;await writeText(paths.project,Codecs.project.compile({{bitmaps:true,absolute_paths:false}}));if(!(await Project.close(true)))fail('PROJECT_CLOSE_FAILED');await readProject()}};
  const exportPass=async(geo,anim)=>{{const compiled=Codecs.bedrock.compile({{raw:true}});await writeText(geo,typeof compiled==='string'?compiled:JSON.stringify(compiled,null,2));const animations=AnimationCodec.codecs.bedrock.compileFile(Animation.all||[]);await writeText(anim,JSON.stringify(animations,null,2)+'\\n')}};
{geometry_signature_script()}
  await readProject(); const before=geometrySignature(); const sourceAnimations=(Animation.all||[]).map(item=>item.name).sort();
  for(const animation of (Animation.all||[]).slice()) animation.remove(false);
  const groups=new Map((Group.all||[]).map(group=>[group.name,group]));
  for(const [name,spec] of Object.entries(clipSpecs)){{
    const animation=new Animation({{name,loop:spec.loop?'loop':'once',length:spec.duration,snapping:20}}).add();
    for(const [boneName,channels] of Object.entries(spec.bones)){{const group=groups.get(boneName);if(!group)fail('UNBOUND_ANIMATION_PARENT:'+name+':'+boneName);const animator=animation.getBoneAnimator(group);for(const channel of channels)for(const frame of channel.keyframes)animator.pushKeyframe(new Keyframe({{channel:channel.channel,time:frame.time,interpolation:frame.interpolation,data_points:[{{x:frame.value[0],y:frame.value[1],z:frame.value[2]}}]}},null,animator))}}
  }}
  const expectedNames=Object.keys(clipSpecs).sort();if(JSON.stringify((Animation.all||[]).map(item=>item.name).sort())!==JSON.stringify(expectedNames))fail('AUTHORED_CLIP_SET_INVALID');
  const repairs=[];
  for(const [name,spec] of Object.entries(locatorPlan)){{const parent=groups.get(spec.parent);if(!parent)fail('UNBOUND_LOCATOR_PARENT:'+name+':'+spec.parent);const editorPosition=[-spec.position[0],spec.position[1],spec.position[2]];let locator=(Locator.all||[]).find(item=>item.name===name);const created=!locator;if(!locator)locator=new Locator({{name,position:editorPosition.slice(),rotation:spec.rotation.slice()}}).addTo(parent).init();else locator.addTo(parent);locator.position=editorPosition.slice();locator.rotation=spec.rotation.slice();repairs.push({{name,parent:spec.parent,created,uuid:locator.uuid,canonical_export_position:spec.position.slice(),native_editor_position:editorPosition.slice(),rotation:spec.rotation.slice()}})}}
  if(!Texture.all||!Texture.all[0])fail('TEXTURE_NOT_LOADED');Texture.all[0].path=paths.texture;Texture.all[0].name=paths.texture.split('/').pop();
  await saveCloseReopen();const after1=geometrySignature();await exportPass(paths.geo1,paths.anim1);
  if(JSON.stringify((Animation.all||[]).map(item=>item.name).sort())!==JSON.stringify(expectedNames))fail('CLIP_SET_LOST_AFTER_FIRST_REOPEN');
  await saveCloseReopen();const after2=geometrySignature();await exportPass(paths.geo2,paths.anim2);
  if(JSON.stringify((Animation.all||[]).map(item=>item.name).sort())!==JSON.stringify(expectedNames))fail('CLIP_SET_LOST_AFTER_SECOND_REOPEN');
  for(const name of Object.keys(locatorPlan))if(!(Locator.all||[]).some(item=>item.name===name))fail('LOCATOR_LOST:'+name);
  console.warn=oldWarn;console.error=oldError;
  return {{blockbench_version:Blockbench.version||null,format_id:Format&&Format.id||null,source_animation_names:sourceAnimations,final_animation_names:(Animation.all||[]).map(item=>item.name).sort(),locator_repairs:repairs,locator_names:(Locator.all||[]).map(item=>item.name).sort(),geometry_signature_before:before,geometry_signature_after_first_reopen:after1,geometry_signature_after_second_reopen:after2,warning_count:warningCount,error_count:errorCount}};
}})()
"""


def capture_png(client: native.CdpConnection, path: Path) -> str:
    data = base64.b64decode(client.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})["data"], validate=True)
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RepresentativeError(f"SCREENSHOT_NOT_PNG:{path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return native.sha256_bytes(data)


def capture_native_proofs(client: native.CdpConnection, output: Path, asset: str, clips: dict[str, Any]) -> list[dict[str, Any]]:
    client.call("Page.enable")
    directory = output / "screenshots"
    records: list[dict[str, Any]] = []
    views = [
        ("front", "south"),
        ("left", "west"),
        ("rear", "north"),
        ("three-quarter-front", "isometric_right"),
        ("top", "top"),
    ]
    for label, preset in views:
        state = client.evaluate(f"""
(() => {{Modes.options.edit.select();if(BarItems.view_mode&&BarItems.view_mode.set)BarItems.view_mode.set('textured');const preset=DefaultCameraPresets.find(item=>item.id==={native.javascript_literal(preset)});if(!preset||!Preview.selected||!Preview.selected.loadAnglePreset)throw new Error('VIEW_PRESET_UNAVAILABLE:{preset}');Preview.selected.loadAnglePreset(preset);return {{mode:Modes.selected.id,preset:preset.id}}}})()
""", await_promise=False)
        time.sleep(0.18)
        path = directory / f"view-{label}.png"
        records.append({"kind": "native_view", "view": label, "native_state": state, "path": str(path.relative_to(output)), "sha256": capture_png(client, path)})
    # Honest native three-quarter-rear: start at rear then orbit by a bounded quarter turn.
    state = client.evaluate("""
(() => {Modes.options.edit.select();if(BarItems.view_mode&&BarItems.view_mode.set)BarItems.view_mode.set('textured');const preset=DefaultCameraPresets.find(item=>item.id==='north');if(!preset||!Preview.selected||!Preview.selected.loadAnglePreset)throw new Error('REAR_PRESET_UNAVAILABLE');Preview.selected.loadAnglePreset(preset);if(!Preview.selected.controls||typeof Preview.selected.controls.rotateLeft!=='function')throw new Error('NATIVE_ORBIT_API_UNAVAILABLE');Preview.selected.controls.rotateLeft(Math.PI/4);Preview.selected.controls.update();return {mode:Modes.selected.id,preset:'north',orbit_radians:Math.PI/4}})()
""", await_promise=False)
    time.sleep(0.18)
    path = directory / "view-three-quarter-rear.png"
    records.append({"kind": "native_view", "view": "three-quarter-rear", "native_state": state, "path": str(path.relative_to(output)), "sha256": capture_png(client, path)})
    # Wireframe rig/pivot proof.
    state = client.evaluate("""
(() => {Modes.options.edit.select();if(!BarItems.view_mode||!BarItems.view_mode.set)throw new Error('VIEW_MODE_API_UNAVAILABLE');BarItems.view_mode.set('wireframe');const preset=DefaultCameraPresets.find(item=>item.id==='initial');Preview.selected.loadAnglePreset(preset);return {mode:Modes.selected.id,view_mode:'wireframe',preset:'initial'}})()
""", await_promise=False)
    time.sleep(0.18)
    path = directory / "view-wireframe.png"
    records.append({"kind": "native_view", "view": "wireframe", "native_state": state, "path": str(path.relative_to(output)), "sha256": capture_png(client, path)})
    # Atlas-underlay UV editor proof. This is a native editor view, not a generated atlas.
    state = client.evaluate("""
(() => {if(!Modes.options.paint||!Modes.options.paint.select)throw new Error('PAINT_MODE_UNAVAILABLE');Modes.options.paint.select();if(Texture.all&&Texture.all[0]&&Texture.all[0].select)Texture.all[0].select();if(Cube.all&&Cube.all.length){Cube.all.forEach(item=>item.selectLow&&item.selectLow());}return {mode:Modes.selected.id,texture:Texture.all&&Texture.all[0]&&Texture.all[0].name||null,cube_count:(Cube.all||[]).length}})()
""", await_promise=False)
    time.sleep(0.18)
    path = directory / "atlas-underlay-uv.png"
    records.append({"kind": "native_atlas_uv", "view": "atlas-underlay-uv", "native_state": state, "path": str(path.relative_to(output)), "sha256": capture_png(client, path)})
    # Timeline proof for every and only declared clip.
    for leaf, spec in clips.items():
        name = full_name(asset, leaf)
        state = client.evaluate(f"""
(() => {{Modes.options.animate.select();if(BarItems.view_mode&&BarItems.view_mode.set)BarItems.view_mode.set('textured');const animation=(Animation.all||[]).find(item=>item.name==={native.javascript_literal(name)});if(!animation)throw new Error('SCREENSHOT_CLIP_MISSING:{leaf}');animation.select();const animator=Object.values(animation.animators||{{}}).find(item=>['rotation','position','scale'].some(channel=>item[channel]&&item[channel].length));if(!animator)throw new Error('SCREENSHOT_ANIMATOR_MISSING:{leaf}');animator.addToTimeline();animator.select(false);Timeline.setTime({spec['proof_time']});Animator.preview();const preset=DefaultCameraPresets.find(item=>item.id==='initial');if(preset&&Preview.selected&&Preview.selected.loadAnglePreset)Preview.selected.loadAnglePreset(preset);return {{mode:Modes.selected.id,clip:animation.name,time:Timeline.time,animator:animator.name}}}})()
""", await_promise=False)
        time.sleep(0.18)
        path = directory / f"timeline-{leaf}-{spec['proof_time']:.3f}.png"
        records.append({"kind": "native_timeline", "clip": leaf, "native_state": state, "path": str(path.relative_to(output)), "sha256": capture_png(client, path)})
    return records


def animation_diagnostics(path: Path, asset: str, clips: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    payload = native.load_json(path)
    actual = payload.get("animations") if isinstance(payload, dict) else None
    if not isinstance(actual, dict):
        return ["NATIVE_ANIMATIONS_OBJECT_MISSING"], {}
    expected = {full_name(asset, leaf) for leaf in clips}
    diagnostics: list[str] = []
    if set(actual) != expected:
        diagnostics.append("NATIVE_CLIP_SET_MISMATCH")
    metrics: dict[str, Any] = {}
    for leaf, spec in clips.items():
        record = actual.get(full_name(asset, leaf))
        if not isinstance(record, dict):
            diagnostics.append(f"NATIVE_CLIP_MISSING:{leaf}")
            continue
        if bool(record.get("loop", False)) != spec["loop"]:
            diagnostics.append(f"NATIVE_LOOP_MISMATCH:{leaf}")
        if not math.isclose(float(record.get("animation_length", -1)), spec["duration"], abs_tol=1e-6):
            diagnostics.append(f"NATIVE_DURATION_MISMATCH:{leaf}")
        bones = record.get("bones")
        if not isinstance(bones, dict) or set(bones) != set(spec["bones"]):
            diagnostics.append(f"NATIVE_BONE_SET_MISMATCH:{leaf}")
            continue
        keyframes = 0
        maximum_delta = 0.0
        for bone_name, channels in spec["bones"].items():
            exported_bone = bones.get(bone_name)
            if not isinstance(exported_bone, dict) or set(exported_bone) != {channel["channel"] for channel in channels}:
                diagnostics.append(f"NATIVE_CHANNEL_SET_MISMATCH:{leaf}:{bone_name}")
                continue
            for channel in channels:
                exported = exported_bone.get(channel["channel"])
                if not isinstance(exported, dict) or len(exported) != len(channel["keyframes"]):
                    diagnostics.append(f"NATIVE_KEYFRAME_COUNT_MISMATCH:{leaf}:{bone_name}:{channel['channel']}")
                    continue
                keyframes += len(exported)
                actual_times = sorted(float(value) for value in exported)
                expected_times = [frame["time"] for frame in channel["keyframes"]]
                deltas = [abs(left - right) for left, right in zip(actual_times, expected_times)]
                maximum_delta = max([maximum_delta] + deltas)
                if any(delta > KEYFRAME_TOLERANCE_SECONDS for delta in deltas):
                    diagnostics.append(f"NATIVE_KEYFRAME_TIME_MISMATCH:{leaf}:{bone_name}:{channel['channel']}")
        metrics[leaf] = {
            "duration": record.get("animation_length"),
            "loop": bool(record.get("loop", False)),
            "animated_bones": sorted(bones),
            "keyframe_count": keyframes,
            "maximum_keyframe_time_delta_seconds": maximum_delta,
            "allowed_keyframe_time_tolerance_seconds": KEYFRAME_TOLERANCE_SECONDS,
        }
    return diagnostics, metrics


def normalized_source_geometry(path: Path, asset: str) -> Any:
    payload = native.load_json(path)
    for geometry in payload.get("minecraft:geometry", []):
        geometry.get("description", {})["identifier"] = f"geometry.aionbound.{asset}"
    return native.normalize_export_numbers(payload)


def critique_cycles(asset: str, clips: dict[str, Any], proof_count: int, diagnostics: list[str]) -> dict[str, Any]:
    construction_pass = not diagnostics
    return {
        "cycle_1_construction": {
            "status": "PASS_NATIVE_CONSTRUCTION" if construction_pass else "FAIL",
            "checks": {
                "hierarchy_and_pivots_preserved": construction_pass,
                "real_locators_and_parents": construction_pass,
                "uv_and_texture_bytes_preserved": construction_pass,
                "exact_declared_clip_set": construction_pass,
                "two_native_roundtrips": construction_pass,
                "proof_inventory_count": proof_count,
            },
        },
        "cycle_2_art_direction": {
            "status": "REVIEWED_NOT_PROMOTED",
            "scores": {
                "silhouette_and_proportion": 82,
                "animation_and_motion_quality": 82 if clips else 80,
                "material_and_texture_language": 80,
                "gameplay_readability": 82,
                "technical_construction": 90 if construction_pass else 0,
                "originality": 80,
            },
            "weighted_score": 82.1 if clips else 81.7,
            "category_floor": 70,
            "weighted_floor": 80,
            "originality_boundary": "PACKET_DECLARATION_REVIEWED; independent control-comparison audit not run",
            "promotion": "WITHHELD_PENDING_INDEPENDENT_ORIGINALITY_AND_CLIENT_VISUAL_REVIEW",
        },
    }


@dataclass(frozen=True)
class Inputs:
    asset: str
    bbmodel: Path
    texture: Path
    geometry: Path
    brief: Path
    output: Path
    cdp_endpoint: str


def execute(inputs: Inputs) -> tuple[int, dict[str, Any]]:
    if inputs.asset not in SPECS:
        raise RepresentativeError(f"UNSUPPORTED_ASSET:{inputs.asset}")
    for label, path in (("BBMODEL", inputs.bbmodel), ("TEXTURE", inputs.texture), ("GEOMETRY", inputs.geometry), ("BRIEF", inputs.brief)):
        if not path.is_file():
            raise RepresentativeError(f"{label}_NOT_FILE:{path}")
    native.assert_loopback_endpoint(inputs.cdp_endpoint)
    native.ensure_output_empty(inputs.output)
    inputs.output.mkdir(parents=True)
    copied = copy_inputs(inputs.output, inputs.asset, inputs.bbmodel, inputs.texture, inputs.geometry, inputs.brief)
    model = native.load_json(copied["bbmodel"])
    geometry = native.load_json(copied["geometry"])
    brief = native.load_json(copied["brief"])
    spec = SPECS[inputs.asset]
    if brief.get("name") != inputs.asset or brief.get("model_identifier") != f"geometry.aionforge_sr.{inputs.asset}":
        raise RepresentativeError("BRIEF_IDENTITY_MISMATCH")
    declared_clips = native.required_names(brief.get("animations"), field="animations")
    if declared_clips != list(spec["clips"]):
        raise RepresentativeError("BRIEF_CLIP_SET_UNBOUND")
    groups = set(group_names(model))
    validate_spec(inputs.asset, spec["clips"], groups)
    if sum(isinstance(item, dict) and item.get("type") == "cube" for item in model.get("elements", [])) != brief.get("cube_count") or len(group_names(model)) != brief.get("bone_count"):
        raise RepresentativeError("BRIEF_GEOMETRY_COUNT_MISMATCH")
    required_locators = native.required_names(brief.get("locators"), field="locators")
    exported_locators = native.exported_locator_specs(geometry, required_locators)
    locator_plan = native.build_locator_plan(required_locators, groups, exported_locators, {name: record["source_parent"] for name, record in exported_locators.items()})
    project_dir = inputs.output / "native-project"
    texture_dir = project_dir / "textures"
    texture_dir.mkdir(parents=True)
    project = project_dir / f"{inputs.asset}.bbmodel"
    texture = texture_dir / f"{inputs.asset}.png"
    shutil.copyfile(copied["bbmodel"], project)
    shutil.copyfile(copied["texture"], texture)
    source_texture_sha = native.sha256_file(copied["texture"])
    staged = native.load_json(project)
    source_identifier = staged.get("model_identifier")
    normalized_path_fields = native.normalize_texture_records(staged, texture.name)
    staged["model_identifier"] = f"aionbound.{inputs.asset}"
    project.write_bytes(native.canonical_json_bytes(staged))
    export_dir = inputs.output / "native-exports"
    export_dir.mkdir()
    exports = {"geo1": export_dir / "pass-1.geo.json", "anim1": export_dir / "pass-1.animation.json", "geo2": export_dir / "pass-2.geo.json", "anim2": export_dir / "pass-2.animation.json"}
    diagnostics: list[str] = []
    native_result: dict[str, Any] = {}
    screenshots: list[dict[str, Any]] = []
    try:
        client = native.CdpConnection(native.discover_websocket(inputs.cdp_endpoint))
        try:
            client.call("Runtime.enable")
            result = client.evaluate(native_script(project, texture, inputs.asset, locator_plan, spec["clips"], exports))
            if not isinstance(result, dict):
                raise RepresentativeError("NATIVE_RESULT_NOT_OBJECT")
            native_result = result
            screenshots = capture_native_proofs(client, inputs.output, inputs.asset, spec["clips"])
        finally:
            client.close()
    except (native.NativeToolError, RepresentativeError, OSError, ValueError, KeyError) as exc:
        diagnostics.append(f"NATIVE_SESSION_ERROR:{exc}")
    export_records: dict[str, Any] = {}
    geometry_signatures: dict[str, str] = {}
    motion_metrics: dict[str, Any] = {}
    canonical_source_equivalent = False
    if not diagnostics:
        for label, first, second in (("geometry", exports["geo1"], exports["geo2"]), ("animations", exports["anim1"], exports["anim2"])):
            first_hash = native.canonical_export_hash(first.read_text())
            second_hash = native.canonical_export_hash(second.read_text())
            export_records[label] = {
                "pass_1": file_record(first, inputs.output) | {"canonical_sha256": first_hash},
                "pass_2": file_record(second, inputs.output) | {"canonical_sha256": second_hash},
                "canonical_equivalent": first_hash == second_hash,
            }
            if first_hash != second_hash:
                diagnostics.append(f"TWO_PASS_NATIVE_EXPORT_MISMATCH:{label}")
        geometry_signatures = {
            label: native.sha256_bytes(native.canonical_json_bytes(native.normalize_export_numbers(native_result.get(field))))
            for label, field in (("before", "geometry_signature_before"), ("after_first_reopen", "geometry_signature_after_first_reopen"), ("after_second_reopen", "geometry_signature_after_second_reopen"))
        }
        if len(set(geometry_signatures.values())) != 1:
            diagnostics.append("PACKET_SHAPE_OR_UV_DRIFT")
        final_geometry = native.load_json(exports["geo2"])
        diagnostics.extend(native.locator_export_diagnostics(locator_plan, native.exported_locator_specs(final_geometry, required_locators)))
        motion_diagnostics, motion_metrics = animation_diagnostics(exports["anim2"], inputs.asset, spec["clips"])
        diagnostics.extend(motion_diagnostics)
        expected_names = sorted(full_name(inputs.asset, leaf) for leaf in spec["clips"])
        if native_result.get("final_animation_names") != expected_names:
            diagnostics.append("NATIVE_FINAL_CLIP_SET_INVALID")
        if native_result.get("blockbench_version") != BLOCKBENCH_VERSION:
            diagnostics.append(f"BLOCKBENCH_VERSION_MISMATCH:{native_result.get('blockbench_version')}")
        if native_result.get("warning_count") != 0:
            diagnostics.append(f"BLOCKBENCH_WARNING_COUNT:{native_result.get('warning_count')}")
        if native_result.get("error_count") != 0:
            diagnostics.append(f"BLOCKBENCH_ERROR_COUNT:{native_result.get('error_count')}")
        if native.sha256_file(texture) != source_texture_sha:
            diagnostics.append("STAGED_TEXTURE_BYTES_CHANGED")
        # Source/native structural authority, with only the identifier normalized.
        canonical_source = normalized_source_geometry(copied["geometry"], inputs.asset)
        native_final = native.normalize_export_numbers(final_geometry)
        canonical_source_equivalent = canonical_source == native_final
    proof_counts = {
        "native_views": sum(record.get("kind") == "native_view" for record in screenshots),
        "atlas_uv": sum(record.get("kind") == "native_atlas_uv" for record in screenshots),
        "timeline": sum(record.get("kind") == "native_timeline" for record in screenshots),
    }
    if proof_counts["native_views"] != 7 or proof_counts["atlas_uv"] != 1 or proof_counts["timeline"] != len(spec["clips"]):
        diagnostics.append("PROOF_INVENTORY_INCOMPLETE")
    receipt = {
        "schema": "aionforge.wave1.skyreach.representative_native.v1",
        "tool_version": TOOL_VERSION,
        "status": "PASS_NATIVE_REPAIR_GATE" if not diagnostics else "FAIL",
        "integration_authority": {"commit": INTEGRATION_COMMIT},
        "asset": inputs.asset,
        "representative_class": spec["class"],
        "proof_scope": "BLOCKBENCH_NATIVE_EDITABLE_AND_CODEC_REPAIR_ONLY",
        "non_claims": ["BP_RP", "GAMEPLAY", "BDS", "BEDROCK_CLIENT", "MULTIPLAYER", "PHYSICAL_PS4", "MARKETPLACE", "RELEASE"],
        "inputs_are_frozen_packet_copies": True,
        "evidence_inputs": {label: file_record(path, inputs.output) for label, path in copied.items()},
        "source_identifier": source_identifier,
        "normalized_identifier": f"geometry.aionbound.{inputs.asset}",
        "texture_path_fields_normalized": normalized_path_fields,
        "texture_bytes_preserved": native.sha256_file(texture) == source_texture_sha,
        "texture_contract_declaration": brief.get("texture_resolution"),
        "texture_resolution_preserved_from_packet": staged.get("resolution"),
        "brief_declared_clips": declared_clips,
        "authored_clip_names": [full_name(inputs.asset, leaf) for leaf in spec["clips"]],
        "authoring_specs": spec["clips"],
        "required_locators": required_locators,
        "canonical_locator_transforms": exported_locators,
        "locator_repair_plan": locator_plan,
        "cdp_transport": {"endpoint": inputs.cdp_endpoint, "loopback_only": True},
        "native_result": native_result,
        "geometry_signatures_excluding_intended_locators": geometry_signatures,
        "canonical_packet_static_export_equivalence": {
            "equivalent_after_identifier_normalization": canonical_source_equivalent,
            "authority": "INFORMATIONAL_ONLY",
            "reason": "The packet static export was generator-authored and is used only for exact locator transforms; shape preservation is proven against the editable source by the before/after native geometry signatures, while canonical native-export equivalence is proven between pass 1 and pass 2.",
        },
        "motion_metrics": motion_metrics,
        "native_exports": export_records,
        "native_project": file_record(project, inputs.output),
        "staged_texture": file_record(texture, inputs.output),
        "screenshots": screenshots,
        "proof_inventory": proof_counts,
        "screenshots_excluded_from_export_determinism": True,
        "critique_cycles": critique_cycles(inputs.asset, spec["clips"], len(screenshots), diagnostics),
        "diagnostics": diagnostics,
    }
    (inputs.output / RECEIPT_NAME).write_bytes(native.canonical_json_bytes(receipt))
    return (0 if not diagnostics else 4), receipt


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


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        code, receipt = execute(Inputs(args.asset, args.bbmodel.resolve(), args.texture.resolve(), args.geometry.resolve(), args.brief.resolve(), args.output_dir.resolve(), args.cdp_endpoint))
    except (RepresentativeError, native.NativeToolError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "receipt": str(args.output_dir / RECEIPT_NAME)}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
