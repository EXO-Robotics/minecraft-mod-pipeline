#!/usr/bin/env python3
"""Author five Packet 001 creature clip sets through native Blockbench codecs.

Inputs must be caller-supplied copies. The tool does not edit BP/RP runtime
files and its evidence does not establish Bedrock client playback.
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


WHISPERWOOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WHISPERWOOD_DIR))
import repair_whisperwood_native as native  # noqa: E402


TOOL_VERSION = "1.0.1"
KEYFRAME_TIME_TOLERANCE_SECONDS = 0.026
RECEIPT_NAME = "entity-animation-native-receipt.json"
PROOF_SCOPE = "BLOCKBENCH_NATIVE_ENTITY_ANIMATION_AUTHORING_AND_CODEC_EXPORT_ONLY"
NON_CLAIMS = ["BEDROCK_CLIENT", "STABLE_BDS", "PHYSICAL_PS4", "MARKETPLACE"]


def frames(channel: str, *entries: tuple[float, list[float]]) -> dict[str, Any]:
    return {
        "channel": channel,
        "keyframes": [
            {"time": point, "interpolation": "linear", "value": value}
            for point, value in entries
        ],
    }


def clip(duration: float, loop: bool, proof_time: float, bones: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {"duration": duration, "loop": loop, "proof_time": proof_time, "bones": bones}


ZERO = [0.0, 0.0, 0.0]


ENTITY_SPECS: dict[str, dict[str, Any]] = {
    "lantern_hare": {
        "role": "ambient_curiosity",
        "clips": {
            "idle_ear_flick": clip(3.2, True, 0.8, {
                "ear_l": [frames("rotation", (0.0, ZERO), (0.7, [0.0, 0.0, 8.0]), (1.0, [0.0, 0.0, -3.0]), (1.3, ZERO), (3.2, ZERO))],
                "ear_r": [frames("rotation", (0.0, ZERO), (1.8, ZERO), (2.1, [0.0, 0.0, -7.0]), (2.4, [0.0, 0.0, 2.0]), (2.7, ZERO), (3.2, ZERO))],
            }),
            "hop": clip(0.8, True, 0.4, {
                "body": [frames("position", (0.0, ZERO), (0.2, [0.0, 0.7, 0.0]), (0.4, [0.0, 1.3, 0.0]), (0.6, [0.0, 0.55, 0.0]), (0.8, ZERO))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.4, [-24.0, 0.0, 0.0]), (0.8, ZERO))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (0.4, [-24.0, 0.0, 0.0]), (0.8, ZERO))],
                "leg_bl": [frames("rotation", (0.0, ZERO), (0.4, [28.0, 0.0, 0.0]), (0.8, ZERO))],
                "leg_br": [frames("rotation", (0.0, ZERO), (0.4, [28.0, 0.0, 0.0]), (0.8, ZERO))],
            }),
            "alert": clip(0.45, False, 0.45, {
                "head": [frames("rotation", (0.0, ZERO), (0.2, [-10.0, 0.0, 0.0]), (0.45, [-14.0, 0.0, 0.0]))],
                "ear_l": [frames("rotation", (0.0, ZERO), (0.45, [0.0, 0.0, 7.0]))],
                "ear_r": [frames("rotation", (0.0, ZERO), (0.45, [0.0, 0.0, -7.0]))],
            }),
            "hurt": clip(0.4, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.16, [0.0, 0.0, 9.0]), (0.4, ZERO))]}),
            "death": clip(0.8, False, 0.8, {"body": [frames("rotation", (0.0, ZERO), (0.8, [0.0, 0.0, 82.0]))]}),
        },
    },
    "mosskip_fawn": {
        "role": "ambient_young",
        "clips": {
            "idle": clip(3.0, True, 0.75, {
                "head": [frames("rotation", (0.0, ZERO), (0.75, [4.0, -6.0, 0.0]), (1.5, ZERO), (2.25, [3.0, 5.0, 0.0]), (3.0, ZERO))],
                "tail": [frames("rotation", (0.0, ZERO), (0.75, [0.0, 0.0, 8.0]), (1.5, ZERO), (2.25, [0.0, 0.0, -7.0]), (3.0, ZERO))],
            }),
            "hop": clip(0.9, True, 0.45, {
                "body": [frames("position", (0.0, ZERO), (0.22, [0.0, 0.7, 0.0]), (0.45, [0.0, 1.5, 0.0]), (0.68, [0.0, 0.55, 0.0]), (0.9, ZERO))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.45, [-23.0, 0.0, 0.0]), (0.9, ZERO))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (0.45, [-23.0, 0.0, 0.0]), (0.9, ZERO))],
                "leg_bl": [frames("rotation", (0.0, ZERO), (0.45, [25.0, 0.0, 0.0]), (0.9, ZERO))],
                "leg_br": [frames("rotation", (0.0, ZERO), (0.45, [25.0, 0.0, 0.0]), (0.9, ZERO))],
            }),
            "skitter": clip(0.65, True, 0.16, {
                "leg_fl": [frames("rotation", (0.0, [18.0, 0.0, 0.0]), (0.325, [-18.0, 0.0, 0.0]), (0.65, [18.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.325, [18.0, 0.0, 0.0]), (0.65, [-18.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-16.0, 0.0, 0.0]), (0.325, [16.0, 0.0, 0.0]), (0.65, [-16.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [16.0, 0.0, 0.0]), (0.325, [-16.0, 0.0, 0.0]), (0.65, [16.0, 0.0, 0.0]))],
            }),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, -8.0]), (0.45, ZERO))]}),
            "death": clip(0.9, False, 0.9, {"body": [frames("rotation", (0.0, ZERO), (0.9, [0.0, 0.0, -84.0]))]}),
        },
    },
    "mosskip_doe": {
        "role": "ambient_adult",
        "clips": {
            "idle_graze": clip(4.0, True, 1.0, {"head": [frames("rotation", (0.0, ZERO), (1.0, [24.0, 0.0, 0.0]), (2.2, [30.0, 0.0, 0.0]), (3.2, [12.0, 0.0, 0.0]), (4.0, ZERO))]}),
            "walk": clip(1.0, True, 0.25, {
                "leg_fl": [frames("rotation", (0.0, [20.0, 0.0, 0.0]), (0.5, [-20.0, 0.0, 0.0]), (1.0, [20.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-20.0, 0.0, 0.0]), (0.5, [20.0, 0.0, 0.0]), (1.0, [-20.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.5, [18.0, 0.0, 0.0]), (1.0, [-18.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [18.0, 0.0, 0.0]), (0.5, [-18.0, 0.0, 0.0]), (1.0, [18.0, 0.0, 0.0]))],
            }),
            "hop_bound": clip(1.0, True, 0.5, {
                "body": [frames("position", (0.0, ZERO), (0.25, [0.0, 0.8, 0.0]), (0.5, [0.0, 1.7, 0.0]), (0.75, [0.0, 0.65, 0.0]), (1.0, ZERO))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.5, [-26.0, 0.0, 0.0]), (1.0, ZERO))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (0.5, [-26.0, 0.0, 0.0]), (1.0, ZERO))],
                "leg_bl": [frames("rotation", (0.0, ZERO), (0.5, [28.0, 0.0, 0.0]), (1.0, ZERO))],
                "leg_br": [frames("rotation", (0.0, ZERO), (0.5, [28.0, 0.0, 0.0]), (1.0, ZERO))],
            }),
            "look": clip(1.2, False, 0.8, {"head": [frames("rotation", (0.0, ZERO), (0.4, [0.0, -14.0, 0.0]), (0.8, [0.0, 14.0, 0.0]), (1.2, ZERO))]}),
            "hurt": clip(0.45, False, 0.18, {"body": [frames("rotation", (0.0, ZERO), (0.18, [0.0, 0.0, 8.0]), (0.45, ZERO))]}),
            "death": clip(1.0, False, 1.0, {"body": [frames("rotation", (0.0, ZERO), (1.0, [0.0, 0.0, 86.0]))]}),
        },
    },
    "mosskip_buck": {
        "role": "neutral_territorial",
        "clips": {
            "idle_graze": clip(4.2, True, 1.05, {"head": [frames("rotation", (0.0, ZERO), (1.05, [20.0, 0.0, 0.0]), (2.3, [26.0, 0.0, 0.0]), (3.25, [10.0, 0.0, 0.0]), (4.2, ZERO))]}),
            "walk": clip(1.1, True, 0.275, {
                "leg_fl": [frames("rotation", (0.0, [18.0, 0.0, 0.0]), (0.55, [-18.0, 0.0, 0.0]), (1.1, [18.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-18.0, 0.0, 0.0]), (0.55, [18.0, 0.0, 0.0]), (1.1, [-18.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-17.0, 0.0, 0.0]), (0.55, [17.0, 0.0, 0.0]), (1.1, [-17.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [17.0, 0.0, 0.0]), (0.55, [-17.0, 0.0, 0.0]), (1.1, [17.0, 0.0, 0.0]))],
            }),
            "hop_bound": clip(1.1, True, 0.55, {
                "body": [frames("position", (0.0, ZERO), (0.275, [0.0, 0.7, 0.0]), (0.55, [0.0, 1.5, 0.0]), (0.825, [0.0, 0.55, 0.0]), (1.1, ZERO))],
                "leg_fl": [frames("rotation", (0.0, ZERO), (0.55, [-24.0, 0.0, 0.0]), (1.1, ZERO))],
                "leg_fr": [frames("rotation", (0.0, ZERO), (0.55, [-24.0, 0.0, 0.0]), (1.1, ZERO))],
                "leg_bl": [frames("rotation", (0.0, ZERO), (0.55, [26.0, 0.0, 0.0]), (1.1, ZERO))],
                "leg_br": [frames("rotation", (0.0, ZERO), (0.55, [26.0, 0.0, 0.0]), (1.1, ZERO))],
            }),
            "look": clip(1.3, False, 0.85, {"head": [frames("rotation", (0.0, ZERO), (0.45, [-5.0, -12.0, 0.0]), (0.85, [-5.0, 12.0, 0.0]), (1.3, ZERO))]}),
            "hurt": clip(0.5, False, 0.2, {"body": [frames("rotation", (0.0, ZERO), (0.2, [0.0, 0.0, -7.0]), (0.5, ZERO))]}),
            "death": clip(1.1, False, 1.1, {"body": [frames("rotation", (0.0, ZERO), (1.1, [0.0, 0.0, -86.0]))]}),
        },
    },
    "rootback_boar": {
        "role": "neutral_provoked",
        "clips": {
            "idle": clip(3.4, True, 0.85, {
                "head": [frames("rotation", (0.0, ZERO), (0.85, [5.0, -5.0, 0.0]), (1.7, ZERO), (2.55, [4.0, 5.0, 0.0]), (3.4, ZERO))],
                "body": [frames("position", (0.0, ZERO), (0.85, [0.0, 0.12, 0.0]), (1.7, ZERO), (2.55, [0.0, 0.1, 0.0]), (3.4, ZERO))],
            }),
            "walk_trundle": clip(1.2, True, 0.3, {
                "leg_fl": [frames("rotation", (0.0, [16.0, 0.0, 0.0]), (0.6, [-16.0, 0.0, 0.0]), (1.2, [16.0, 0.0, 0.0]))],
                "leg_fr": [frames("rotation", (0.0, [-16.0, 0.0, 0.0]), (0.6, [16.0, 0.0, 0.0]), (1.2, [-16.0, 0.0, 0.0]))],
                "leg_bl": [frames("rotation", (0.0, [-14.0, 0.0, 0.0]), (0.6, [14.0, 0.0, 0.0]), (1.2, [-14.0, 0.0, 0.0]))],
                "leg_br": [frames("rotation", (0.0, [14.0, 0.0, 0.0]), (0.6, [-14.0, 0.0, 0.0]), (1.2, [14.0, 0.0, 0.0]))],
            }),
            "charge_snort": clip(0.75, False, 0.75, {
                "head": [frames("rotation", (0.0, ZERO), (0.25, [10.0, 0.0, 0.0]), (0.5, [16.0, 0.0, 0.0]), (0.75, [12.0, 0.0, 0.0]))],
                "body": [frames("position", (0.0, ZERO), (0.25, [0.0, -0.15, 0.0]), (0.75, [0.0, -0.25, -0.35]))],
            }),
            "hurt": clip(0.5, False, 0.2, {"body": [frames("rotation", (0.0, ZERO), (0.2, [0.0, 0.0, 7.0]), (0.5, ZERO))]}),
            "death": clip(1.1, False, 1.1, {"body": [frames("rotation", (0.0, ZERO), (1.1, [0.0, 0.0, 88.0]))]}),
        },
    },
}


class EntityAnimationError(RuntimeError):
    pass


def full_clip_name(model_identifier: str, leaf: str) -> str:
    return f"animation.{model_identifier.removeprefix('geometry.')}.{leaf}"


def source_preview_names(model_identifier: str) -> list[str]:
    prefix = model_identifier.removeprefix("geometry.")
    return sorted([f"animation.{prefix}.idle", f"animation.{prefix}.action"])


def group_names(model: dict[str, Any]) -> list[str]:
    return native.extract_group_names(model)


def validate_spec(asset: str, spec: dict[str, Any]) -> None:
    clips = spec.get("clips")
    if not isinstance(clips, dict) or not clips:
        raise EntityAnimationError(f"SPEC_CLIPS_INVALID:{asset}")
    for clip_name, record in clips.items():
        duration = record.get("duration")
        if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
            raise EntityAnimationError(f"SPEC_DURATION_INVALID:{asset}:{clip_name}")
        if not 0 <= record.get("proof_time", -1) <= duration:
            raise EntityAnimationError(f"SPEC_PROOF_TIME_INVALID:{asset}:{clip_name}")
        bones = record.get("bones")
        if not isinstance(bones, dict) or not bones:
            raise EntityAnimationError(f"SPEC_BONES_INVALID:{asset}:{clip_name}")
        for bone, channels in bones.items():
            if not isinstance(channels, list) or not channels:
                raise EntityAnimationError(f"SPEC_CHANNELS_INVALID:{asset}:{clip_name}:{bone}")
            channel_names: set[str] = set()
            for channel in channels:
                name = channel.get("channel")
                if name not in {"rotation", "position", "scale"} or name in channel_names:
                    raise EntityAnimationError(f"SPEC_CHANNEL_INVALID:{asset}:{clip_name}:{bone}")
                channel_names.add(name)
                keyframes = channel.get("keyframes")
                if not isinstance(keyframes, list) or len(keyframes) < 2:
                    raise EntityAnimationError(f"SPEC_KEYFRAMES_INVALID:{asset}:{clip_name}:{bone}:{name}")
                times = [frame.get("time") for frame in keyframes]
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in times):
                    raise EntityAnimationError(f"SPEC_TIME_INVALID:{asset}:{clip_name}:{bone}:{name}")
                if times != sorted(times) or times[0] != 0 or not math.isclose(times[-1], duration, abs_tol=1e-9):
                    raise EntityAnimationError(f"SPEC_TIME_RANGE_INVALID:{asset}:{clip_name}:{bone}:{name}")
                values = [frame.get("value") for frame in keyframes]
                if any(not isinstance(v, list) or len(v) != 3 or any(isinstance(c, bool) or not isinstance(c, (int, float)) or not math.isfinite(c) for c in v) for v in values):
                    raise EntityAnimationError(f"SPEC_VALUE_INVALID:{asset}:{clip_name}:{bone}:{name}")
                if record["loop"] and values[0] != values[-1]:
                    raise EntityAnimationError(f"SPEC_LOOP_SEAM_INVALID:{asset}:{clip_name}:{bone}:{name}")
                if all(value == values[0] for value in values[1:]):
                    raise EntityAnimationError(f"SPEC_NO_MOTION:{asset}:{clip_name}:{bone}:{name}")


def geometry_signature_script() -> str:
    return """
  const vector = value => Array.isArray(value) ? value.slice() : null;
  const parentName = element => element.parent && element.parent !== 'root' ? element.parent.name : null;
  const geometrySignature = () => ({
    groups: (Group.all || []).map(group => ({uuid: group.uuid, name: group.name, parent: parentName(group), origin: vector(group.origin), rotation: vector(group.rotation)})).sort((a,b) => a.uuid.localeCompare(b.uuid)),
    cubes: (Cube.all || []).map(cube => ({uuid: cube.uuid, name: cube.name, parent: parentName(cube), from: vector(cube.from), to: vector(cube.to), origin: vector(cube.origin), rotation: vector(cube.rotation), inflate: cube.inflate || 0, mirror_uv: !!cube.mirror_uv})).sort((a,b) => a.uuid.localeCompare(b.uuid)),
  });
