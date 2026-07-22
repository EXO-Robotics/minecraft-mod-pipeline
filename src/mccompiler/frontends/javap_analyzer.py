from __future__ import annotations

import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from ..semantics import TRIGGERS, health_threshold


CALL_ACTIONS = {
    "addEffect": "apply_effect", "cooldown": "start_cooldown", "spawnProjectile": "spawn_projectile",
    "explode": "create_explosion", "damage": "damage", "playSound": "play_sound", "openForm": "open_interaction_ui",
    "placeStructure": "place_structure", "setBlock": "set_block", "dropLoot": "add_item", "set": "update_persistent_state",
}
TRIGGER_ALIASES = {"server_tick": "object_tick", "entity_killed": "entity_death"}


def _bytecode_actions(block: str) -> tuple[list[dict[str, Any]], list[str]]:
    pending: list[Any] = []
    actions: list[dict[str, Any]] = []
    calls: list[str] = []
    for line in block.splitlines():
        string = re.search(r"\bldc(?:2_w|_w)?\s+#[0-9]+\s+// String (.+)$", line)
        number = re.search(r"\b(?:bipush|sipush)\s+(-?\d+)", line)
        small = re.search(r"\biconst_([m\d]+)", line)
        small_float = re.search(r"\b[fd]const_([012])", line)
        floating = re.search(r"// (?:float|double) (-?[\d.]+)[fd]?", line)
        if string: pending.append(string.group(1).strip())
        elif number: pending.append(int(number.group(1)))
        elif small: pending.append(-1 if small.group(1) == "m1" else int(small.group(1)))
        elif small_float: pending.append(float(small_float.group(1)))
        elif floating: pending.append(float(floating.group(1)))
        invoke = re.search(r"FixtureApi\$Context\.([A-Za-z_$][\w$]*):", line)
        if not invoke: continue
        call = invoke.group(1); calls.append(call)
        strings = [x for x in pending if isinstance(x, str)]
        numbers = [x for x in pending if isinstance(x, (int, float)) and not isinstance(x, bool)]
        action: dict[str, Any] | None = None
        if call == "addEffect" and strings: action = {"type": "apply_effect", "effect": strings[-1], "duration": int(numbers[-2]), "amplifier": int(numbers[-1])}
        elif call == "cooldown" and strings: action = {"type": "start_cooldown", "category": strings[-1], "ticks": int(numbers[-1])}
        elif call == "spawnProjectile" and strings: action = {"type": "spawn_projectile", "entity": strings[-1], "velocity": {"x": 0, "y": 0, "z": float(numbers[-1])}}
        elif call == "explode": action = {"type": "create_explosion", "power": float(numbers[-2]), "breaks_blocks": bool(numbers[-1])}
        elif call == "damage": action = {"type": "damage", "amount": int(numbers[-1])}
        elif call == "playSound" and strings: action = {"type": "play_sound", "sound": strings[-1]}
        elif call == "openForm" and strings: action = {"type": "open_interaction_ui", "ui": strings[-1]}
        elif call == "placeStructure" and strings: action = {"type": "place_structure", "structure": strings[-1]}
        elif call == "setBlock" and strings: action = {"type": "set_block", "block": strings[-1]}
        elif call == "dropLoot" and strings: action = {"type": "add_item", "item": strings[-1]}
        elif call == "set" and strings: action = {"type": "update_persistent_state", "key": strings[0]}
        if action: actions.append(action)
        if call != "get": pending = []
    return actions, calls


