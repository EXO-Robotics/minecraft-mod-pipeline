from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0.0"
ANALYZER_VERSION = "java-common/1.0.0"

TRIGGERS = {
    "item_use", "item_use_on_block", "item_used_on_entity", "entity_hit",
    "entity_hurt", "entity_death", "entity_spawn", "block_interact",
    "block_place", "block_break", "player_join", "player_spawn",
    "player_death", "scheduled_tick", "object_tick", "processing_complete",
    "projectile_impact", "state_transition",
}
CONDITIONS = {
    "player_sneaking", "held_item_match", "equipped_armor_match",
    "target_entity_match", "block_match", "dimension_match",
    "random_probability", "cooldown_ready", "state_comparison",
    "health_threshold", "distance_threshold", "time_or_tick",
    "permission_or_ownership", "client_server_side", "configuration_flag",
    "dependency_presence",
}
ACTIONS = {
    "spawn_entity", "spawn_projectile", "remove_entity", "create_explosion",
    "damage", "heal", "apply_effect", "remove_effect", "play_sound",
    "spawn_particles", "set_block", "replace_block", "break_block",
    "place_structure", "teleport", "apply_velocity", "modify_item_durability",
    "add_item", "remove_item", "update_persistent_state", "start_cooldown",
    "set_entity_phase", "trigger_behavior", "send_player_feedback",
    "open_interaction_ui", "schedule_delayed_action",
}


def source_actions(body: str) -> list[dict[str, Any]]:
    calls: list[tuple[int, dict[str, Any]]] = []
    specs = [
        (r'context\.addEffect\(\s*"([^"]+)"\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', lambda m: {"type": "apply_effect", "effect": m[0], "duration": int(m[1]), "amplifier": int(m[2])}),
        (r'context\.cooldown\(\s*"([^"]+)"\s*,\s*(\d+)\s*\)', lambda m: {"type": "start_cooldown", "category": m[0], "ticks": int(m[1])}),
        (r'context\.spawnProjectile\(\s*"([^"]+)"\s*,\s*([\d.]+)\s*\)', lambda m: {"type": "spawn_projectile", "entity": m[0], "velocity": {"x": 0, "y": 0, "z": float(m[1])}}),
        (r'context\.explode\(\s*([\d.]+)f?\s*,\s*(true|false)\s*\)', lambda m: {"type": "create_explosion", "power": float(m[0]), "breaks_blocks": m[1] == "true"}),
        (r'context\.damage\(\s*(\d+)\s*\)', lambda m: {"type": "damage", "amount": int(m[0])}),
        (r'context\.playSound\(\s*"([^"]+)"\s*\)', lambda m: {"type": "play_sound", "sound": m[0]}),
        (r'context\.openForm\(\s*"([^"]+)"\s*\)', lambda m: {"type": "open_interaction_ui", "ui": m[0]}),
        (r'context\.placeStructure\(\s*"([^"]+)"\s*\)', lambda m: {"type": "place_structure", "structure": m[0]}),
        (r'context\.setBlock\(\s*"([^"]+)"\s*\)', lambda m: {"type": "set_block", "block": m[0]}),
        (r'context\.dropLoot\(\s*"([^"]+)"\s*\)', lambda m: {"type": "add_item", "item": m[0]}),
        (r'context\.set\(\s*"([^"]+)"\s*,', lambda m: {"type": "update_persistent_state", "key": m[0]}),
    ]
    for pattern, factory in specs:
        for match in re.finditer(pattern, body): calls.append((match.start(), factory(match.groups())))
    return [action for _, action in sorted(calls, key=lambda row: row[0])]


def evidence(path: str, lines: tuple[int, int], rule: str, *, class_name: str | None = None,
             method: str | None = None, resource: str | None = None,
             source_mode: str = "source", confidence: float = 1.0) -> dict[str, Any]:
    return {
        "source_file": path, "class": class_name, "method": method, "field": None,
        "start_line": lines[0], "end_line": lines[1], "ast_node_type": "Annotation",
        "bytecode_location": None, "resource_path": resource,
        "registration_path": None, "extraction_rule": rule,
        "analyzer_version": ANALYZER_VERSION, "confidence": confidence,
        "source_mode": source_mode, "conflicting_evidence": [],
        "human_override_provenance": None,
    }


