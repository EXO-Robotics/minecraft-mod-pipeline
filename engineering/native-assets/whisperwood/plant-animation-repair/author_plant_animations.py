#!/usr/bin/env python3
"""Author the four brief-approved Whisperwood plant loops in native Blockbench.

Inputs must be caller-supplied copies of the frozen Packet 001 files. The tool
creates exactly one approved animation, repairs the canonical ``effect``
locator, and performs two native save/close/reopen/export passes through an
already-running loopback-only Blockbench renderer.

This establishes native editable and codec evidence only. It does not establish
Bedrock client playback, BDS behavior, console performance, or shipping proof.
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


TOOL_VERSION = "1.0.0"
RECEIPT_NAME = "plant-animation-native-receipt.json"
PROOF_SCOPE = "BLOCKBENCH_NATIVE_PLANT_ANIMATION_AUTHORING_AND_CODEC_EXPORT_ONLY"
NON_CLAIMS = ["BEDROCK_CLIENT", "STABLE_BDS", "PHYSICAL_PS4", "MARKETPLACE"]


def keyframes(channel: str, entries: list[tuple[float, list[float]]]) -> list[dict[str, Any]]:
    return [
        {
            "channel": channel,
            "time": time_value,
            "interpolation": "linear",
            "value": value,
        }
        for time_value, value in entries
    ]


PLANT_SPECS: dict[str, dict[str, Any]] = {
    "lantern_bloom": {
        "clip": "glow_idle",
        "duration": 3.2,
        "motion_identity": "slow restrained glow-core breathing without root motion",
        "bones": {
            "chassis": keyframes(
                "scale",
                [
                    (0.0, [1.0, 1.0, 1.0]),
                    (0.8, [1.025, 1.04, 1.025]),
                    (1.6, [1.05, 1.065, 1.05]),
                    (2.4, [1.025, 1.04, 1.025]),
                    (3.2, [1.0, 1.0, 1.0]),
                ],
            )
        },
        "channel_limits": {"scale_delta": 0.07},
    },
    "pale_reed": {
        "clip": "sway",
        "duration": 4.0,
        "motion_identity": "slow stream-edge reed bend around the clump base",
        "bones": {
            "clump": keyframes(
                "rotation",
                [
                    (0.0, [0.0, 0.0, 0.0]),
                    (1.0, [0.8, 0.0, 2.6]),
                    (2.0, [0.0, 0.0, 0.0]),
                    (3.0, [-0.6, 0.0, -2.2]),
                    (4.0, [0.0, 0.0, 0.0]),
                ],
            )
        },
        "channel_limits": {"rotation_degrees": 3.0},
    },
    "star_grass": {
        "clip": "wind_sway",
        "duration": 3.6,
        "motion_identity": "light clearing wind sway with a small asymmetric return",
        "bones": {
            "clump": keyframes(
                "rotation",
                [
                    (0.0, [0.0, 0.0, 0.0]),
                    (0.9, [0.7, 0.0, 3.2]),
                    (1.8, [0.0, 0.0, 0.0]),
                    (2.7, [-0.5, 0.0, -2.7]),
                    (3.6, [0.0, 0.0, 0.0]),
                ],
            )
        },
        "channel_limits": {"rotation_degrees": 3.5},
    },
    "whisper_fern": {
        "clip": "gentle_sway",
        "duration": 4.8,
        "motion_identity": "independent low-amplitude frond drift with opposing silhouettes",
        "bones": {
            "frond_a": keyframes(
                "rotation",
                [
                    (0.0, [0.0, 0.0, 0.0]),
                    (1.2, [0.8, 0.0, 2.0]),
                    (2.4, [0.0, 0.0, 0.0]),
                    (3.6, [-0.5, 0.0, -1.6]),
                    (4.8, [0.0, 0.0, 0.0]),
                ],
            ),
            "frond_b": keyframes(
                "rotation",
                [
                    (0.0, [0.0, 0.0, 0.0]),
                    (1.2, [-0.5, 0.0, -1.7]),
                    (2.4, [0.0, 0.0, 0.0]),
                    (3.6, [0.7, 0.0, 1.9]),
                    (4.8, [0.0, 0.0, 0.0]),
                ],
            ),
            "frond_c": keyframes(
                "rotation",
                [
                    (0.0, [0.0, 0.0, 0.0]),
                    (1.2, [0.4, 0.0, 1.2]),
                    (2.4, [0.0, 0.0, 0.0]),
                    (3.6, [-0.3, 0.0, -1.0]),
                    (4.8, [0.0, 0.0, 0.0]),
                ],
            ),
        },
        "channel_limits": {"rotation_degrees": 2.25},
    },
}


class PlantAnimationError(RuntimeError):
    """A fail-closed plant animation authoring error."""


def full_clip_name(model_identifier: str, clip: str) -> str:
    prefix = model_identifier.removeprefix("geometry.")
    return f"animation.{prefix}.{clip}"


def source_preview_names(model_identifier: str) -> list[str]:
    prefix = model_identifier.removeprefix("geometry.")
    return sorted([f"animation.{prefix}.idle", f"animation.{prefix}.action"])


def group_names(model: dict[str, Any]) -> list[str]:
    return native.extract_group_names(model)


def count_groups(model: dict[str, Any]) -> int:
    return len(group_names(model))


def count_cubes(model: dict[str, Any]) -> int:
    elements = model.get("elements")
    if not isinstance(elements, list):
        raise PlantAnimationError("BBMODEL_ELEMENTS_NOT_ARRAY")
    return sum(1 for element in elements if isinstance(element, dict) and element.get("type") == "cube")


def validate_spec(asset: str, spec: dict[str, Any]) -> None:
    duration = spec.get("duration")
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise PlantAnimationError(f"SPEC_DURATION_INVALID:{asset}")
    bones = spec.get("bones")
    if not isinstance(bones, dict) or not bones:
        raise PlantAnimationError(f"SPEC_BONES_INVALID:{asset}")
    for bone, frames in bones.items():
        if not isinstance(bone, str) or not isinstance(frames, list) or len(frames) < 3:
            raise PlantAnimationError(f"SPEC_KEYFRAMES_INVALID:{asset}:{bone}")
        channel = frames[0].get("channel")
        if channel not in {"rotation", "scale"} or any(frame.get("channel") != channel for frame in frames):
            raise PlantAnimationError(f"SPEC_CHANNEL_INVALID:{asset}:{bone}")
        times = [frame.get("time") for frame in frames]
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in times):
            raise PlantAnimationError(f"SPEC_TIME_INVALID:{asset}:{bone}")
        if times != sorted(times) or times[0] != 0 or not math.isclose(times[-1], duration, abs_tol=1e-9):
            raise PlantAnimationError(f"SPEC_TIME_RANGE_INVALID:{asset}:{bone}")
        values = [frame.get("value") for frame in frames]
        for value in values:
            if not isinstance(value, list) or len(value) != 3 or any(
                isinstance(component, bool) or not isinstance(component, (int, float)) or not math.isfinite(component)
                for component in value
            ):
                raise PlantAnimationError(f"SPEC_VALUE_INVALID:{asset}:{bone}")
        if values[0] != values[-1]:
            raise PlantAnimationError(f"SPEC_LOOP_SEAM_INVALID:{asset}:{bone}")
        if all(value == values[0] for value in values[1:-1]):
            raise PlantAnimationError(f"SPEC_NO_MOTION:{asset}:{bone}")


def copy_evidence_inputs(
    output: Path,
    asset: str,
    bbmodel: Path,
    texture: Path,
    geometry: Path,
    brief: Path,
) -> dict[str, Path]:
    input_dir = output / "inputs"
    input_dir.mkdir(parents=True)
    result = {
        "bbmodel": input_dir / f"{asset}.source.bbmodel",
        "texture": input_dir / f"{asset}.source.png",
        "geometry": input_dir / f"{asset}.source.geo.json",
        "brief": input_dir / f"{asset}.brief.json",
    }
    for source, destination in (
        (bbmodel, result["bbmodel"]),
        (texture, result["texture"]),
        (geometry, result["geometry"]),
        (brief, result["brief"]),
    ):
        shutil.copyfile(source, destination)
    return result


def geometry_signature_script() -> str:
    return """
  const vector = value => Array.isArray(value) ? value.slice() : null;
  const parentName = element => element.parent && element.parent !== 'root' ? element.parent.name : null;
  const faceRecord = face => ({
    uv: vector(face.uv),
    rotation: face.rotation || 0,
    texture: face.texture === undefined ? null : face.texture,
    cullface: face.cullface || '',
    tint: face.tint === undefined ? -1 : face.tint,
  });
  const geometrySignature = () => ({
    groups: (Group.all || []).map(group => ({
      uuid: group.uuid,
      name: group.name,
      parent: parentName(group),
      origin: vector(group.origin),
      rotation: vector(group.rotation),
    })).sort((a, b) => a.uuid.localeCompare(b.uuid)),
    cubes: (Cube.all || []).map(cube => ({
      uuid: cube.uuid,
      name: cube.name,
      parent: parentName(cube),
      from: vector(cube.from),
      to: vector(cube.to),
      origin: vector(cube.origin),
      rotation: vector(cube.rotation),
      inflate: cube.inflate || 0,
      mirror_uv: !!cube.mirror_uv,
      faces: Object.fromEntries(Object.entries(cube.faces || {}).map(([name, face]) => [name, faceRecord(face)])),
    })).sort((a, b) => a.uuid.localeCompare(b.uuid)),
  });
