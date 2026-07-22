from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from pathlib import Path

from ..semantics import evidence


def _manifest(raw_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current: str | None = None
    for raw in raw_text.replace("\r\n", "\n").split("\n"):
        if raw.startswith(" ") and current:
            fields[current] += raw[1:]
        elif ":" in raw:
            current, value = raw.split(":", 1)
            fields[current] = value.strip()
    return fields


def _dependency(value: str) -> dict[str, Any]:
    match = re.match(r'(?:(?:(required|optional)-)?(before|after):)?([^@]+)(?:@(.+))?$', value)
    if not match:
        return {"id": value, "version": None, "optional": False, "kind": "legacy"}
    requirement, ordering, dep_id, version = match.groups()
    return {"id": dep_id, "version": version, "optional": requirement == "optional", "kind": f"legacy-{ordering}" if ordering else "legacy"}


def metadata(document: Any, raw_text: str, manifest_text: str | None = None, path: str = "mcmod.info") -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse Forge/FML 1.7.x metadata without discarding original fields or bytes."""
    rows = document if isinstance(document, list) else [document] if isinstance(document, dict) else []
    manifest = _manifest(manifest_text or "")
    mods: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        mod_id = str(row.get("modid") or row.get("modId") or "unknown_forge_mod")
        raw_dependencies = row.get("dependencies", [])
        if isinstance(raw_dependencies, str):
            raw_dependencies = [part.strip() for part in raw_dependencies.split(";") if part.strip()]
        dependencies = [_dependency(dep) for dep in raw_dependencies if isinstance(dep, str)]
        mods.append({"id": mod_id, "name": row.get("name") or mod_id, "version": row.get("version"), "loader": "forge-legacy", "dependencies": dependencies, "metadata": {"raw": row, "manifest": manifest}})
    evidence_rows = [{"path": path, "kind": "mcmod.info", "source_mode": "metadata", "extraction_rule": "forge-legacy-metadata/1.0.0", "sha256": hashlib.sha256(raw_text.encode()).hexdigest(), "raw_text": raw_text, "raw_document": document}]
    if manifest_text is not None:
        evidence_rows.append({"path": "META-INF/MANIFEST.MF", "kind": "manifest", "source_mode": "metadata", "extraction_rule": "forge-legacy-manifest/1.0.0", "sha256": hashlib.sha256(manifest_text.encode()).hexdigest(), "raw_text": manifest_text, "raw_document": manifest})
    core_plugin = manifest.get("FMLCorePlugin")
    if core_plugin:
        diagnostics.append({"severity": "error", "code": "unsupported_hook", "feature": f"forge_coremod:{core_plugin}", "reason": "Forge coremod bytecode transformation has no direct Bedrock equivalent.", "evidence": [evidence("META-INF/MANIFEST.MF", (1, 1), "forge-legacy-manifest:FMLCorePlugin", source_mode="metadata", confidence=1.0)]})
    return mods, evidence_rows, diagnostics


def _line(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def analyze_source(path: str, text: str) -> dict[str, list[dict[str, Any]]]:
    """Recognize representative Forge 1.7.10 registration/event/network surfaces."""
    result: dict[str, list[dict[str, Any]]] = {key: [] for key in ("content", "behaviors", "state", "presentation", "ui", "networking", "diagnostics")}
    mod_match = re.search(r'@Mod\s*\([^)]*\bmodid\s*=\s*(?:"([^"]+)"|\w+\.MODID)', text, re.DOTALL)
    constant = re.search(r'\bMODID\s*=\s*"([a-z0-9_.-]+)"', text)
    mod_id = (mod_match.group(1) if mod_match and mod_match.group(1) else None) or (constant.group(1) if constant else "forge_mod")
    class_match = re.search(r'\bclass\s+(\w+)', text)
    class_name = class_match.group(1) if class_match else None
    for match in re.finditer(r'@EventHandler\s+public\s+\w+[<>, ?\w\[\]]*\s+(\w+)\s*\(\s*(FML(?:Pre|Post)?InitializationEvent)\s+\w+', text):
        line = _line(text, match.start())
        result["diagnostics"].append({"severity": "info", "code": "loader_lifecycle", "feature": match.group(1), "loader": "forge-legacy", "event": match.group(2), "evidence": [evidence(path, (line, line), "forge-legacy-source:Mod.EventHandler", class_name=class_name, method=match.group(1), confidence=1.0)]})

    registrations = [
        (r'GameRegistry\.registerItem\s*\([^,]+,\s*"([a-z0-9_./-]+)"', "item", "GameRegistry.registerItem"),
        (r'GameRegistry\.registerBlock\s*\([^,]+,\s*"([a-z0-9_./-]+)"', "block", "GameRegistry.registerBlock"),
        (r'GameRegistry\.registerTileEntity\s*\([^,]+,\s*"([a-z0-9_.:/-]+)"', "block_entity", "GameRegistry.registerTileEntity"),
        (r'EntityRegistry\.registerModEntity\s*\([^,]+,\s*"([a-z0-9_./-]+)"', "entity", "EntityRegistry.registerModEntity"),
    ]
    for pattern, kind, api in registrations:
        for match in re.finditer(pattern, text):
            identifier = match.group(1) if ":" in match.group(1) else f"{mod_id}:{match.group(1)}"
            line = _line(text, match.start())
            result["content"].append({"kind": kind, "identifier": identifier, "properties": {"loader": "forge-legacy", "registration_api": api}, "evidence": [evidence(path, (line, line), f"forge-legacy-source:{api}", class_name=class_name, confidence=.9)]})
    for index, match in enumerate(re.finditer(r'GameRegistry\.(addRecipe|addShapelessRecipe|addSmelting)\s*\(', text)):
        line = _line(text, match.start())
        result["content"].append({"kind": "recipe", "identifier": f"{mod_id}:inferred_{match.group(1).lower()}_{index}", "properties": {"loader": "forge-legacy", "registration_api": f"GameRegistry.{match.group(1)}", "identifier_inferred": True}, "evidence": [evidence(path, (line, line), f"forge-legacy-source:GameRegistry.{match.group(1)}", class_name=class_name, confidence=.6)]})

    event_map = {"PlayerInteractEvent": "block_interact", "LivingHurtEvent": "entity_hurt", "LivingDeathEvent": "entity_death", "TickEvent": "object_tick"}
    event_pattern = re.compile(r'@SubscribeEvent\s+public\s+\w+[<>, ?\w\[\]]*\s+(\w+)\s*\(\s*(?:[\w.]+\.)?(\w+)\s+\w+[^)]*\)', re.MULTILINE)
    for match in event_pattern.finditer(text):
        method, event_type = match.groups()
        line = _line(text, match.start())
        trigger = event_map.get(event_type, "object_tick")
        result["behaviors"].append({"id": f"{mod_id}:forge_event/{method}", "owner": {"kind": "mod", "identifier": mod_id}, "trigger": {"type": trigger}, "conditions": [], "actions": [], "stateReads": [], "stateWrites": [], "feedback": [], "presentationRequirements": [], "evidence": [evidence(path, (line, line), "forge-legacy-source:SubscribeEvent", class_name=class_name, method=method, confidence=.7)], "confidence": .7, "diagnostics": [{"severity": "info", "code": "event_body_unresolved", "message": f"Forge event subscription for {event_type} is proven; handler behavior requires deeper data-flow analysis."}]})

    channels: dict[str, str] = {}
    for match in re.finditer(r'(\w+)\s*=\s*NetworkRegistry\.INSTANCE\.newSimpleChannel\s*\(\s*"([^"]+)"', text):
        channels[match.group(1)] = match.group(2)
    for index, match in enumerate(re.finditer(r'(\w+)\.registerMessage\s*\(\s*([^,]+),\s*([^,]+),\s*(\d+)\s*,\s*Side\.(CLIENT|SERVER)', text)):
        variable, handler, message, discriminator, side = match.groups()
        line = _line(text, match.start())
        result["networking"].append({"id": f"{mod_id}:{channels.get(variable, variable)}_{discriminator}", "direction": "server_to_client" if side == "CLIENT" else "client_to_server", "trigger": "custom_packet", "payload": message.strip(), "authority": side.lower(), "action": handler.strip(), "replacement_strategy": None, "evidence": [evidence(path, (line, line), "forge-legacy-source:SimpleNetworkWrapper.registerMessage", class_name=class_name, confidence=.85)]})

    coremod_match = re.search(r'implements\s+IFMLLoadingPlugin\b|IClassTransformer\b', text)
    if coremod_match is not None:
        line = _line(text, coremod_match.start())
        result["diagnostics"].append({"severity": "error", "code": "unsupported_hook", "feature": f"forge_coremod_source:{class_name or path}", "reason": "Forge coremod/class-transformer behavior requires manual reconstruction for Bedrock.", "evidence": [evidence(path, (line, line), "forge-legacy-source:coremod", class_name=class_name, confidence=1.0)]})
    return result


def _bytecode_evidence(archive: Path, fact: dict[str, Any], rule: str, confidence: float = .68) -> dict[str, Any]:
    return {"source_file": fact.get("source_file"), "class": fact.get("class"), "method": fact.get("method"), "field": None, "start_line": None, "end_line": None, "ast_node_type": None, "bytecode_location": f"{fact.get('class')}#{fact.get('method') or '<class>'}", "resource_path": None, "registration_path": None, "extraction_rule": rule, "analyzer_version": "forge-legacy-bytecode/1.0.0", "confidence": confidence, "source_mode": "bytecode-javap", "conflicting_evidence": [], "human_override_provenance": None}


def analyze_facts(archive: Path, facts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Lower loader-neutral facts for supported Forge 1.7.10 surfaces."""
    result: dict[str, list[dict[str, Any]]] = {key: [] for key in ("content", "behaviors", "state", "presentation", "ui", "networking", "diagnostics")}
    by_class: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        if fact.get("class"):
            by_class.setdefault(str(fact["class"]), []).append(fact)
    registration = {
        ("cpw.mods.fml.common.registry.GameRegistry", "registerItem"): "item",
        ("cpw.mods.fml.common.registry.GameRegistry", "registerBlock"): "block",
        ("cpw.mods.fml.common.registry.GameRegistry", "registerTileEntity"): "block_entity",
        ("cpw.mods.fml.common.registry.EntityRegistry", "registerModEntity"): "entity",
    }
    for class_name, rows in by_class.items():
        ordered = sorted(rows, key=lambda row: int(row.get("instruction_line") or 0))
        constants: list[str] = []
        channel = "network"
        mod_candidates = [str(row["value"]) for row in rows if row["fact_type"] == "constant" and re.fullmatch(r"[a-z][a-z0-9_.-]+", str(row["value"])) and "legacy" in str(row["value"])]
        mod_id = next((value for value in mod_candidates if value.startswith("authentic_")), mod_candidates[0] if mod_candidates else "forge_mod")
        for row in ordered:
            if row["fact_type"] == "constant":
                constants.append(str(row["value"]))
                continue
            if row["fact_type"] == "class" and "cpw.mods.fml.relauncher.IFMLLoadingPlugin" in row.get("interfaces", []):
                result["diagnostics"].append({"severity": "error", "code": "unsupported_hook", "feature": f"forge_coremod_source:{class_name.rsplit('.', 1)[-1]}", "reason": "Forge coremod/class-transformer behavior requires manual reconstruction for Bedrock.", "evidence": [_bytecode_evidence(archive, row, "forge-legacy-bytecode:coremod", .72)]})
                continue
            if row["fact_type"] != "invoke":
                continue
            owner_value, name_value = row.get("owner"), row.get("name")
            if not isinstance(owner_value, str) or not isinstance(name_value, str):
                continue
            owner, name = owner_value, name_value
            kind = registration.get((owner, name))
            if kind:
                identifier = next((value for value in reversed(constants[-5:]) if re.fullmatch(r"[a-z0-9_.:/-]+", value)), None)
                if identifier:
                    if ":" not in identifier:
                        identifier = f"{mod_id}:{identifier}"
                    result["content"].append({"kind": kind, "identifier": identifier, "properties": {"loader": "forge-legacy", "registration_api": f"{owner.rsplit('.', 1)[-1]}.{name}"}, "evidence": [_bytecode_evidence(archive, row, f"forge-legacy-bytecode:{name}")]})
            if owner == "cpw.mods.fml.common.network.NetworkRegistry" and name == "newSimpleChannel" and constants:
                channel = constants[-1]
            if owner == "cpw.mods.fml.common.network.simpleimpl.SimpleNetworkWrapper" and name == "registerMessage":
                side = next((f.get("name") for f in reversed(ordered[:ordered.index(row)]) if f["fact_type"] == "field" and f.get("owner") == "cpw.mods.fml.relauncher.Side"), "SERVER")
                result["networking"].append({"id": f"{mod_id}:{channel}_0", "direction": "server_to_client" if side == "CLIENT" else "client_to_server", "trigger": "custom_packet", "payload": "bytecode-proven-message", "authority": str(side).lower(), "action": "bytecode-proven-handler", "replacement_strategy": None, "evidence": [_bytecode_evidence(archive, row, "forge-legacy-bytecode:SimpleNetworkWrapper.registerMessage", .68)]})
        # A method-level SubscribeEvent annotation plus its parameter descriptor
        # is sufficient to prove subscription and event kind, not body behavior.
        annotations = [row for row in rows if row["fact_type"] == "annotation" and str(row.get("annotation", "")).endswith("SubscribeEvent")]
        methods = [row for row in rows if row["fact_type"] == "method"]
        for index, annotation in enumerate(annotations):
            method = next((m for m in methods if m.get("name") == annotation.get("method")), None)
            method = method or next((m for m in methods if "LivingHurtEvent" in str(m.get("descriptor"))), methods[index] if index < len(methods) else None)
            if method:
                result["behaviors"].append({"id": f"{mod_id}:forge_event/{method['name']}", "owner": {"kind": "mod", "identifier": mod_id}, "trigger": {"type": "entity_hurt" if "LivingHurtEvent" in str(method.get("descriptor")) else "object_tick"}, "conditions": [], "actions": [], "stateReads": [], "stateWrites": [], "feedback": [], "presentationRequirements": [], "evidence": [_bytecode_evidence(archive, method, "forge-legacy-bytecode:SubscribeEvent", .62)], "confidence": .62, "diagnostics": [{"severity": "info", "code": "event_body_unresolved", "message": "Forge event subscription is proven from bytecode; handler body remains unresolved."}]})
    return result