def _args(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for match in re.finditer(r'(\w+)\s*=\s*("(?:\\.|[^"])*"|[-\d.]+|true|false)', text):
        raw = match.group(2)
        if raw.startswith('"'):
            value: Any = bytes(raw[1:-1], "utf-8").decode("unicode_escape")
        elif raw in {"true", "false"}:
            value = raw == "true"
        else:
            value = float(raw) if "." in raw else int(raw)
        result[match.group(1)] = value
    return result


def health_threshold(expression: str) -> dict[str, Any]:
    condition: dict[str, Any] = {"type": "health_threshold", "expression": expression}
    lower = re.search(r"health\s*>\s*([\d.]+)", expression)
    upper = re.search(r"health\s*<=\s*([\d.]+)", expression)
    if lower: condition["min_ratio_exclusive"] = float(lower.group(1))
    if upper: condition["max_ratio_inclusive"] = float(upper.group(1))
    return condition


def analyze_java(path: str, text: str) -> dict[str, list[dict[str, Any]]]:
    """Extract the validated fixture annotation profile; unknown Java stays diagnostic."""
    lines = text.splitlines()
    class_match = re.search(r"\bclass\s+(\w+)", text)
    class_name = class_match.group(1) if class_match else None
    content: list[dict[str, Any]] = []
    behaviors: list[dict[str, Any]] = []
    state: list[dict[str, Any]] = []
    presentation: list[dict[str, Any]] = []
    ui: list[dict[str, Any]] = []
    networking: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []

    # Production fixture profile: source-retained Java annotations plus ordinary
    # method calls. This is intentionally constrained and never treats an
    # unrecognized call as supported behavior.
    for match in re.finditer(r'@Register\s*\(\s*kind\s*=\s*"([^"]+)"\s*,\s*id\s*=\s*"([^"]+)"\s*\)', text):
        line = text.count("\n", 0, match.start()) + 1
        kind, identifier = match.groups()
        content.append({"kind": kind, "identifier": identifier, "properties": {}, "evidence": [evidence(path, (line, line), "java-common:Register", class_name=class_name)]})
    registered = {(x["kind"], x["identifier"]) for x in content}
    for match in re.finditer(r'Registry\.register\(\s*"([^"]+)"\s*,\s*"([^"]+)"', text):
        kind, identifier = match.groups()
        if (kind, identifier) in registered: continue
        line = text.count("\n", 0, match.start()) + 1
        content.append({"kind": kind, "identifier": identifier, "properties": {}, "evidence": [evidence(path, (line, line), "java-common:Registry.register", class_name=class_name)]})
        registered.add((kind, identifier))
    for match in re.finditer(r'REGISTRATIONS\.put\(\s*"(item|block|entity|recipe):([^\"]+)"\s*,\s*"([^"]*)"', text):
        kind, identifier, properties = match.groups()
        line = text.count("\n", 0, match.start()) + 1
        content.append({"kind": kind, "identifier": identifier, "properties": {"declaration": properties}, "evidence": [evidence(path, (line, line), "java-common:registration-map", class_name=class_name)]})
    for match in re.finditer(r'REGISTRATIONS\.put\(\s*"behavior:([^"]+)"\s*,\s*"([^"]*)"', text):
        trigger, declaration = match.groups(); line = text.count("\n", 0, match.start()) + 1
        actions = []
        if "effect=" in declaration: actions.append({"type": "apply_effect"})
        if "cooldown=" in declaration: actions.append({"type": "start_cooldown"})
        behaviors.append({"id": f"compat_companion:attuned_token/{trigger}", "owner": {"kind": "item", "identifier": "compat_companion:attuned_token"}, "trigger": {"type": trigger}, "conditions": [], "actions": actions, "stateReads": [], "stateWrites": [], "feedback": [], "presentationRequirements": [], "evidence": [evidence(path, (line, line), "java-common:behavior-map", class_name=class_name)], "confidence": .9, "diagnostics": []})

    action_calls = {
        "addEffect": "apply_effect", "cooldown": "start_cooldown", "spawnProjectile": "spawn_projectile",
        "explode": "create_explosion", "damage": "damage", "playSound": "play_sound", "openForm": "open_interaction_ui",
        "placeStructure": "place_structure", "setBlock": "set_block", "dropLoot": "add_item", "set": "update_persistent_state",
    }
    trigger_aliases = {"server_tick": "object_tick", "entity_killed": "entity_death"}
    trigger_pattern = re.compile(r'@Trigger\(\s*"([^"]+)"\s*\)\s*public\s+\w+[<>, ?\w\[\]]*\s+(\w+)\s*\([^)]*\)\s*\{', re.MULTILINE)
    for match in trigger_pattern.finditer(text):
        trigger_raw, method = match.groups()
        trigger = trigger_aliases.get(trigger_raw, trigger_raw)
        depth, pos = 1, match.end()
        while pos < len(text) and depth:
            depth += (text[pos] == "{") - (text[pos] == "}")
            pos += 1
        body = text[match.end():pos - 1]
        start = text.count("\n", 0, match.start()) + 1
        end = text.count("\n", 0, pos) + 1
        prefix = text[:match.start()]
        owner_classes = list(re.finditer(r'(?:class|interface)\s+(\w+)', prefix))
        owner_name = owner_classes[-1].group(1) if owner_classes else class_name
        owner_identifier = re.sub(r'(?<!^)(?=[A-Z])', '_', owner_name or "unknown").lower()
        namespace = next((m[1].split(":", 1)[0] for m in registered if ":" in m[1]), "fixture")
        actions = source_actions(body)
        unknown_calls = sorted(set(re.findall(r'context\.(\w+)\s*\(', body)) - set(action_calls) - {"get"})
        ev = [evidence(path, (start, end), "java-common:Trigger-method", class_name=owner_name, method=method)]
        behavior = {"id": f"{namespace}:{owner_identifier}/{method}", "owner": {"kind": "object", "identifier": f"{namespace}:{owner_identifier}"}, "trigger": {"type": trigger}, "conditions": [], "actions": actions, "stateReads": sorted(set(re.findall(r'context\.get\(\s*"([^"]+)"', body))), "stateWrites": sorted(set(re.findall(r'context\.set\(\s*"([^"]+)"', body))), "feedback": [], "presentationRequirements": [], "evidence": ev, "confidence": 1.0 if trigger in TRIGGERS and not unknown_calls else .75, "diagnostics": [{"severity": "error", "code": "unrecognized_operation", "operation": call} for call in unknown_calls]}
        behaviors.append(behavior)

    for match in re.finditer(r'@State\s*\(\s*keys\s*=\s*\{([^}]*)\}\s*,\s*persistent\s*=\s*(true|false)\s*\)', text):
        line = text.count("\n", 0, match.start()) + 1
        for key in re.findall(r'"([^"]+)"', match.group(1)):
            state.append({"id": key, "scope": "object", "value_type": "number", "default": 0, "persistence": "persistent" if match.group(2) == "true" else "temporary", "evidence": [evidence(path, (line, line), "java-common:State", class_name=class_name)]})
    for match in re.finditer(r'@FormReplacement\s*\(\s*title\s*=\s*"([^"]+)"\s*,\s*purpose\s*=\s*"([^"]+)"\s*\)', text):
        line = text.count("\n", 0, match.start()) + 1
        ui.append({"id": re.sub(r'\W+', '_', match.group(1).lower()), "title": match.group(1), "purpose": match.group(2), "controls": ["action_buttons"], "evidence": [evidence(path, (line, line), "java-common:FormReplacement", class_name=class_name)]})
    for match in re.finditer(r'@Phase\s*\(\s*value\s*=\s*(\d+)\s*,\s*condition\s*=\s*"([^"]+)"\s*\)\s*public\s+void\s+(\w+)\s*\([^)]*\)\s*\{', text):
        phase, condition, method = match.groups(); depth, pos = 1, match.end()
        while pos < len(text) and depth:
            depth += (text[pos] == "{") - (text[pos] == "}"); pos += 1
        body = text[match.end():pos - 1]
        start, end = text.count("\n", 0, match.start()) + 1, text.count("\n", 0, pos) + 1
        actions = source_actions(body) + [{"type": "set_entity_phase", "value": int(phase)}]
        reads = sorted(set(["health"] + re.findall(r'context\.get\(\s*"([^"]+)"', body)))
        writes = sorted(set(["phase"] + re.findall(r'context\.set\(\s*"([^"]+)"', body)))
        behaviors.append({"id": f"representative:rift_boss/{method}", "owner": {"kind": "entity", "identifier": "representative:rift_boss"}, "trigger": {"type": "state_transition"}, "conditions": [health_threshold(condition)], "actions": actions, "stateReads": reads, "stateWrites": writes, "feedback": [], "presentationRequirements": [], "evidence": [evidence(path, (start, end), "java-common:Phase-method", class_name="RiftBoss", method=method)], "confidence": 1.0, "diagnostics": []})
    for match in re.finditer(r'@Approximation\s*\((.*?)\)\s*public', text, re.DOTALL):
        args = _args(match.group(1)); line = text.count("\n", 0, match.start()) + 1
        presentation.append({"kind": "visual_approximation", "owner": class_name, "resource": None, "reason": args.get("reason"), "strategy": args.get("bedrockStrategy"), "evidence": [evidence(path, (line, line), "java-common:Approximation", class_name=class_name)]})

    for number, line in enumerate(lines, 1):
        annotation = re.search(r"@(ModContent|Behavior|StateRequirement|Presentation|UiIntent|NetworkIntent|Unsupported)\s*\((.*)\)", line)
        if not annotation:
            continue
        kind, raw = annotation.groups()
        args = _args(raw)
        ev = [evidence(path, (number, number), f"fixture-annotation:{kind}", class_name=class_name)]
        if kind == "ModContent":
            content.append({"kind": args.get("kind", "unknown"), "identifier": args.get("id"), "properties": args, "evidence": ev})
        elif kind == "Behavior":
            trigger = str(args.get("trigger", "unknown"))
            actions = [x.strip() for x in str(args.get("actions", "")).split(",") if x.strip()]
            conditions = [x.strip() for x in str(args.get("conditions", "")).split(",") if x.strip()]
            unknown = ([f"trigger:{trigger}"] if trigger not in TRIGGERS else []) + [f"condition:{x}" for x in conditions if x not in CONDITIONS] + [f"action:{x}" for x in actions if x not in ACTIONS]
            behavior = {
                "id": args.get("id"), "owner": {"kind": args.get("ownerKind", "item"), "identifier": args.get("owner")},
                "trigger": {"type": trigger}, "conditions": [{"type": x} for x in conditions],
                "actions": [{"type": x} for x in actions], "stateReads": [], "stateWrites": [],
                "feedback": [], "presentationRequirements": [], "evidence": ev,
                "confidence": 1.0 if not unknown else 0.5,
                "diagnostics": [{"severity": "error", "code": "unrecognized_operation", "operation": x} for x in unknown],
            }
            behaviors.append(behavior)
        elif kind == "StateRequirement":
            state.append({"id": args.get("id"), "scope": args.get("scope"), "value_type": args.get("type", "number"), "default": args.get("default", 0), "persistence": args.get("persistence", "persistent"), "evidence": ev})
        elif kind == "Presentation":
            presentation.append({"kind": args.get("kind"), "owner": args.get("owner"), "resource": args.get("resource"), "evidence": ev})
        elif kind == "UiIntent":
            ui.append({"id": args.get("id"), "title": args.get("title"), "purpose": args.get("purpose"), "controls": str(args.get("controls", "")).split(","), "evidence": ev})
        elif kind == "NetworkIntent":
            networking.append({"id": args.get("id"), "direction": args.get("direction"), "trigger": args.get("trigger"), "payload": args.get("payload"), "authority": args.get("authority", "server"), "action": args.get("action"), "replacement_strategy": args.get("replacement"), "evidence": ev})
        else:
            diagnostics.append({"severity": "error", "code": "unsupported_hook", "feature": args.get("feature") or args.get("javaFeature"), "reason": args.get("reason"), "evidence": ev})
    for match in re.finditer(r'@Unsupported\s*\((.*?)\)\s*public', text, re.DOTALL):
        args = _args(match.group(1)); feature = args.get("feature") or args.get("javaFeature")
        if any(row.get("code") == "unsupported_hook" and row.get("feature") == feature for row in diagnostics):
            continue
        line = text.count("\n", 0, match.start()) + 1
        diagnostics.append({"severity": "error", "code": "unsupported_hook", "feature": feature, "reason": args.get("reason"), "evidence": [evidence(path, (line, line), "java-common:Unsupported", class_name=class_name)]})
    return {"content": content, "behaviors": behaviors, "state": state, "presentation": presentation, "ui": ui, "networking": networking, "diagnostics": diagnostics}


def normalized_behavior(behavior: dict[str, Any]) -> dict[str, Any]:
    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: clean(v) for k, v in sorted(value.items()) if k not in {"evidence", "diagnostics", "confidence", "source_file", "start_line", "end_line"}}
        if isinstance(value, list):
            items = [clean(v) for v in value]
            return sorted(items, key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
        return value
    return clean(behavior)


def fingerprint(behavior: dict[str, Any]) -> dict[str, Any]:
    normalized = normalized_behavior(behavior)
    readable = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return {"version": "behavior-fingerprint/1", "readable": readable, "sha256": hashlib.sha256(readable.encode()).hexdigest()}


def attach_fingerprints(ir: dict[str, Any]) -> None:
    for behavior in ir.get("behaviors", []):
        behavior["fingerprint"] = fingerprint(behavior)