def _javap() -> str | None:
    candidates = [
        os.environ.get("MCCOMPILER_JAVAP"), shutil.which("javap"),
        "/opt/homebrew/opt/openjdk/bin/javap", "/usr/local/opt/openjdk/bin/javap",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            try:
                subprocess.run([candidate, "-version"], check=True, capture_output=True, timeout=10)
                return candidate
            except (OSError, subprocess.SubprocessError):
                continue
    return None


def available() -> bool:
    return _javap() is not None


def _ev(archive: Path, class_name: str, method: str | None, start: int, end: int, rule: str) -> dict[str, Any]:
    return {
        "source_file": f"{archive.name}!/{class_name.replace('.', '/')}.class", "class": class_name,
        "method": method, "field": None, "start_line": start or None, "end_line": end or None,
        "ast_node_type": None, "bytecode_location": f"{class_name}#{method or '<class>'}",
        "resource_path": None, "registration_path": None, "extraction_rule": rule,
        "analyzer_version": "jar-bytecode-javap/1.0.0", "confidence": 1.0,
        "source_mode": "bytecode-javap", "conflicting_evidence": [], "human_override_provenance": None,
    }


def _annotation(block: str, simple_name: str) -> str | None:
    match = re.search(rf"FixtureApi\${simple_name}\(\s*(.*?)\s*\)", block, re.DOTALL)
    return match.group(1) if match else None


def _value(body: str, name: str = "value") -> str | None:
    match = re.search(rf"\b{name}=\"([^\"]*)\"", body)
    return match.group(1) if match else None


def _method_blocks(output: str) -> list[tuple[str, str]]:
    headers = list(re.finditer(r"^  (?:public|protected|private).+?\s([\w$<>]+)\([^;]*\);$", output, re.MULTILINE))
    result = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(output)
        result.append((header.group(1), output[header.start():end]))
    return result


def analyze_archive(path: str | Path) -> dict[str, list[dict[str, Any]]]:
    archive = Path(path).resolve()
    tool = _javap()
    result = {key: [] for key in ("content", "behaviors", "state", "presentation", "ui", "networking", "diagnostics")}
    if not tool or not archive.is_file() or not zipfile.is_zipfile(archive):
        return result
    with zipfile.ZipFile(archive) as jar:
        classes = sorted(name[:-6].replace("/", ".") for name in jar.namelist() if name.endswith(".class") and not name.startswith("META-INF/versions/"))
    namespace = re.sub(r"[^a-z0-9_]+", "_", archive.stem.lower()) or "bytecode_mod"
    for class_name in classes:
        completed = subprocess.run([tool, "-classpath", str(archive), "-p", "-c", "-l", "-v", class_name], capture_output=True, text=True, timeout=30)
        if completed.returncode:
            result["diagnostics"].append({"severity": "error", "code": "javap_failed", "class": class_name, "message": completed.stderr.strip()})
            continue
        output = completed.stdout
        owner = class_name.rsplit("$", 1)[-1]
        owner_id = re.sub(r"(?<!^)(?=[A-Z])", "_", owner).lower()
        for ann in re.finditer(r"FixtureApi\$Register\(\s*kind=\"([^\"]+)\"\s*id=\"([^\"]+)\"\s*\)", output):
            kind, identifier = ann.groups()
            result["content"].append({"kind": kind, "identifier": identifier, "properties": {}, "evidence": [_ev(archive, class_name, None, 0, 0, "javap:Register")]})
            namespace = identifier.split(":", 1)[0]
        constants: list[str] = []
        for raw_line in output.splitlines():
            string_match = re.search(r"// String (.+)$", raw_line)
            if string_match:
                constants.append(string_match.group(1).strip())
            if "FixtureApi$Registry.register:" in raw_line:
                candidates = constants[-3:]
                kind_index = next((i for i, value in enumerate(candidates) if value in {"item", "block", "entity", "recipe", "loot_table", "sound", "structure", "spawn_rule", "player_state"}), None)
                if kind_index is not None and kind_index + 1 < len(candidates):
                    kind, identifier = candidates[kind_index], candidates[kind_index + 1]
                    if ":" in identifier:
                        result["content"].append({"kind": kind, "identifier": identifier, "properties": {}, "evidence": [_ev(archive, class_name, None, 0, 0, "javap:Registry.register")]})
                        namespace = identifier.split(":", 1)[0]
                constants = []
        for method, block in _method_blocks(output):
            lines = [int(x) for x in re.findall(r"\bline (\d+):", block)]
            start, end = (min(lines), max(lines)) if lines else (0, 0)
            trigger_body = _annotation(block, "Trigger")
            phase_body = _annotation(block, "Phase")
            form_body = _annotation(block, "FormReplacement")
            trigger_raw = _value(trigger_body or "")
            if phase_body is not None:
                trigger_raw = "state_transition"
            if trigger_raw:
                trigger = TRIGGER_ALIASES.get(trigger_raw, trigger_raw)
                actions, calls = _bytecode_actions(block)
                if phase_body is not None:
                    phase_match = re.search(r"value=(\d+)", phase_body)
                    actions.append({"type": "set_entity_phase", "value": int(phase_match.group(1)) if phase_match else 1})
                state_reads: list[str] = []
                state_writes: list[str] = []
                string_hits = list(re.finditer(r"// String ([^\r\n]+)", block))
                for index, hit in enumerate(string_hits):
                    tail = block[hit.end():string_hits[index + 1].start() if index + 1 < len(string_hits) else len(block)]
                    key = hit.group(1).strip()
                    if "FixtureApi$Context.get:" in tail: state_reads.append(key)
                    if "FixtureApi$Context.set:" in tail: state_writes.append(key)
                unknown = sorted(set(calls) - set(CALL_ACTIONS) - {"get"})
                ev = [_ev(archive, class_name, method, start, end, "javap:annotated-method")]
                conditions = []
                if phase_body is not None:
                    conditions.append(health_threshold(_value(phase_body, "condition") or ""))
                behavior = {
                    "id": f"{namespace}:{owner_id}/{method}", "owner": {"kind": "entity" if owner == "RiftBoss" else "object", "identifier": f"{namespace}:{owner_id}"},
                    "trigger": {"type": trigger}, "conditions": conditions, "actions": actions,
                    "stateReads": sorted(set(state_reads + (["health"] if phase_body is not None else []))), "stateWrites": sorted(set(state_writes + (["phase"] if phase_body is not None else []))), "feedback": [], "presentationRequirements": [],
                    "evidence": ev, "confidence": 1.0 if trigger in TRIGGERS and not unknown else .75,
                    "diagnostics": [{"severity": "error", "code": "unrecognized_operation", "operation": x} for x in unknown],
                }
                result["behaviors"].append(behavior)
            if form_body is not None:
                result["ui"].append({"id": owner_id, "title": _value(form_body, "title"), "purpose": _value(form_body, "purpose"), "controls": ["action_buttons"], "evidence": [_ev(archive, class_name, method, start, end, "javap:FormReplacement")]})
        state_body = _annotation(output, "State")
        if state_body is not None:
            for key in re.findall(r'"([^\"]+)"', state_body.split("persistent=", 1)[0]):
                result["state"].append({"id": key, "scope": "object", "value_type": "number", "default": 0, "persistence": "persistent" if "persistent=true" in state_body else "temporary", "evidence": [_ev(archive, class_name, None, 0, 0, "javap:State")]})
        approximation = _annotation(output, "Approximation")
        if approximation is not None:
            result["presentation"].append({"kind": "visual_approximation", "owner": class_name, "reason": _value(approximation, "reason"), "strategy": _value(approximation, "bedrockStrategy"), "evidence": [_ev(archive, class_name, None, 0, 0, "javap:Approximation")]})
        unsupported = _annotation(output, "Unsupported")
        if unsupported is not None:
            result["diagnostics"].append({"severity": "error", "code": "unsupported_hook", "feature": _value(unsupported, "javaFeature"), "reason": _value(unsupported, "reason"), "evidence": [_ev(archive, class_name, None, 0, 0, "javap:Unsupported")]})
    # Stable de-duplication protects against annotations repeated in verbose output.
    for key in result:
        seen: set[str] = set(); unique = []
        for item in result[key]:
            marker = repr(item)
            if marker not in seen: seen.add(marker); unique.append(item)
        result[key] = unique
    content_seen: set[tuple[str, str]] = set(); content_unique = []
    for item in result["content"]:
        marker = (str(item.get("kind")), str(item.get("identifier")))
        if marker not in content_seen: content_seen.add(marker); content_unique.append(item)
    result["content"] = content_unique
    return result