"""


def native_authoring_script(project: Path, texture: Path, locator_plan: dict[str, Any], clip_specs: dict[str, Any], model_identifier: str, exports: dict[str, Path]) -> str:
    paths = {name: str(path) for name, path in exports.items()} | {"project": str(project), "texture": str(texture)}
    full_specs = {full_clip_name(model_identifier, leaf): value for leaf, value in clip_specs.items()}
    return f"""
(async () => {{
  const paths = {native.javascript_literal(paths)};
  const locatorPlan = {native.javascript_literal(locator_plan)};
  const clipSpecs = {native.javascript_literal(full_specs)};
  const fail = code => {{ throw new Error(code); }};
  if (typeof Blockbench === 'undefined' || typeof Codecs === 'undefined') fail('BLOCKBENCH_API_UNAVAILABLE');
  if (!Codecs.project || !Codecs.bedrock) fail('REQUIRED_NATIVE_CODEC_UNAVAILABLE');
  if (typeof Animation === 'undefined' || typeof Keyframe === 'undefined') fail('NATIVE_ANIMATION_API_UNAVAILABLE');
  if (typeof AnimationCodec === 'undefined' || !AnimationCodec.codecs || !AnimationCodec.codecs.bedrock) fail('BEDROCK_ANIMATION_CODEC_UNAVAILABLE');
  let warningCount = 0, errorCount = 0;
  const oldWarn = console.warn.bind(console), oldError = console.error.bind(console);
  console.warn = (...args) => {{ warningCount += 1; return oldWarn(...args); }};
  console.error = (...args) => {{ errorCount += 1; return oldError(...args); }};
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const timeout = (promise, code) => Promise.race([promise, new Promise((_, reject) => setTimeout(() => reject(new Error(code)), 10000))]);
  const readText = path => timeout(new Promise((resolve, reject) => {{ try {{ Blockbench.read([path], {{readtype:'text'}}, files => {{ const file=files&&files[0]; if (!file || typeof file.content !== 'string') reject(new Error('READ_EMPTY:'+path)); else resolve(file.content); }}); }} catch(error) {{ reject(error); }} }}), 'READ_TIMEOUT:'+path);
  const writeText = (path, content) => timeout(new Promise((resolve, reject) => {{ try {{ Blockbench.writeFile(path, {{content}}, resolve); }} catch(error) {{ reject(error); }} }}), 'WRITE_TIMEOUT:'+path);
  const readProject = async () => {{ Codecs.project.load(JSON.parse(await readText(paths.project)), {{path:paths.project}}); await wait(100); if (!Project || !Format) fail('PROJECT_REOPEN_FAILED'); }};
  const saveReopen = async () => {{ Project.save_path=paths.project; await writeText(paths.project, Codecs.project.compile({{bitmaps:true, absolute_paths:false}})); if (!(await Project.close(true))) fail('PROJECT_CLOSE_FAILED'); await readProject(); }};
  const exportPass = async (geo, anim) => {{ const geometry=Codecs.bedrock.compile({{raw:true}}); await writeText(geo, typeof geometry==='string'?geometry:JSON.stringify(geometry,null,2)); const animations=AnimationCodec.codecs.bedrock.compileFile(Animation.all||[]); await writeText(anim, JSON.stringify(animations,null,2)+'\\n'); }};
{geometry_signature_script()}
  await readProject();
  const before = geometrySignature();
  const sourceAnimations=(Animation.all||[]).map(item=>item.name).sort();
  for (const animation of (Animation.all||[]).slice()) animation.remove(false);
  const groups=new Map((Group.all||[]).map(group=>[group.name,group]));
  for (const [name, spec] of Object.entries(clipSpecs)) {{
    const animation=new Animation({{name, loop:spec.loop?'loop':'once', length:spec.duration, snapping:20}}).add();
    for (const [boneName, channels] of Object.entries(spec.bones)) {{
      const group=groups.get(boneName); if (!group) fail('AUTHORING_BONE_MISSING:'+boneName);
      const animator=animation.getBoneAnimator(group);
      for (const channel of channels) for (const frame of channel.keyframes) animator.pushKeyframe(new Keyframe({{channel:channel.channel,time:frame.time,interpolation:frame.interpolation,data_points:[{{x:frame.value[0],y:frame.value[1],z:frame.value[2]}}]}},null,animator));
    }}
  }}
  const expectedNames=Object.keys(clipSpecs).sort();
  if (JSON.stringify((Animation.all||[]).map(item=>item.name).sort()) !== JSON.stringify(expectedNames)) fail('AUTHORED_CLIP_SET_INVALID');
  const locatorRepairs=[];
  for (const [name, spec] of Object.entries(locatorPlan)) {{ const parent=groups.get(spec.parent); if (!parent) fail('LOCATOR_PARENT_MISSING:'+name); const editorPosition=[-spec.position[0],spec.position[1],spec.position[2]]; let locator=(Locator.all||[]).find(item=>item.name===name); const created=!locator; if (!locator) locator=new Locator({{name,position:editorPosition.slice(),rotation:spec.rotation.slice()}}).addTo(parent).init(); else locator.addTo(parent); locator.position=editorPosition.slice(); locator.rotation=spec.rotation.slice(); locatorRepairs.push({{name,parent:spec.parent,created,uuid:locator.uuid,canonical_export_position:spec.position.slice(),native_editor_position:editorPosition}}); }}
  if (Texture.all && Texture.all[0]) {{ Texture.all[0].path=paths.texture; Texture.all[0].name=paths.texture.split('/').pop(); }}
  await saveReopen(); const after1=geometrySignature(); await exportPass(paths.geo1,paths.anim1);
  if (JSON.stringify((Animation.all||[]).map(item=>item.name).sort()) !== JSON.stringify(expectedNames)) fail('CLIP_SET_LOST_AFTER_FIRST_REOPEN');
  await saveReopen(); const after2=geometrySignature(); await exportPass(paths.geo2,paths.anim2);
  if (JSON.stringify((Animation.all||[]).map(item=>item.name).sort()) !== JSON.stringify(expectedNames)) fail('CLIP_SET_LOST_AFTER_SECOND_REOPEN');
  for (const name of Object.keys(locatorPlan)) if (!(Locator.all||[]).some(item=>item.name===name)) fail('LOCATOR_LOST:'+name);
  console.warn=oldWarn; console.error=oldError;
  return {{blockbench_version:Blockbench.version||null,format_id:Format&&Format.id||null,source_animation_names:sourceAnimations,final_animation_names:(Animation.all||[]).map(item=>item.name).sort(),locator_repairs:locatorRepairs,locator_names:(Locator.all||[]).map(item=>item.name).sort(),geometry_signature_before:before,geometry_signature_after_first_reopen:after1,geometry_signature_after_second_reopen:after2,warning_count:warningCount,error_count:errorCount}};
}})()
"""


def capture_timeline(client: native.CdpConnection, output: Path, model_identifier: str, specs: dict[str, Any]) -> list[dict[str, Any]]:
    directory = output / "screenshots"
    directory.mkdir(parents=True, exist_ok=True)
    client.call("Page.enable")
    records = []
    for leaf, spec in specs.items():
        full_name = full_clip_name(model_identifier, leaf)
        state = client.evaluate(f"""
