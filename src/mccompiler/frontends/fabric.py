from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from pathlib import Path

from ..semantics import evidence


def metadata(document: dict[str, Any], raw_text: str, path: str = "fabric.mod.json") -> tuple[dict[str, Any], dict[str, Any]]:
    """Return lossless Fabric metadata evidence plus the normalized inventory view."""
    mod_id = str(document.get("id") or "unknown_fabric_mod")
    dependencies: list[dict[str, Any]] = []
    for key, optional in (("depends", False), ("recommends", True), ("suggests", True), ("conflicts", True), ("breaks", True)):
        values = document.get(key, {})
        if isinstance(values, dict):
            dependencies.extend({"id": str(dep_id), "version": version, "optional": optional, "kind": key} for dep_id, version in values.items())
        elif isinstance(values, list):
            dependencies.extend({"id": str(dep_id), "version": None, "optional": optional, "kind": key} for dep_id in values if isinstance(dep_id, str))
    normalized = {
        "id": mod_id,
        "name": document.get("name") or mod_id,
        "version": document.get("version"),
        "loader": "fabric",
        "dependencies": dependencies,
        "metadata": {
            "environment": document.get("environment"),
            "entrypoints": document.get("entrypoints", {}),
            "mixins": document.get("mixins", []),
            "access_widener": document.get("accessWidener"),
            "nested_jars": document.get("jars", []),
            "provides": document.get("provides", []),
            "license": document.get("license"),
            "raw": document,
        },
    }
    provenance = {
        "path": path,
        "kind": "fabric.mod.json",
        "source_mode": "metadata",
        "extraction_rule": "fabric-metadata/1.0.0",
        "sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        "raw_text": raw_text,
        "raw_document": document,
    }
    return normalized, provenance