"""


def native_authoring_script(
    project: Path,
    texture: Path,
    locator_plan: dict[str, dict[str, Any]],
    clip_name: str,
    spec: dict[str, Any],
    geo1: Path,
    anim1: Path,
    geo2: Path,
    anim2: Path,
) -> str:
    paths = {
        "project": str(project),
        "texture": str(texture),
        "geo1": str(geo1),
        "anim1": str(anim1),
        "geo2": str(geo2),
        "anim2": str(anim2),
    }
    return f"""
(async () => {{
  const paths = {native.javascript_literal(paths)};
  const locatorPlan = {native.javascript_literal(locator_plan)};
  const clipName = {native.javascript_literal(clip_name)};
  const spec = {native.javascript_literal(spec)};
  const fail = code => {{ throw new Error(code); }};
  if (typeof Blockbench === 'undefined' || typeof Codecs === 'undefined') fail('BLOCKBENCH_API_UNAVAILABLE');
  if (!Codecs.project || !Codecs.bedrock) fail('REQUIRED_NATIVE_CODEC_UNAVAILABLE');
  if (typeof Animation === 'undefined' || typeof Keyframe === 'undefined') fail('NATIVE_ANIMATION_API_UNAVAILABLE');
  if (typeof AnimationCodec === 'undefined' || !AnimationCodec.codecs || !AnimationCodec.codecs.bedrock) fail('BEDROCK_ANIMATION_CODEC_UNAVAILABLE');
  if (typeof Blockbench.read !== 'function' || typeof Blockbench.writeFile !== 'function') fail('BLOCKBENCH_FILE_API_UNAVAILABLE');

  let warningCount = 0;
  let errorCount = 0;
  const originalWarn = console.warn.bind(console);
  const originalError = console.error.bind(console);
  console.warn = (...args) => {{ warningCount += 1; return originalWarn(...args); }};
  console.error = (...args) => {{ errorCount += 1; return originalError(...args); }};
  const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
  const withTimeout = (promise, code) => Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(code)), 10000))
  ]);
  const readText = path => withTimeout(new Promise((resolve, reject) => {{
    try {{
      Blockbench.read([path], {{readtype: 'text'}}, files => {{
        const file = files && files[0];
        if (!file || typeof file.content !== 'string') {{ reject(new Error('BLOCKBENCH_READ_EMPTY:' + path)); return; }}
        resolve(file.content);
      }});
    }} catch (error) {{ reject(error); }}
  }}), 'BLOCKBENCH_READ_TIMEOUT:' + path);
  const writeText = (path, content) => withTimeout(new Promise((resolve, reject) => {{
    try {{ Blockbench.writeFile(path, {{content}}, () => resolve()); }} catch (error) {{ reject(error); }}
  }}), 'BLOCKBENCH_WRITE_TIMEOUT:' + path);
  const readProject = async () => {{
    const parsed = JSON.parse(await readText(paths.project));
    Codecs.project.load(parsed, {{path: paths.project}});
    await wait(100);
    if (!Project || !Format) fail('NATIVE_PROJECT_REOPEN_FAILED');
  }};
  const saveAndReopenProject = async () => {{
    Project.save_path = paths.project;
    const source = Codecs.project.compile({{bitmaps: true, absolute_paths: false}});
    await writeText(paths.project, source);
    const closed = await Project.close(true);
    if (!closed) fail('NATIVE_PROJECT_CLOSE_FAILED');
    await readProject();
  }};
  const compileText = (codec, label) => {{
    if (!codec || typeof codec.compile !== 'function') fail(label + '_CODEC_COMPILE_UNAVAILABLE');
    const result = codec.compile({{raw: true}});
    return typeof result === 'string' ? result : JSON.stringify(result, null, 2);
  }};
  const exportPass = async (geoPath, animPath) => {{
    await writeText(geoPath, compileText(Codecs.bedrock, 'BEDROCK_GEOMETRY'));
    const animation = AnimationCodec.codecs.bedrock.compileFile(Animation.all || []);
    await writeText(animPath, JSON.stringify(animation, null, 2) + '\\n');
  }};
{geometry_signature_script()}

  await readProject();
  const geometryBefore = geometrySignature();
  const sourceAnimationNames = (Animation.all || []).map(animation => animation.name).sort();
  for (const animation of (Animation.all || []).slice()) animation.remove(false);
  if ((Animation.all || []).length !== 0) fail('SOURCE_ANIMATIONS_NOT_REMOVED');

  const groups = new Map((Group.all || []).map(group => [group.name, group]));
  const animation = new Animation({{
    name: clipName,
    loop: 'loop',
    length: spec.duration,
    snapping: 20,
  }}).add();
  for (const [boneName, frames] of Object.entries(spec.bones)) {{
    const group = groups.get(boneName);
    if (!group) fail('AUTHORING_BONE_MISSING:' + boneName);
    const animator = animation.getBoneAnimator(group);
    for (const frame of frames) {{
      const keyframe = new Keyframe({{
        channel: frame.channel,
        time: frame.time,
        interpolation: frame.interpolation,
        data_points: [{{x: frame.value[0], y: frame.value[1], z: frame.value[2]}}],
      }}, null, animator);
      animator.pushKeyframe(keyframe);
    }}
  }}
  if ((Animation.all || []).length !== 1 || Animation.all[0].name !== clipName) fail('AUTHORED_CLIP_SET_INVALID');

  const locatorRepairs = [];
  for (const [name, locatorSpec] of Object.entries(locatorPlan)) {{
    const parent = groups.get(locatorSpec.parent);
    if (!parent) fail('NATIVE_TARGET_BONE_MISSING:' + name + ':' + locatorSpec.parent);
    let locator = (Locator.all || []).find(candidate => candidate.name === name);
    const created = !locator;
    if (!locator) locator = new Locator({{name, position: locatorSpec.position.slice(), rotation: locatorSpec.rotation.slice()}}).addTo(parent).init();
    else if (!locator.parent || locator.parent.name !== locatorSpec.parent) locator.addTo(parent);
    locator.position = locatorSpec.position.slice();
    locator.rotation = locatorSpec.rotation.slice();
    locatorRepairs.push({{name, parent: locatorSpec.parent, created, uuid: locator.uuid}});
  }}
  if (Texture.all && Texture.all[0]) {{
    Texture.all[0].path = paths.texture;
    Texture.all[0].name = paths.texture.split('/').pop();
  }}

  await saveAndReopenProject();
  if ((Animation.all || []).length !== 1 || Animation.all[0].name !== clipName) fail('CLIP_LOST_AFTER_FIRST_REOPEN');
  for (const name of Object.keys(locatorPlan)) if (!(Locator.all || []).find(locator => locator.name === name)) fail('LOCATOR_LOST_AFTER_FIRST_REOPEN:' + name);
  const geometryAfterFirstReopen = geometrySignature();
  await exportPass(paths.geo1, paths.anim1);

  await saveAndReopenProject();
  if ((Animation.all || []).length !== 1 || Animation.all[0].name !== clipName) fail('CLIP_LOST_AFTER_SECOND_REOPEN');
  for (const name of Object.keys(locatorPlan)) if (!(Locator.all || []).find(locator => locator.name === name)) fail('LOCATOR_LOST_AFTER_SECOND_REOPEN:' + name);
  const geometryAfterSecondReopen = geometrySignature();
  await exportPass(paths.geo2, paths.anim2);

  const finalAnimation = Animation.all[0];
  const authoredKeyframes = [];
  for (const animator of Object.values(finalAnimation.animators || {{}})) {{
    for (const channel of ['rotation', 'position', 'scale']) {{
      for (const keyframe of animator[channel] || []) {{
        authoredKeyframes.push({{
          bone: animator.name,
          channel,
          time: keyframe.time,
          interpolation: keyframe.interpolation,
          value: keyframe.getArray(0),
        }});
      }}
    }}
  }}
  console.warn = originalWarn;
  console.error = originalError;
  return {{
    blockbench_version: Blockbench.version || null,
    format_id: Format && Format.id || null,
    source_animation_names: sourceAnimationNames,
    final_animation_names: (Animation.all || []).map(item => item.name).sort(),
    authored_keyframes: authoredKeyframes.sort((a, b) => a.bone.localeCompare(b.bone) || a.channel.localeCompare(b.channel) || a.time - b.time),
    locator_repairs: locatorRepairs,
    locator_names: (Locator.all || []).map(locator => locator.name).sort(),
    geometry_signature_before: geometryBefore,
    geometry_signature_after_first_reopen: geometryAfterFirstReopen,
    geometry_signature_after_second_reopen: geometryAfterSecondReopen,
    warning_count: warningCount,
    error_count: errorCount,
  }};
}})()
"""


def capture_frames(
    client: native.CdpConnection,
    output: Path,
    clip_name: str,
    duration: float,
) -> list[dict[str, Any]]:
    frame_dir = output / "screenshots"
    frame_dir.mkdir(parents=True, exist_ok=True)
    client.call("Page.enable")
    records: list[dict[str, Any]] = []
    for index, frame_time in enumerate((0.0, duration / 4, duration / 2)):
        script = f"""
