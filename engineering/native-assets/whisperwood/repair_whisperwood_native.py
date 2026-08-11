#!/usr/bin/env python3
"""Native Blockbench repair gate for copied Whisperwood source assets.

The tool never edits its inputs. It stages an isolated copy, performs a
fail-closed animation preflight, and then drives an already-running Blockbench
renderer through a loopback-only Chrome DevTools Protocol endpoint.

This is native-editor/export evidence only. It is not Bedrock client, BDS,
console, or Marketplace evidence.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.client
import json
import secrets
import shutil
import socket
import struct
import sys
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


TOOL_VERSION = "1.0.0"
RECEIPT_NAME = "whisperwood-native-blockbench-receipt.json"
DEFAULT_LOCATOR_BONES: dict[str, tuple[str, ...]] = {
    "effect": ("root",),
    "gaze": ("head",),
    "projectile": ("head",),
}
DEFAULT_SCREENSHOT_VIEWS = ("front", "three_quarter", "wireframe", "animate")


class NativeToolError(RuntimeError):
    """A deterministic, user-actionable native-gate failure."""


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise NativeToolError(f"INVALID_JSON:{path}:{exc}") from exc


def required_names(raw: Any, *, field: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise NativeToolError(f"BRIEF_FIELD_NOT_ARRAY:{field}")
    result: list[str] = []
    for index, entry in enumerate(raw):
        if isinstance(entry, str):
            name = entry.strip()
        elif isinstance(entry, dict):
            candidate = entry.get("name") or entry.get("id") or entry.get("clip")
            name = candidate.strip() if isinstance(candidate, str) else ""
        else:
            name = ""
        if not name:
            raise NativeToolError(f"BRIEF_FIELD_INVALID_ENTRY:{field}:{index}")
        if name not in result:
            result.append(name)
    return result


def clip_leaf(name: str) -> str:
    return name.rsplit(".", 1)[-1]


def animation_names(model: dict[str, Any]) -> list[str]:
    animations = model.get("animations", [])
    if not isinstance(animations, list):
        raise NativeToolError("BBMODEL_ANIMATIONS_NOT_ARRAY")
    names: list[str] = []
    for index, entry in enumerate(animations):
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise NativeToolError(f"BBMODEL_ANIMATION_INVALID:{index}")
        names.append(entry["name"])
    return names


def missing_role_clips(required: Iterable[str], actual: Iterable[str]) -> list[str]:
    actual_names = set(actual)
    actual_leaves = {clip_leaf(name) for name in actual_names}
    return [name for name in required if name not in actual_names and clip_leaf(name) not in actual_leaves]


def extract_group_names(model: dict[str, Any]) -> list[str]:
    names: list[str] = []

    def walk(nodes: Any) -> None:
        if not isinstance(nodes, list):
            return
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if isinstance(node.get("name"), str):
                names.append(node["name"])
            walk(node.get("children"))

    walk(model.get("outliner"))
    return names


def choose_locator_bones(
    required: Iterable[str],
    group_names: Iterable[str],
    explicit: dict[str, str] | None = None,
) -> dict[str, str]:
    explicit = explicit or {}
    groups = set(group_names)
    plan: dict[str, str] = {}
    for locator in required:
        if locator in explicit:
            target = explicit[locator]
            if target not in groups:
                raise NativeToolError(f"EXPLICIT_LOCATOR_BONE_MISSING:{locator}:{target}")
            plan[locator] = target
            continue
        candidates = DEFAULT_LOCATOR_BONES.get(locator, ("root",))
        target = next((candidate for candidate in candidates if candidate in groups), None)
        if target is None:
            raise NativeToolError(f"NO_SENSIBLE_EXISTING_BONE:{locator}:{','.join(candidates)}")
        plan[locator] = target
    unknown_explicit = sorted(set(explicit) - set(required))
    if unknown_explicit:
        raise NativeToolError(f"LOCATOR_MAP_NOT_REQUIRED:{','.join(unknown_explicit)}")
    return plan


def normalize_texture_records(model: dict[str, Any], texture_name: str) -> int:
    textures = model.get("textures")
    if not isinstance(textures, list) or not textures:
        raise NativeToolError("BBMODEL_TEXTURES_MISSING")
    changed = 0
    relative = f"textures/{texture_name}"
    for texture in textures:
        if not isinstance(texture, dict):
            raise NativeToolError("BBMODEL_TEXTURE_RECORD_INVALID")
        for key, value in (("name", texture_name), ("path", relative), ("relative_path", relative)):
            if texture.get(key) != value:
                texture[key] = value
                changed += 1
    return changed


def canonical_export_hash(text: str) -> str:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise NativeToolError(f"NATIVE_EXPORT_INVALID_JSON:{exc}") from exc
    return sha256_bytes(canonical_json_bytes(parsed))


def write_receipt(output_dir: Path, receipt: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / RECEIPT_NAME
    path.write_bytes(canonical_json_bytes(receipt))
    return path


def stage_inputs(bbmodel_path: Path, texture_path: Path, output_dir: Path) -> tuple[Path, Path]:
    project_dir = output_dir / "native-project"
    texture_dir = project_dir / "textures"
    texture_dir.mkdir(parents=True, exist_ok=True)
    staged_model = project_dir / bbmodel_path.name
    staged_texture = texture_dir / texture_path.name
    shutil.copyfile(bbmodel_path, staged_model)
    shutil.copyfile(texture_path, staged_texture)
    return staged_model, staged_texture


def ensure_output_empty(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise NativeToolError(f"OUTPUT_NOT_EMPTY:{output_dir}")


def assert_loopback_endpoint(endpoint: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(endpoint if "://" in endpoint else f"http://{endpoint}")
    if parsed.scheme not in {"http", "ws"} or not parsed.hostname or not parsed.port:
        raise NativeToolError(f"INVALID_CDP_ENDPOINT:{endpoint}")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise NativeToolError(f"CDP_ENDPOINT_RESOLUTION_FAILED:{parsed.hostname}") from exc
    if not addresses or any(address not in {"127.0.0.1", "::1"} for address in addresses):
        raise NativeToolError(f"CDP_ENDPOINT_NOT_LOOPBACK:{parsed.hostname}")
    return parsed


def discover_websocket(endpoint: str) -> str:
    parsed = assert_loopback_endpoint(endpoint)
    if parsed.scheme == "ws":
        return endpoint
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    try:
        connection.request("GET", "/json/list")
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()
    if not isinstance(payload, list):
        raise NativeToolError("CDP_TARGET_LIST_INVALID")
    targets = [target for target in payload if isinstance(target, dict) and target.get("webSocketDebuggerUrl")]
    blockbench = next((target for target in targets if "blockbench" in str(target.get("title", "")).lower()), None)
    target = blockbench or next((target for target in targets if target.get("type") == "page"), None)
    if target is None:
        raise NativeToolError("CDP_BLOCKBENCH_PAGE_NOT_FOUND")
    websocket_url = str(target["webSocketDebuggerUrl"])
    assert_loopback_endpoint(websocket_url)
    return websocket_url


class CdpConnection:
    """Small dependency-free loopback WebSocket client sufficient for CDP."""

    def __init__(self, websocket_url: str, timeout: float = 30.0) -> None:
        parsed = assert_loopback_endpoint(websocket_url)
        if parsed.scheme != "ws":
            raise NativeToolError("CDP_WEBSOCKET_MUST_USE_WS")
        self._socket = socket.create_connection((parsed.hostname, parsed.port), timeout=timeout)
        self._socket.settimeout(timeout)
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"
        request = (
            f"GET {path} HTTP/1.1\r\nHost: {parsed.hostname}:{parsed.port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self._socket.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            response += self._socket.recv(4096)
        if not response.startswith(b"HTTP/1.1 101"):
            raise NativeToolError(f"CDP_WEBSOCKET_HANDSHAKE_FAILED:{response[:80]!r}")
        self._next_id = 1

    def close(self) -> None:
        self._socket.close()

    def _send_text(self, value: str) -> None:
        payload = value.encode("utf-8")
        mask = secrets.token_bytes(4)
        header = bytearray([0x81])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self._socket.sendall(bytes(header) + masked)

    def _read_exact(self, count: int) -> bytes:
        result = b""
        while len(result) < count:
            chunk = self._socket.recv(count - len(result))
            if not chunk:
                raise NativeToolError("CDP_WEBSOCKET_CLOSED")
            result += chunk
        return result

    def _receive_text(self) -> str:
        first, second = self._read_exact(2)
        opcode = first & 0x0F
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        if second & 0x80:
            mask = self._read_exact(4)
        else:
            mask = None
        payload = self._read_exact(length)
        if mask:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        if opcode == 0x8:
            raise NativeToolError("CDP_WEBSOCKET_CLOSED")
        if opcode == 0x9:
            raise NativeToolError("CDP_UNEXPECTED_PING")
        if opcode != 0x1:
            return self._receive_text()
        return payload.decode("utf-8")

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._send_text(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            response = json.loads(self._receive_text())
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise NativeToolError(f"CDP_CALL_FAILED:{method}:{response['error']}")
            return response.get("result", {})

    def evaluate(self, expression: str, *, await_promise: bool = True) -> Any:
        result = self.call("Runtime.evaluate", {
            "expression": expression,
            "awaitPromise": await_promise,
            "returnByValue": True,
            "userGesture": True,
        })
        if "exceptionDetails" in result:
            description = result.get("exceptionDetails", {}).get("exception", {}).get("description", "unknown")
            raise NativeToolError(f"BLOCKBENCH_EVALUATION_FAILED:{description}")
        remote = result.get("result", {})
        if remote.get("subtype") == "error":
            raise NativeToolError(f"BLOCKBENCH_EVALUATION_FAILED:{remote.get('description', 'unknown')}")
        return remote.get("value")


def javascript_literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def native_session_script(
    project_path: Path,
    texture_path: Path,
    locator_plan: dict[str, str],
    pass_one_geometry: Path,
    pass_one_animation: Path,
    pass_two_geometry: Path,
    pass_two_animation: Path,
) -> str:
    """Build the native Blockbench transaction executed in its renderer."""
    paths = {
        "project": str(project_path),
        "texture": str(texture_path),
        "geo1": str(pass_one_geometry),
        "anim1": str(pass_one_animation),
        "geo2": str(pass_two_geometry),
        "anim2": str(pass_two_animation),
    }
    return f"""