(() => {{
  Modes.options.animate.select();
  const animation=(Animation.all||[]).find(item=>item.name==={native.javascript_literal(full_name)}); if (!animation) throw new Error('SCREENSHOT_CLIP_MISSING');
  animation.select();
  const animator=Object.values(animation.animators||{{}}).find(item=>['rotation','position','scale'].some(channel=>item[channel]&&item[channel].length)); if (!animator) throw new Error('SCREENSHOT_ANIMATOR_MISSING');
  animator.addToTimeline(); animator.select(false); Timeline.setTime({spec['proof_time']}); Animator.preview();
  const preset=DefaultCameraPresets.find(item=>item.id==='initial'); if (preset&&Preview.selected&&Preview.selected.loadAnglePreset) Preview.selected.loadAnglePreset(preset);
  return {{clip:animation.name,time:Timeline.time,animator:animator.name}};
}})()
""", await_promise=False)
        time.sleep(0.2)
        data = base64.b64decode(client.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})["data"], validate=True)
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise EntityAnimationError(f"SCREENSHOT_NOT_PNG:{leaf}")
        path = directory / f"timeline-{leaf}-{spec['proof_time']:.3f}.png"
        path.write_bytes(data)
        records.append({"clip": leaf, "native_state": state, "path": str(path.relative_to(output)), "sha256": native.sha256_bytes(data)})
    return records


def file_record(path: Path, root: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(root)), "sha256": native.sha256_file(path)}


def copy_inputs(output: Path, asset: str, bbmodel: Path, texture: Path, geometry: Path, brief: Path) -> dict[str, Path]:
    directory = output / "inputs"
    directory.mkdir(parents=True)
    result = {"bbmodel": directory / f"{asset}.source.bbmodel", "texture": directory / f"{asset}.source.png", "geometry": directory / f"{asset}.source.geo.json", "brief": directory / f"{asset}.brief.json"}
    for source, target in ((bbmodel,result["bbmodel"]),(texture,result["texture"]),(geometry,result["geometry"]),(brief,result["brief"])):
        shutil.copyfile(source, target)
    return result


def animation_diagnostics(path: Path, model_identifier: str, specs: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    payload = native.load_json(path)
    actual = payload.get("animations") if isinstance(payload, dict) else None
    if not isinstance(actual, dict):
        return ["NATIVE_ANIMATIONS_OBJECT_MISSING"], {}
    expected_names = {full_clip_name(model_identifier, leaf) for leaf in specs}
    diagnostics = []
    if set(actual) != expected_names:
        diagnostics.append("NATIVE_CLIP_SET_MISMATCH")
    metrics: dict[str, Any] = {}
    for leaf, spec in specs.items():
        name = full_clip_name(model_identifier, leaf)
        record = actual.get(name)
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
        keyframe_count = 0
        maximum_time_delta = 0.0
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
                keyframe_count += len(exported)
                times = sorted(float(value) for value in exported)
                expected_times = [frame["time"] for frame in channel["keyframes"]]
                if len(times) == len(expected_times):
                    maximum_time_delta = max(maximum_time_delta, *(abs(a-b) for a,b in zip(times,expected_times)))
                if len(times) != len(expected_times) or any(not math.isclose(a,b,abs_tol=KEYFRAME_TIME_TOLERANCE_SECONDS) for a,b in zip(times,expected_times)):
                    diagnostics.append(f"NATIVE_KEYFRAME_TIME_MISMATCH:{leaf}:{bone_name}:{channel['channel']}")
        metrics[leaf] = {"duration": record.get("animation_length"), "loop": bool(record.get("loop", False)), "animated_bones": sorted(bones), "keyframe_count": keyframe_count, "maximum_keyframe_time_delta_seconds": maximum_time_delta, "allowed_keyframe_time_tolerance_seconds": KEYFRAME_TIME_TOLERANCE_SECONDS}
    return diagnostics, metrics


@dataclass(frozen=True)
class Inputs:
    asset: str
    bbmodel: Path
    texture: Path
    geometry: Path
    brief: Path
    output: Path
    cdp_endpoint: str
    capture: bool


def execute(inputs: Inputs) -> tuple[int, dict[str, Any]]:
    if inputs.asset not in ENTITY_SPECS:
        raise EntityAnimationError(f"UNSUPPORTED_ASSET:{inputs.asset}")
    spec = ENTITY_SPECS[inputs.asset]
    validate_spec(inputs.asset, spec)
    for label, path in (("BBMODEL",inputs.bbmodel),("TEXTURE",inputs.texture),("GEOMETRY",inputs.geometry),("BRIEF",inputs.brief)):
        if not path.is_file():
            raise EntityAnimationError(f"{label}_NOT_FILE:{path}")
    native.assert_loopback_endpoint(inputs.cdp_endpoint)
    native.ensure_output_empty(inputs.output)
    inputs.output.mkdir(parents=True)
    copied = copy_inputs(inputs.output, inputs.asset, inputs.bbmodel, inputs.texture, inputs.geometry, inputs.brief)
    model, geometry, brief = native.load_json(copied["bbmodel"]), native.load_json(copied["geometry"]), native.load_json(copied["brief"])
    model_identifier = brief.get("model_identifier")
    if brief.get("name") != inputs.asset or not isinstance(model_identifier, str):
        raise EntityAnimationError("BRIEF_IDENTITY_MISMATCH")
    if native.required_names(brief.get("animations"), field="animations") != list(spec["clips"]):
        raise EntityAnimationError("BRIEF_CLIP_MISMATCH")
    if sorted(native.animation_names(model)) != source_preview_names(model_identifier):
        raise EntityAnimationError("SOURCE_PREVIEW_CLIP_SET_UNEXPECTED")
    groups = set(group_names(model))
    authored_bones = {bone for item in spec["clips"].values() for bone in item["bones"]}
    if authored_bones - groups:
        raise EntityAnimationError(f"AUTHORING_BONES_MISSING:{','.join(sorted(authored_bones-groups))}")
    if sum(1 for item in model.get("elements",[]) if isinstance(item,dict) and item.get("type")=="cube") != brief.get("cube_count") or len(group_names(model)) != brief.get("bone_count"):
        raise EntityAnimationError("BRIEF_GEOMETRY_COUNT_MISMATCH")
    required_locators = native.required_names(brief.get("locators"), field="locators")
    exported_locators = native.exported_locator_specs(geometry, required_locators)
    locator_plan = native.build_locator_plan(required_locators, groups, exported_locators, {name:item["source_parent"] for name,item in exported_locators.items()})
    project_dir = inputs.output / "native-project"
    texture_dir = project_dir / "textures"
    texture_dir.mkdir(parents=True)
    project, texture = project_dir / f"{inputs.asset}.bbmodel", texture_dir / f"{inputs.asset}.png"
    shutil.copyfile(copied["bbmodel"], project); shutil.copyfile(copied["texture"], texture)
    staged = native.load_json(project)
    normalized_paths = native.normalize_texture_records(staged, texture.name)
    source_identifier = staged.get("model_identifier")
    if source_identifier != model_identifier:
        raise EntityAnimationError("BBMODEL_IDENTIFIER_MISMATCH")
    staged["model_identifier"] = model_identifier.removeprefix("geometry.")
    project.write_bytes(native.canonical_json_bytes(staged))
    texture_hash = native.sha256_file(texture)
    export_dir = inputs.output / "native-exports"; export_dir.mkdir()
    exports = {"geo1":export_dir/"pass-1.geo.json","anim1":export_dir/"pass-1.animation.json","geo2":export_dir/"pass-2.geo.json","anim2":export_dir/"pass-2.animation.json"}
    native_result: dict[str, Any] = {}; screenshots: list[dict[str, Any]] = []; diagnostics: list[str] = []
    try:
        client = native.CdpConnection(native.discover_websocket(inputs.cdp_endpoint))
        try:
            client.call("Runtime.enable")
            result = client.evaluate(native_authoring_script(project, texture, locator_plan, spec["clips"], model_identifier, exports))
            if not isinstance(result, dict):
                raise EntityAnimationError("NATIVE_RESULT_NOT_OBJECT")
            native_result = result
            if inputs.capture:
                screenshots = capture_timeline(client, inputs.output, model_identifier, spec["clips"])
        finally:
            client.close()
    except (native.NativeToolError, EntityAnimationError, OSError, ValueError, KeyError) as exc:
        diagnostics.append(f"NATIVE_SESSION_ERROR:{exc}")
    export_records: dict[str, Any] = {}
    if not diagnostics:
        for label, first, second in (("geometry",exports["geo1"],exports["geo2"]),("animations",exports["anim1"],exports["anim2"])):
            h1, h2 = native.canonical_export_hash(first.read_text()), native.canonical_export_hash(second.read_text())
            export_records[label] = {"pass_1":file_record(first,inputs.output)|{"canonical_sha256":h1},"pass_2":file_record(second,inputs.output)|{"canonical_sha256":h2},"canonical_equivalent":h1==h2}
            if h1 != h2:
                diagnostics.append(f"TWO_PASS_NATIVE_EXPORT_MISMATCH:{label}")
        signatures = {key:native.sha256_bytes(native.canonical_json_bytes(native.normalize_export_numbers(native_result.get(field)))) for key,field in (("before_authoring","geometry_signature_before"),("after_first_reopen","geometry_signature_after_first_reopen"),("after_second_reopen","geometry_signature_after_second_reopen"))}
        if len(set(signatures.values())) != 1:
            diagnostics.append("NATIVE_GEOMETRY_DRIFT_DURING_ANIMATION_AUTHORING")
        final_geometry = native.load_json(exports["geo2"])
        diagnostics.extend(native.locator_export_diagnostics(locator_plan, native.exported_locator_specs(final_geometry, required_locators)))
        motion_diagnostics, motion_metrics = animation_diagnostics(exports["anim2"], model_identifier, spec["clips"])
        diagnostics.extend(motion_diagnostics)
        expected_full = sorted(full_clip_name(model_identifier, leaf) for leaf in spec["clips"])
        if native_result.get("final_animation_names") != expected_full:
            diagnostics.append("NATIVE_FINAL_CLIP_SET_INVALID")
        if native_result.get("blockbench_version") != "5.1.6":
            diagnostics.append(f"BLOCKBENCH_VERSION_MISMATCH:{native_result.get('blockbench_version')}")
        if native_result.get("warning_count") != 0: diagnostics.append(f"BLOCKBENCH_WARNING_COUNT:{native_result.get('warning_count')}")
        if native_result.get("error_count") != 0: diagnostics.append(f"BLOCKBENCH_ERROR_COUNT:{native_result.get('error_count')}")
        if native.sha256_file(texture) != texture_hash: diagnostics.append("STAGED_TEXTURE_BYTES_CHANGED")
    else:
        signatures, motion_metrics = {}, {}
    receipt = {
        "schema_version":1,"tool_version":TOOL_VERSION,"status":"PASS" if not diagnostics else "FAIL","proof_scope":PROOF_SCOPE,"non_claims":NON_CLAIMS,
        "asset":inputs.asset,"approved_role":spec["role"],"brief_approved_clips":list(spec["clips"]),"native_clip_names":[full_clip_name(model_identifier,leaf) for leaf in spec["clips"]],"authoring_specs":spec["clips"],
        "inputs_are_caller_supplied_copies":True,"evidence_inputs":{label:file_record(path,inputs.output) for label,path in copied.items()},"source_preview_animation_names":sorted(native.animation_names(model)),
        "required_locators":required_locators,"canonical_geometry_locator_transforms":exported_locators,"locator_repair_plan":locator_plan,"cdp_transport":{"loopback_only":True,"endpoint":inputs.cdp_endpoint},
        "native_result":native_result,"screenshots":screenshots,"screenshots_excluded_from_export_determinism":True,"texture_path_fields_normalized":normalized_paths,
        "native_project_identifier_normalization":{"source_value":source_identifier,"native_project_value":model_identifier.removeprefix('geometry.'),"expected_export_value":model_identifier},
        "geometry_signatures_excluding_intended_locators":signatures,"motion_metrics":motion_metrics,"staged_project":file_record(project,inputs.output),"staged_texture":file_record(texture,inputs.output),"exports":export_records,"diagnostics":diagnostics,
    }
    (inputs.output / RECEIPT_NAME).write_bytes(native.canonical_json_bytes(receipt))
    return (0 if not diagnostics else 4), receipt


def parser() -> argparse.ArgumentParser:
    result=argparse.ArgumentParser(description=__doc__)
    result.add_argument("--asset",required=True,choices=sorted(ENTITY_SPECS)); result.add_argument("--bbmodel",required=True,type=Path); result.add_argument("--texture",required=True,type=Path); result.add_argument("--geometry",required=True,type=Path); result.add_argument("--brief",required=True,type=Path); result.add_argument("--output-dir",required=True,type=Path); result.add_argument("--cdp-endpoint",required=True); result.add_argument("--capture-timeline",action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args=parser().parse_args(argv)
    try:
        code, receipt=execute(Inputs(args.asset,args.bbmodel.resolve(),args.texture.resolve(),args.geometry.resolve(),args.brief.resolve(),args.output_dir.resolve(),args.cdp_endpoint,args.capture_timeline))
    except (EntityAnimationError,native.NativeToolError) as exc:
        print(str(exc),file=sys.stderr); return 2
    print(json.dumps({"status":receipt["status"],"receipt":str(args.output_dir/RECEIPT_NAME)},sort_keys=True)); return code


if __name__ == "__main__":
    raise SystemExit(main())