(() => {{
  if (!Modes.options || !Modes.options.animate || !Modes.options.animate.select) throw new Error('ANIMATE_MODE_API_UNAVAILABLE');
  Modes.options.animate.select();
  const animation = (Animation.all || []).find(item => item.name === {native.javascript_literal(clip_name)});
  if (!animation) throw new Error('SCREENSHOT_CLIP_MISSING');
  animation.select();
  const firstAnimator = Object.values(animation.animators || {{}}).find(item =>
    (item.rotation && item.rotation.length) || (item.scale && item.scale.length) || (item.position && item.position.length)
  );
  if (!firstAnimator) throw new Error('SCREENSHOT_ANIMATOR_MISSING');
  firstAnimator.addToTimeline();
  firstAnimator.select(false);
  Timeline.setTime({frame_time});
  Animator.preview();
  const preset = DefaultCameraPresets.find(item => item.id === 'initial');
  if (preset && Preview.selected && Preview.selected.loadAnglePreset) Preview.selected.loadAnglePreset(preset);
  return {{time: Timeline.time, clip: animation.name}};
}})()
"""
        state = client.evaluate(script, await_promise=False)
        time.sleep(0.25)
        result = client.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        data = base64.b64decode(result["data"], validate=True)
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise PlantAnimationError(f"SCREENSHOT_NOT_PNG:{index}")
        path = frame_dir / f"frame-{index}-{frame_time:.3f}.png"
        path.write_bytes(data)
        records.append({
            "index": index,
            "timeline_time": frame_time,
            "native_state": state,
            "path": str(path.relative_to(output)),
            "sha256": native.sha256_bytes(data),
        })
    return records


def exported_animation_motion(
    animation_path: Path,
    clip_name: str,
    spec: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    payload = native.load_json(animation_path)
    animations = payload.get("animations") if isinstance(payload, dict) else None
    if not isinstance(animations, dict):
        return ["NATIVE_ANIMATIONS_OBJECT_MISSING"], {}
    diagnostics: list[str] = []
    if set(animations) != {clip_name}:
        diagnostics.append(f"NATIVE_CLIP_SET_MISMATCH:expected={clip_name}:actual={','.join(sorted(animations))}")
        return diagnostics, {}
    clip = animations[clip_name]
    if not isinstance(clip, dict):
        return ["NATIVE_CLIP_NOT_OBJECT"], {}
    if clip.get("loop") is not True:
        diagnostics.append("NATIVE_CLIP_NOT_LOOPING")
    duration = clip.get("animation_length")
    if not isinstance(duration, (int, float)) or not math.isclose(duration, spec["duration"], abs_tol=1e-6):
        diagnostics.append(f"NATIVE_DURATION_MISMATCH:expected={spec['duration']}:actual={duration}")
    bones = clip.get("bones")
    if not isinstance(bones, dict):
        diagnostics.append("NATIVE_BONES_OBJECT_MISSING")
        return diagnostics, {}
    if set(bones) != set(spec["bones"]):
        diagnostics.append(
            f"NATIVE_ANIMATED_BONE_SET_MISMATCH:expected={','.join(sorted(spec['bones']))}:actual={','.join(sorted(bones))}"
        )
    metrics: dict[str, Any] = {"duration": duration, "loop": clip.get("loop"), "bones": {}}
    for bone_name, frames in spec["bones"].items():
        expected_channel = frames[0]["channel"]
        bone = bones.get(bone_name)
        if not isinstance(bone, dict) or set(bone) != {expected_channel}:
            diagnostics.append(f"NATIVE_CHANNEL_SET_MISMATCH:{bone_name}:{expected_channel}")
            continue
        channel = bone[expected_channel]
        if not isinstance(channel, dict):
            diagnostics.append(f"NATIVE_CHANNEL_NOT_KEYFRAMED:{bone_name}:{expected_channel}")
            continue
        exported_values: list[list[float]] = []
        for time_key in sorted(channel, key=float):
            raw = channel[time_key]
            if isinstance(raw, dict):
                raw = raw.get("post") or raw.get("pre")
            if not isinstance(raw, list) or len(raw) != 3 or any(not isinstance(value, (int, float)) for value in raw):
                diagnostics.append(f"NATIVE_KEYFRAME_VALUE_INVALID:{bone_name}:{expected_channel}:{time_key}")
                continue
            exported_values.append([float(value) for value in raw])
        if len(exported_values) != len(frames):
            diagnostics.append(
                f"NATIVE_KEYFRAME_COUNT_MISMATCH:{bone_name}:expected={len(frames)}:actual={len(exported_values)}"
            )
            continue
        if exported_values[0] != exported_values[-1]:
            diagnostics.append(f"NATIVE_LOOP_SEAM_MISMATCH:{bone_name}:{expected_channel}")
        if expected_channel == "rotation":
            peak = max(abs(value) for vector in exported_values for value in vector)
            if peak <= 0 or peak > spec["channel_limits"]["rotation_degrees"] + 1e-6:
                diagnostics.append(f"NATIVE_ROTATION_LIMIT_INVALID:{bone_name}:{peak}")
            metrics["bones"][bone_name] = {"channel": expected_channel, "keyframe_count": len(exported_values), "peak_degrees": peak}
        else:
            peak = max(abs(value - 1.0) for vector in exported_values for value in vector)
            if peak <= 0 or peak > spec["channel_limits"]["scale_delta"] + 1e-6:
                diagnostics.append(f"NATIVE_SCALE_LIMIT_INVALID:{bone_name}:{peak}")
            metrics["bones"][bone_name] = {"channel": expected_channel, "keyframe_count": len(exported_values), "peak_scale_delta": peak}
    return diagnostics, metrics


def file_record(path: Path, output: Path | None = None) -> dict[str, str]:
    display = str(path.relative_to(output)) if output and path.is_relative_to(output) else str(path)
    return {"path": display, "sha256": native.sha256_file(path)}


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
    if inputs.asset not in PLANT_SPECS:
        raise PlantAnimationError(f"UNSUPPORTED_ASSET:{inputs.asset}")
    spec = PLANT_SPECS[inputs.asset]
    validate_spec(inputs.asset, spec)
    for label, path in (("BBMODEL", inputs.bbmodel), ("TEXTURE", inputs.texture), ("GEOMETRY", inputs.geometry), ("BRIEF", inputs.brief)):
        if not path.is_file():
            raise PlantAnimationError(f"{label}_NOT_FILE:{path}")
    native.assert_loopback_endpoint(inputs.cdp_endpoint)
    native.ensure_output_empty(inputs.output)
    if not inputs.texture.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
        raise PlantAnimationError(f"TEXTURE_NOT_PNG:{inputs.texture}")

    inputs.output.mkdir(parents=True, exist_ok=True)
    copied = copy_evidence_inputs(inputs.output, inputs.asset, inputs.bbmodel, inputs.texture, inputs.geometry, inputs.brief)
    model = native.load_json(copied["bbmodel"])
    brief = native.load_json(copied["brief"])
    geometry = native.load_json(copied["geometry"])
    model_identifier = brief.get("model_identifier")
    if brief.get("name") != inputs.asset or not isinstance(model_identifier, str):
        raise PlantAnimationError("BRIEF_IDENTITY_MISMATCH")
    required_clips = native.required_names(brief.get("animations"), field="animations")
    if required_clips != [spec["clip"]]:
        raise PlantAnimationError(f"BRIEF_CLIP_MISMATCH:expected={spec['clip']}:actual={','.join(required_clips)}")
    actual_source_animations = sorted(native.animation_names(model))
    if actual_source_animations != source_preview_names(model_identifier):
        raise PlantAnimationError("SOURCE_PREVIEW_CLIP_SET_UNEXPECTED")
    actual_groups = set(group_names(model))
    missing_bones = sorted(set(spec["bones"]) - actual_groups)
    if missing_bones:
        raise PlantAnimationError(f"AUTHORING_BONES_MISSING:{','.join(missing_bones)}")
    if count_cubes(model) != brief.get("cube_count") or count_groups(model) != brief.get("bone_count"):
        raise PlantAnimationError(
            f"BRIEF_GEOMETRY_COUNT_MISMATCH:cubes={count_cubes(model)}/{brief.get('cube_count')}:bones={count_groups(model)}/{brief.get('bone_count')}"
        )
    required_locators = native.required_names(brief.get("locators"), field="locators")
    exported_locators = native.exported_locator_specs(geometry, required_locators)
    explicit_parent_map = {name: record["source_parent"] for name, record in exported_locators.items()}
    locator_plan = native.build_locator_plan(required_locators, actual_groups, exported_locators, explicit_parent_map)

    project_dir = inputs.output / "native-project"
    texture_dir = project_dir / "textures"
    texture_dir.mkdir(parents=True)
    staged_project = project_dir / f"{inputs.asset}.bbmodel"
    staged_texture = texture_dir / f"{inputs.asset}.png"
    shutil.copyfile(copied["bbmodel"], staged_project)
    shutil.copyfile(copied["texture"], staged_texture)
    staged_json = native.load_json(staged_project)
    normalized_paths = native.normalize_texture_records(staged_json, staged_texture.name)
    source_model_identifier = staged_json.get("model_identifier")
    if source_model_identifier != model_identifier:
        raise PlantAnimationError(
            f"BBMODEL_IDENTIFIER_MISMATCH:expected={model_identifier}:actual={source_model_identifier}"
        )
    native_project_identifier = model_identifier.removeprefix("geometry.")
    staged_json["model_identifier"] = native_project_identifier
    staged_project.write_bytes(native.canonical_json_bytes(staged_json))
    staged_texture_hash_before = native.sha256_file(staged_texture)

    export_dir = inputs.output / "native-exports"
    export_dir.mkdir()
    geo1 = export_dir / "pass-1.geo.json"
    anim1 = export_dir / "pass-1.animation.json"
    geo2 = export_dir / "pass-2.geo.json"
    anim2 = export_dir / "pass-2.animation.json"
    clip_name = full_clip_name(model_identifier, spec["clip"])
    native_result: dict[str, Any] = {}
    screenshots: list[dict[str, Any]] = []
    session_diagnostic: str | None = None
    try:
        client = native.CdpConnection(native.discover_websocket(inputs.cdp_endpoint))
        try:
            client.call("Runtime.enable")
            value = client.evaluate(
                native_authoring_script(staged_project, staged_texture, locator_plan, clip_name, spec, geo1, anim1, geo2, anim2)
            )
            if not isinstance(value, dict):
                raise PlantAnimationError("NATIVE_RESULT_NOT_OBJECT")
            native_result = value
            if inputs.capture:
                screenshots = capture_frames(client, inputs.output, clip_name, spec["duration"])
        finally:
            client.close()
    except (native.NativeToolError, PlantAnimationError, OSError, ValueError, KeyError) as exc:
        session_diagnostic = f"NATIVE_SESSION_ERROR:{exc}"

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "tool_version": TOOL_VERSION,
        "status": "FAIL",
        "proof_scope": PROOF_SCOPE,
        "non_claims": NON_CLAIMS,
        "asset": inputs.asset,
        "brief_approved_clip": spec["clip"],
        "native_clip_name": clip_name,
        "authoring_spec": spec,
        "inputs_are_caller_supplied_copies": True,
        "evidence_inputs": {label: file_record(path, inputs.output) for label, path in copied.items()},
        "source_preview_animation_names": actual_source_animations,
        "required_locators": required_locators,
        "canonical_geometry_locator_transforms": exported_locators,
        "locator_repair_plan": locator_plan,
        "cdp_transport": {"loopback_only": True, "endpoint": inputs.cdp_endpoint},
        "native_session_started": True,
        "native_result": native_result,
        "screenshots": screenshots,
        "screenshots_excluded_from_export_determinism": True,
        "texture_path_fields_normalized": normalized_paths,
        "native_project_identifier_normalization": {
            "source_value": source_model_identifier,
            "native_project_value": native_project_identifier,
            "expected_export_value": model_identifier,
            "reason": "Blockbench Bedrock codec prepends geometry. to the project model_identifier",
        },
        "diagnostics": [],
    }
    diagnostics: list[str] = []
    if session_diagnostic:
        diagnostics.append(session_diagnostic)
    exports: dict[str, Any] = {}
    if not diagnostics:
        for label, first, second in (("geometry", geo1, geo2), ("animations", anim1, anim2)):
            if not first.is_file() or not second.is_file():
                diagnostics.append(f"NATIVE_EXPORT_MISSING:{label}")
                continue
            first_hash = native.canonical_export_hash(first.read_text(encoding="utf-8"))
            second_hash = native.canonical_export_hash(second.read_text(encoding="utf-8"))
            exports[label] = {
                "pass_1": file_record(first, inputs.output) | {"canonical_sha256": first_hash},
                "pass_2": file_record(second, inputs.output) | {"canonical_sha256": second_hash},
                "canonical_equivalent": first_hash == second_hash,
            }
            if first_hash != second_hash:
                diagnostics.append(f"TWO_PASS_NATIVE_EXPORT_MISMATCH:{label}")
        geometry_signatures = {
            "before_authoring": native.sha256_bytes(
                native.canonical_json_bytes(native.normalize_export_numbers(native_result.get("geometry_signature_before")))
            ),
            "after_first_reopen": native.sha256_bytes(
                native.canonical_json_bytes(native.normalize_export_numbers(native_result.get("geometry_signature_after_first_reopen")))
            ),
            "after_second_reopen": native.sha256_bytes(
                native.canonical_json_bytes(native.normalize_export_numbers(native_result.get("geometry_signature_after_second_reopen")))
            ),
        }
        if len(set(geometry_signatures.values())) != 1:
            diagnostics.append("NATIVE_GEOMETRY_DRIFT_DURING_ANIMATION_AUTHORING")
        receipt["geometry_signatures_excluding_intended_locator"] = geometry_signatures
        receipt["geometry_signature_numeric_normalization"] = {
            "decimal_places": native.CANONICAL_FLOAT_DECIMAL_PLACES,
            "maximum_rounding_delta": native.CANONICAL_FLOAT_MAX_ROUNDING_DELTA,
            "purpose": "ignore native IEEE-754 serialization noise without masking material geometry drift",
        }
        if native.sha256_file(staged_texture) != staged_texture_hash_before:
            diagnostics.append("STAGED_TEXTURE_BYTES_CHANGED")
        locator_diagnostics: list[str] = []
        try:
            final_geometry = native.load_json(geo2)
            geometry_entries = final_geometry.get("minecraft:geometry") if isinstance(final_geometry, dict) else None
            exported_identifier = None
            if isinstance(geometry_entries, list) and len(geometry_entries) == 1 and isinstance(geometry_entries[0], dict):
                description = geometry_entries[0].get("description")
                if isinstance(description, dict):
                    exported_identifier = description.get("identifier")
            receipt["native_export_geometry_identifier"] = exported_identifier
            if exported_identifier != model_identifier:
                diagnostics.append(
                    f"NATIVE_GEOMETRY_IDENTIFIER_MISMATCH:expected={model_identifier}:actual={exported_identifier}"
                )
            native_locator_specs = native.exported_locator_specs(final_geometry, required_locators)
            locator_diagnostics = native.locator_export_diagnostics(locator_plan, native_locator_specs)
            receipt["native_export_locator_transforms"] = native_locator_specs
        except native.NativeToolError as exc:
            locator_diagnostics = [str(exc)]
        diagnostics.extend(locator_diagnostics)
        motion_diagnostics, motion_metrics = exported_animation_motion(anim2, clip_name, spec)
        diagnostics.extend(motion_diagnostics)
        receipt["motion_metrics"] = motion_metrics
        if native_result.get("final_animation_names") != [clip_name]:
            diagnostics.append("NATIVE_FINAL_CLIP_SET_INVALID")
        if native_result.get("warning_count") != 0:
            diagnostics.append(f"BLOCKBENCH_WARNING_COUNT:{native_result.get('warning_count')}")
        if native_result.get("error_count") != 0:
            diagnostics.append(f"BLOCKBENCH_ERROR_COUNT:{native_result.get('error_count')}")
        receipt["staged_project"] = file_record(staged_project, inputs.output)
        receipt["staged_texture"] = file_record(staged_texture, inputs.output)
    receipt["exports"] = exports
    receipt["diagnostics"] = diagnostics
    receipt["status"] = "PASS" if not diagnostics else "FAIL"
    receipt_path = inputs.output / RECEIPT_NAME
    receipt_path.write_bytes(native.canonical_json_bytes(receipt))
    return (0 if not diagnostics else 4), receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--asset", required=True, choices=sorted(PLANT_SPECS))
    result.add_argument("--bbmodel", required=True, type=Path)
    result.add_argument("--texture", required=True, type=Path)
    result.add_argument("--geometry", required=True, type=Path)
    result.add_argument("--brief", required=True, type=Path)
    result.add_argument("--output-dir", required=True, type=Path)
    result.add_argument("--cdp-endpoint", required=True)
    result.add_argument("--capture-frames", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    inputs = Inputs(
        asset=args.asset,
        bbmodel=args.bbmodel.resolve(),
        texture=args.texture.resolve(),
        geometry=args.geometry.resolve(),
        brief=args.brief.resolve(),
        output=args.output_dir.resolve(),
        cdp_endpoint=args.cdp_endpoint,
        capture=args.capture_frames,
    )
    try:
        code, receipt = execute(inputs)
    except (PlantAnimationError, native.NativeToolError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "receipt": str(inputs.output / RECEIPT_NAME)}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