(async () => {{
  const paths = {javascript_literal(paths)};
  const locatorPlan = {javascript_literal(locator_plan)};
  const fail = (code) => {{ throw new Error(code); }};
  if (typeof Blockbench === 'undefined' || typeof Codecs === 'undefined') fail('BLOCKBENCH_API_UNAVAILABLE');
  if (!Codecs.project || !Codecs.bedrock) fail('REQUIRED_NATIVE_CODEC_UNAVAILABLE');
  const fs = (typeof require === 'function') ? require('fs') : null;
  if (!fs) fail('BLOCKBENCH_NODE_FILESYSTEM_UNAVAILABLE');

  let warningCount = 0;
  const originalWarn = console.warn.bind(console);
  console.warn = (...args) => {{ warningCount += 1; return originalWarn(...args); }};
  const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
  const readProject = async () => {{
    const parsed = JSON.parse(fs.readFileSync(paths.project, 'utf8'));
    Codecs.project.load(parsed, {{path: paths.project}});
    await wait(100);
    if (!Project || !Format) fail('NATIVE_PROJECT_REOPEN_FAILED');
  }};
  const saveAndReopenProject = async () => {{
    Project.save_path = paths.project;
    Project.saved = true;
    const source = Codecs.project.compile({{bitmaps: true, absolute_paths: false}});
    fs.writeFileSync(paths.project, source, 'utf8');
    const closed = await Project.close(true);
    if (!closed) fail('NATIVE_PROJECT_CLOSE_FAILED');
    await readProject();
  }};
  const compileText = (codec, label) => {{
    if (!codec || typeof codec.compile !== 'function') fail(label + '_CODEC_COMPILE_UNAVAILABLE');
    const result = codec.compile({{raw: true}});
    return typeof result === 'string' ? result : JSON.stringify(result, null, 2);
  }};
  const exportPass = (geoPath, animPath) => {{
    fs.writeFileSync(geoPath, compileText(Codecs.bedrock, 'BEDROCK_GEOMETRY'), 'utf8');
    if (typeof AnimationCodec === 'undefined' || !AnimationCodec.codecs || !AnimationCodec.codecs.bedrock) fail('BEDROCK_ANIMATION_CODEC_UNAVAILABLE');
    const animation = AnimationCodec.codecs.bedrock.compileFile(Animation.all || []);
    fs.writeFileSync(animPath, JSON.stringify(animation, null, 2) + '\\n', 'utf8');
  }};

  await readProject();
  const groups = new Map((Group.all || []).map(group => [group.name, group]));
  const existingLocators = new Set((Locator.all || []).map(locator => locator.name));
  const repairs = [];
  for (const [name, boneName] of Object.entries(locatorPlan)) {{
    const parent = groups.get(boneName);
    if (!parent) fail('NATIVE_TARGET_BONE_MISSING:' + name + ':' + boneName);
    let locator = (Locator.all || []).find(candidate => candidate.name === name);
    const created = !locator;
    if (!locator) {{
      const position = Array.isArray(parent.origin) ? parent.origin.slice() : [0, 0, 0];
      locator = new Locator({{name, position, rotation: [0, 0, 0]}}).addTo(parent).init();
    }} else if (!locator.parent || locator.parent.name !== boneName) {{
      locator.addTo(parent);
    }}
    repairs.push({{name: locator.name, parent: boneName, uuid: locator.uuid, created}});
  }}
  if (Texture.all && Texture.all[0]) {{
    Texture.all[0].path = paths.texture;
    Texture.all[0].name = paths.texture.split('/').pop();
  }}
  await saveAndReopenProject();
  const afterFirstReopen = new Set((Locator.all || []).map(locator => locator.name));
  for (const name of Object.keys(locatorPlan)) if (!afterFirstReopen.has(name)) fail('LOCATOR_LOST_AFTER_SAVE_REOPEN:' + name);
  exportPass(paths.geo1, paths.anim1);
  await saveAndReopenProject();
  const afterSecondReopen = new Set((Locator.all || []).map(locator => locator.name));
  for (const name of Object.keys(locatorPlan)) if (!afterSecondReopen.has(name)) fail('LOCATOR_LOST_AFTER_SECOND_REOPEN:' + name);
  exportPass(paths.geo2, paths.anim2);
  console.warn = originalWarn;
  return {{
    blockbench_version: Blockbench.version || null,
    format_id: Format && Format.id || null,
    locator_repairs: repairs,
    locator_names: Array.from(afterSecondReopen).sort(),
    animation_names: (Animation.all || []).map(animation => animation.name).sort(),
    warning_count: warningCount
  }};
}})()
"""


def screenshot_view_script(view: str) -> str:
    scripts = {
        "front": "const preset = DefaultCameraPresets.find(item => item.id === 'front'); if (!preset || !Preview.selected || !Preview.selected.loadAnglePreset) throw new Error('FRONT_PREVIEW_PRESET_UNAVAILABLE'); Preview.selected.loadAnglePreset(preset);",
        "three_quarter": "const preset = DefaultCameraPresets.find(item => item.id === 'initial'); if (!preset || !Preview.selected || !Preview.selected.loadAnglePreset) throw new Error('THREE_QUARTER_PREVIEW_PRESET_UNAVAILABLE'); Preview.selected.loadAnglePreset(preset);",
        "wireframe": "if (!BarItems.view_mode || !BarItems.view_mode.set) throw new Error('VIEW_MODE_API_UNAVAILABLE'); BarItems.view_mode.set('wireframe');",
        "animate": "if (!Modes.options || !Modes.options.animate || !Modes.options.animate.select) throw new Error('ANIMATE_MODE_API_UNAVAILABLE'); Modes.options.animate.select();",
    }
    if view not in scripts:
        raise NativeToolError(f"UNSUPPORTED_SCREENSHOT_VIEW:{view}")
    return f"(() => {{{scripts[view]} return true;}})()"


def capture_screenshots(client: CdpConnection, output_dir: Path, views: Iterable[str]) -> list[dict[str, str]]:
    evidence_dir = output_dir / "screenshots"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, str]] = []
    client.call("Page.enable")
    for view in views:
        client.evaluate(screenshot_view_script(view), await_promise=False)
        time.sleep(0.2)
        result = client.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
        data = base64.b64decode(result["data"], validate=True)
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise NativeToolError(f"SCREENSHOT_NOT_PNG:{view}")
        path = evidence_dir / f"{view}.png"
        path.write_bytes(data)
        records.append({"view": view, "path": str(path.relative_to(output_dir)), "sha256": sha256_bytes(data)})
    return records


@dataclass(frozen=True)
class Inputs:
    bbmodel: Path
    texture: Path
    brief: Path
    output: Path
    cdp_endpoint: str
    locator_map: Path | None
    screenshot_views: tuple[str, ...]


def execute(inputs: Inputs) -> tuple[int, dict[str, Any]]:
    for label, path in (("BBMODEL", inputs.bbmodel), ("TEXTURE", inputs.texture), ("BRIEF", inputs.brief)):
        if not path.is_file():
            raise NativeToolError(f"{label}_NOT_FILE:{path}")
    assert_loopback_endpoint(inputs.cdp_endpoint)
    ensure_output_empty(inputs.output)
    if not inputs.texture.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
        raise NativeToolError(f"TEXTURE_NOT_PNG:{inputs.texture}")
    brief = load_json(inputs.brief)
    model = load_json(inputs.bbmodel)
    required_clips = required_names(brief.get("animations"), field="animations")
    required_locators = required_names(brief.get("locators"), field="locators")
    actual_clips = animation_names(model)
    missing = missing_role_clips(required_clips, actual_clips)
    base_receipt: dict[str, Any] = {
        "schema_version": 1,
        "tool_version": TOOL_VERSION,
        "proof_scope": "BLOCKBENCH_NATIVE_EDITABLE_ROUNDTRIP_AND_CODEC_EXPORT_ONLY",
        "non_claims": ["BEDROCK_CLIENT", "STABLE_BDS", "PHYSICAL_PS4", "MARKETPLACE"],
        "inputs": {
            "bbmodel": {"path": str(inputs.bbmodel), "sha256": sha256_file(inputs.bbmodel)},
            "texture": {"path": str(inputs.texture), "sha256": sha256_file(inputs.texture)},
            "brief": {"path": str(inputs.brief), "sha256": sha256_file(inputs.brief)},
        },
        "required_role_animations": required_clips,
        "actual_role_animations": actual_clips,
        "missing_role_animations": missing,
        "required_locators": required_locators,
    }
    if missing:
        base_receipt.update({
            "status": "WITHHELD_MISSING_ROLE_ANIMATIONS",
            "diagnostics": [f"MISSING_REQUIRED_ROLE_CLIP:{name}" for name in missing],
            "native_session_started": False,
        })
        write_receipt(inputs.output, base_receipt)
        return 3, base_receipt

    explicit: dict[str, str] = {}
    if inputs.locator_map:
        raw_map = load_json(inputs.locator_map)
        if not isinstance(raw_map, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in raw_map.items()):
            raise NativeToolError("LOCATOR_MAP_MUST_BE_STRING_OBJECT")
        explicit = raw_map
    plan = choose_locator_bones(required_locators, extract_group_names(model), explicit)
    staged_model, staged_texture = stage_inputs(inputs.bbmodel, inputs.texture, inputs.output)
    staged_json = load_json(staged_model)
    path_changes = normalize_texture_records(staged_json, staged_texture.name)
    staged_model.write_bytes(canonical_json_bytes(staged_json))

    export_dir = inputs.output / "native-exports"
    export_dir.mkdir(parents=True)
    geo1, anim1 = export_dir / "pass-1.geo.json", export_dir / "pass-1.animation.json"
    geo2, anim2 = export_dir / "pass-2.geo.json", export_dir / "pass-2.animation.json"
    try:
        websocket_url = discover_websocket(inputs.cdp_endpoint)
        client = CdpConnection(websocket_url)
        try:
            client.call("Runtime.enable")
            native_result = client.evaluate(native_session_script(staged_model, staged_texture, plan, geo1, anim1, geo2, anim2))
            screenshots = capture_screenshots(client, inputs.output, inputs.screenshot_views) if inputs.screenshot_views else []
        finally:
            client.close()
    except (NativeToolError, OSError, ValueError, KeyError) as exc:
        base_receipt.update({
            "status": "FAIL_NATIVE_SESSION",
            "diagnostics": [f"NATIVE_SESSION_ERROR:{exc}"],
            "native_session_started": True,
            "cdp_transport": {"loopback_only": True, "endpoint": inputs.cdp_endpoint},
            "texture_path_fields_normalized": path_changes,
            "locator_repair_plan": plan,
        })
        write_receipt(inputs.output, base_receipt)
        return 4, base_receipt

    exports: dict[str, dict[str, Any]] = {}
    equality = True
    for label, first, second in (("geometry", geo1, geo2), ("animations", anim1, anim2)):
        if not first.is_file() or not second.is_file():
            raise NativeToolError(f"NATIVE_EXPORT_MISSING:{label}")
        first_text, second_text = first.read_text(encoding="utf-8"), second.read_text(encoding="utf-8")
        first_canonical, second_canonical = canonical_export_hash(first_text), canonical_export_hash(second_text)
        equivalent = first_canonical == second_canonical
        equality = equality and equivalent
        exports[label] = {
            "pass_1": {"path": str(first.relative_to(inputs.output)), "sha256": sha256_file(first), "canonical_sha256": first_canonical},
            "pass_2": {"path": str(second.relative_to(inputs.output)), "sha256": sha256_file(second), "canonical_sha256": second_canonical},
            "canonical_equivalent": equivalent,
        }
    required_exported = set(required_locators)
    geometry = load_json(geo2)
    exported_locators: set[str] = set()
    for geometry_entry in geometry.get("minecraft:geometry", []):
        for bone in geometry_entry.get("bones", []):
            if isinstance(bone.get("locators"), dict):
                exported_locators.update(bone["locators"])
    missing_exported = sorted(required_exported - exported_locators)
    native_actual_clips = native_result.get("animation_names", []) if isinstance(native_result, dict) else []
    missing_native_clips = missing_role_clips(required_clips, native_actual_clips)
    warning_count = native_result.get("warning_count", 0) if isinstance(native_result, dict) else 0
    status = "PASS" if equality and not missing_exported and not missing_native_clips and warning_count == 0 else "FAIL"
    diagnostics: list[str] = []
    if not equality:
        diagnostics.append("TWO_PASS_NATIVE_EXPORT_MISMATCH")
    diagnostics.extend(f"LOCATOR_MISSING_FROM_NATIVE_EXPORT:{name}" for name in missing_exported)
    diagnostics.extend(f"ROLE_CLIP_MISSING_AFTER_NATIVE_REOPEN:{name}" for name in missing_native_clips)
    if warning_count:
        diagnostics.append(f"BLOCKBENCH_WARNING_COUNT:{warning_count}")
    base_receipt.update({
        "status": status,
        "diagnostics": diagnostics,
        "native_session_started": True,
        "cdp_transport": {"loopback_only": True, "endpoint": inputs.cdp_endpoint},
        "texture_path_fields_normalized": path_changes,
        "locator_repair_plan": plan,
        "native_result": native_result,
        "staged_project": {"path": str(staged_model.relative_to(inputs.output)), "sha256": sha256_file(staged_model)},
        "exports": exports,
        "exported_locator_names": sorted(exported_locators),
        "screenshots": screenshots,
        "screenshots_excluded_from_export_determinism": True,
    })
    write_receipt(inputs.output, base_receipt)
    return (0 if status == "PASS" else 4), base_receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--bbmodel", required=True, type=Path, help="Caller-supplied copied editable source")
    result.add_argument("--texture", required=True, type=Path, help="Caller-supplied copied PNG source")
    result.add_argument("--brief", required=True, type=Path, help="Approved per-asset brief")
    result.add_argument("--output-dir", required=True, type=Path, help="New or empty isolated evidence directory")
    result.add_argument("--cdp-endpoint", required=True, help="Isolated loopback Blockbench CDP endpoint")
    result.add_argument("--locator-map", type=Path, help="Optional JSON object mapping required locator names to existing bones")
    result.add_argument(
        "--capture-screenshots",
        nargs="*",
        choices=DEFAULT_SCREENSHOT_VIEWS,
        help="Capture representative views; no values selects the default representative set",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    views: tuple[str, ...]
    if args.capture_screenshots is None:
        views = ()
    elif not args.capture_screenshots:
        views = DEFAULT_SCREENSHOT_VIEWS
    else:
        views = tuple(args.capture_screenshots)
    inputs = Inputs(
        bbmodel=args.bbmodel.resolve(),
        texture=args.texture.resolve(),
        brief=args.brief.resolve(),
        output=args.output_dir.resolve(),
        cdp_endpoint=args.cdp_endpoint,
        locator_map=args.locator_map.resolve() if args.locator_map else None,
        screenshot_views=views,
    )
    try:
        code, receipt = execute(inputs)
    except NativeToolError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "receipt": str(inputs.output / RECEIPT_NAME)}, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