def _line(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def _mod_id(text: str) -> str:
    match = re.search(r'\bMOD_ID\s*=\s*"([a-z0-9_.-]+)"', text)
    return match.group(1) if match else "fabric_mod"


def _identifier(expression: str, mod_id: str) -> str | None:
    direct = re.search(r'(?:Identifier\.(?:of|tryParse)|new\s+Identifier)\s*\(\s*"([a-z0-9_.-]+)"\s*,\s*"([a-z0-9_./-]+)"', expression)
    if direct:
        return f"{direct.group(1)}:{direct.group(2)}"
    constant = re.search(r'(?:Identifier\.(?:of|tryParse)|new\s+Identifier)\s*\(\s*MOD_ID\s*,\s*"([a-z0-9_./-]+)"', expression)
    if constant:
        return f"{mod_id}:{constant.group(1)}"
    single = re.search(r'(?:Identifier\.(?:of|tryParse)|new\s+Identifier)\s*\(\s*"([a-z0-9_.-]+:[a-z0-9_./-]+)"', expression)
    return single.group(1) if single else None


def analyze_source(path: str, text: str) -> dict[str, list[dict[str, Any]]]:
    """Recognize a deliberately small, authentic modern Fabric API surface."""
    result: dict[str, list[dict[str, Any]]] = {key: [] for key in ("content", "behaviors", "state", "presentation", "ui", "networking", "diagnostics")}
    mod_id = _mod_id(text)
    class_match = re.search(r'\bclass\s+(\w+)', text)
    class_name = class_match.group(1) if class_match else None
    initializer = re.search(r'\bimplements\s+(?:ModInitializer|ClientModInitializer)\b', text)
    if initializer:
        line = _line(text, initializer.start())
        result["diagnostics"].append({"severity": "info", "code": "loader_entrypoint", "feature": class_name, "loader": "fabric", "entrypoint": initializer.group(0).split()[-1], "evidence": [evidence(path, (line, line), "fabric-source:ModInitializer", class_name=class_name, confidence=1.0)]})

    registration = re.compile(r'Registry\.register\s*\(\s*Registries\.(ITEM|BLOCK|ENTITY_TYPE|BLOCK_ENTITY_TYPE)\s*,(.*?)(?:;|\n)', re.DOTALL)
    kinds = {"ITEM": "item", "BLOCK": "block", "ENTITY_TYPE": "entity", "BLOCK_ENTITY_TYPE": "block_entity"}
    for match in registration.finditer(text):
        identifier = _identifier(match.group(2), mod_id)
        if not identifier:
            continue
        line = _line(text, match.start())
        result["content"].append({"kind": kinds[match.group(1)], "identifier": identifier, "properties": {"loader": "fabric", "registry": match.group(1)}, "evidence": [evidence(path, (line, line), "fabric-source:Registry.register", class_name=class_name, confidence=.9)]})

    callbacks = [
        (r'UseItemCallback\.EVENT\.register\s*\(', "item_use", "fabric-source:UseItemCallback"),
        (r'UseBlockCallback\.EVENT\.register\s*\(', "block_interact", "fabric-source:UseBlockCallback"),
        (r'ServerTickEvents\.END_SERVER_TICK\.register\s*\(', "object_tick", "fabric-source:ServerTickEvents"),
        (r'AttackEntityCallback\.EVENT\.register\s*\(', "entity_hit", "fabric-source:AttackEntityCallback"),
    ]
    for pattern, trigger, rule in callbacks:
        for index, match in enumerate(re.finditer(pattern, text)):
            line = _line(text, match.start())
            result["behaviors"].append({
                "id": f"{mod_id}:fabric_callback/{trigger}_{index}", "owner": {"kind": "mod", "identifier": mod_id},
                "trigger": {"type": trigger}, "conditions": [], "actions": [], "stateReads": [], "stateWrites": [],
                "feedback": [], "presentationRequirements": [], "evidence": [evidence(path, (line, line), rule, class_name=class_name, confidence=.7)],
                "confidence": .7, "diagnostics": [{"severity": "info", "code": "callback_body_unresolved", "message": "Fabric callback subscription is proven; callback behavior requires deeper data-flow analysis."}],
            })

    for match in re.finditer(r'class\s+(\w+)\s+extends\s+PersistentState\b', text):
        line = _line(text, match.start())
        result["state"].append({"id": re.sub(r'(?<!^)(?=[A-Z])', '_', match.group(1)).lower(), "scope": "world", "value_type": "object", "default": {}, "persistence": "persistent", "evidence": [evidence(path, (line, line), "fabric-source:PersistentState", class_name=match.group(1), confidence=.8)]})

    for index, match in enumerate(re.finditer(r'ServerPlayNetworking\.registerGlobalReceiver\s*\(\s*([^,]+),', text)):
        line = _line(text, match.start())
        result["networking"].append({"id": f"{mod_id}:receiver_{index}", "direction": "client_to_server", "trigger": "custom_payload", "payload": match.group(1).strip(), "authority": "server", "action": "unresolved", "replacement_strategy": None, "evidence": [evidence(path, (line, line), "fabric-source:ServerPlayNetworking.registerGlobalReceiver", class_name=class_name, confidence=.75)]})

    for match in re.finditer(r'@(Mixin|Inject|Redirect|ModifyArg|ModifyVariable|Overwrite)\b', text):
        line = _line(text, match.start())
        result["diagnostics"].append({"severity": "error", "code": "unsupported_hook", "feature": f"fabric_mixin:{match.group(1)}", "reason": "Fabric Mixin bytecode injection requires manual reconstruction for Bedrock.", "evidence": [evidence(path, (line, line), "fabric-source:mixin", class_name=class_name, confidence=1.0)]})
    return result


def _bytecode_evidence(archive: Path, fact: dict[str, Any], rule: str, confidence: float = .68) -> dict[str, Any]:
    return {
        "source_file": fact.get("source_file"), "class": fact.get("class"), "method": fact.get("method"),
        "field": None, "start_line": None, "end_line": None, "ast_node_type": None,
        "bytecode_location": f"{fact.get('class')}#{fact.get('method') or '<class>'}", "resource_path": None,
        "registration_path": None, "extraction_rule": rule, "analyzer_version": "fabric-bytecode/1.0.0",
        "confidence": confidence, "source_mode": "bytecode-javap", "conflicting_evidence": [],
        "human_override_provenance": None,
    }


def analyze_facts(archive: Path, facts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Lower loader-neutral facts for a small, authentic Fabric API surface."""
    result: dict[str, list[dict[str, Any]]] = {key: [] for key in ("content", "behaviors", "state", "presentation", "ui", "networking", "diagnostics")}
    by_class: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        if fact.get("class"):
            by_class.setdefault(str(fact["class"]), []).append(fact)
    registry_kinds = {"ITEM": "item", "BLOCK": "block", "ENTITY_TYPE": "entity", "BLOCK_ENTITY_TYPE": "block_entity"}
    callbacks = {
        "net.fabricmc.fabric.api.event.player.UseItemCallback$Event": "item_use",
        "net.fabricmc.fabric.api.event.player.AttackEntityCallback$Event": "entity_hit",
        "net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents$EndTick": "object_tick",
        "net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents$Event": "object_tick",
    }
    for class_name, rows in by_class.items():
        ordered = sorted(rows, key=lambda row: int(row.get("instruction_line") or 0))
        constants: list[str] = []
        fields: list[dict[str, Any]] = []
        callback_counts: dict[str, int] = {}
        mod_id = "fabric_mod"
        for row in ordered:
            if row["fact_type"] == "constant":
                constants.append(str(row["value"]))
            elif row["fact_type"] == "field":
                fields.append(row)
            elif row["fact_type"] == "class" and (
                "net.fabricmc.api.ModInitializer" in row.get("interfaces", []) or
                "net.fabricmc.api.ClientModInitializer" in row.get("interfaces", [])
            ):
                result["diagnostics"].append({"severity": "info", "code": "loader_entrypoint", "feature": class_name.rsplit(".", 1)[-1], "loader": "fabric", "entrypoint": "ModInitializer", "evidence": [_bytecode_evidence(archive, row, "fabric-bytecode:ModInitializer")]})
            elif row["fact_type"] == "class" and row.get("super_name") == "net.minecraft.world.PersistentState":
                state_id = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name.rsplit("$", 1)[-1]).lower()
                result["state"].append({"id": state_id, "scope": "world", "value_type": "object", "default": {}, "persistence": "persistent", "evidence": [_bytecode_evidence(archive, row, "fabric-bytecode:PersistentState")]})
            elif row["fact_type"] == "invoke":
                owner, name = row.get("owner"), row.get("name")
                if owner == "net.minecraft.util.Identifier" and name in {"of", "tryParse", "<init>"} and len(constants) >= 2:
                    namespace, path = constants[-2], constants[-1]
                    if re.fullmatch(r"[a-z0-9_.-]+", namespace) and re.fullmatch(r"[a-z0-9_./-]+", path):
                        mod_id = namespace
                if owner == "net.minecraft.registry.Registry" and name == "register":
                    registry = next((f["name"] for f in reversed(fields) if f.get("owner") == "net.minecraft.registry.Registries" and f.get("name") in registry_kinds), None)
                    candidates = [value for value in constants[-5:] if re.fullmatch(r"[a-z0-9_.-]+(?::[a-z0-9_./-]+)?", value)]
                    identifier = None
                    if len(candidates) >= 2:
                        identifier = f"{candidates[-2]}:{candidates[-1]}"
                    elif candidates and ":" in candidates[-1]:
                        identifier = candidates[-1]
                    if registry and identifier:
                        result["content"].append({"kind": registry_kinds[registry], "identifier": identifier, "properties": {"loader": "fabric", "registry": registry}, "evidence": [_bytecode_evidence(archive, row, "fabric-bytecode:Registry.register")]})
                if name == "register" and owner in callbacks:
                    trigger = callbacks[owner]
                    index = callback_counts.get(trigger, 0); callback_counts[trigger] = index + 1
                    result["behaviors"].append({"id": f"{mod_id}:fabric_callback/{trigger}_{index}", "owner": {"kind": "mod", "identifier": mod_id}, "trigger": {"type": trigger}, "conditions": [], "actions": [], "stateReads": [], "stateWrites": [], "feedback": [], "presentationRequirements": [], "evidence": [_bytecode_evidence(archive, row, f"fabric-bytecode:{owner.rsplit('.', 1)[-1]}", .62)], "confidence": .62, "diagnostics": [{"severity": "info", "code": "callback_body_unresolved", "message": "Fabric callback subscription is proven from bytecode; callback body remains unresolved."}]})
                if owner == "net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking" and name == "registerGlobalReceiver":
                    result["networking"].append({"id": f"{mod_id}:receiver_0", "direction": "client_to_server", "trigger": "custom_payload", "payload": "bytecode-proven-payload", "authority": "server", "action": "unresolved", "replacement_strategy": None, "evidence": [_bytecode_evidence(archive, row, "fabric-bytecode:ServerPlayNetworking.registerGlobalReceiver", .62)]})
        annotation_names = {str(row.get("annotation")) for row in rows if row["fact_type"] == "annotation"}
        resource_mixins = any(row["fact_type"] == "resource" and "mixin" in str(row.get("path", "")).lower() for row in facts)
        if any(name.endswith(".Mixin") or name.endswith(".Inject") for name in annotation_names) or ("Mixin" in class_name and resource_mixins):
            result["diagnostics"].append({"severity": "error", "code": "unsupported_hook", "feature": "fabric_mixin:bytecode", "reason": "Fabric Mixin bytecode injection requires manual reconstruction for Bedrock.", "evidence": [_bytecode_evidence(archive, rows[0], "fabric-bytecode:mixin", .7)]})
    return result
