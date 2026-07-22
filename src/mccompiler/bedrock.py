from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Any

from .io import write_json


TOOL_VERSION = "0.2.0"
ARCHIVE_NAME = "converted-mod.mcaddon"
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
UUID_NAMESPACE = uuid.UUID("c9383f7f-e377-5cf8-af37-2a34029b29b9")
GENERATABLE = {"DIRECT", "SCRIPTED_EQUIVALENT", "RECONSTRUCTED", "BEHAVIORAL_APPROXIMATION", "VISUAL_APPROXIMATION"}


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", (value or "converted_mod").lower()).strip("_") or "converted_mod"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value.replace("\r\n", "\n"), encoding="utf-8")
    else:
        path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _target_min_version(ir: dict[str, Any]) -> list[int]:
    for marker in (ir.get("target") or {}).get("version_markers", []):
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", str(marker))
        if match:
            return [int(x) for x in match.groups()]
    return [1, 21, 90]


def _identity(ir: dict[str, Any], plan: dict[str, Any]) -> tuple[str, str]:
    namespace = _safe_id(((ir.get("mods") or [{}])[0].get("id") or (ir.get("metadata") or {}).get("id") or "converted_mod"))
    # Input locations are deliberately excluded: identical semantics produce identical packs.
    semantic = {k: ir.get(k) for k in ("schema_version", "metadata", "dependencies", "content", "assets", "behaviors", "state", "presentation_requirements", "ui_intent", "networking_intent", "unsupported_hooks", "tests")}
    stable_plan = {k: v for k, v in plan.items() if k != "target"}
    return namespace, hashlib.sha256((_canonical(semantic) + _canonical(stable_plan)).encode()).hexdigest()


def _uuid(seed: str, role: str) -> str:
    return str(uuid.uuid5(UUID_NAMESPACE, f"{seed}:{role}"))


def _feature_index(plan: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(x.get("kind")), str(x.get("id"))): x for x in plan.get("features", [])}


def _approved(feature: dict[str, Any] | None, source: dict[str, Any]) -> bool:
    return bool(feature and feature.get("classification") in GENERATABLE and (source.get("evidence") or source.get("override_provenance") or feature.get("override")))


def _identifier(raw: str, namespace: str) -> str:
    return raw if ":" in raw else f"{namespace}:{_safe_id(raw)}"


def _nbt_name(name: str) -> bytes:
    raw = name.encode("utf-8")
    return len(raw).to_bytes(2, "little") + raw


def _empty_structure() -> bytes:
    """Minimal little-endian Bedrock structure NBT with a 1x1x1 air volume."""
    byte, integer, list_tag, compound, end = 1, 3, 9, 10, 0
    out = bytearray([compound, 0, 0])
    out += bytes([integer]) + _nbt_name("format_version") + (1).to_bytes(4, "little", signed=True)
    for name, values in (("size", (1, 1, 1)), ("structure_world_origin", (0, 0, 0))):
        out += bytes([list_tag]) + _nbt_name(name) + bytes([integer]) + len(values).to_bytes(4, "little", signed=True)
        for value in values: out += value.to_bytes(4, "little", signed=True)
    out += bytes([compound]) + _nbt_name("structure")
    out += bytes([list_tag]) + _nbt_name("block_indices") + bytes([list_tag]) + (2).to_bytes(4, "little", signed=True)
    for value in (-1, -1):
        out += bytes([integer]) + (1).to_bytes(4, "little", signed=True) + value.to_bytes(4, "little", signed=True)
    out += bytes([list_tag]) + _nbt_name("entities") + bytes([compound]) + (0).to_bytes(4, "little", signed=True)
    out += bytes([compound]) + _nbt_name("palette") + bytes([compound]) + _nbt_name("default")
    out += bytes([list_tag]) + _nbt_name("block_palette") + bytes([compound]) + (0).to_bytes(4, "little", signed=True)
    out += bytes([compound]) + _nbt_name("block_position_data") + bytes([end, end, end, end])
    return bytes(out)


def _native_content(kind: str, identifier: str, props: dict[str, Any], min_engine: list[int]) -> tuple[str, Any] | None:
    description = {"identifier": identifier}
    if kind == "item":
        return f"items/{identifier.replace(':', '_')}.json", {"format_version": ".".join(map(str, min_engine)), "minecraft:item": {"description": {**description, "menu_category": {"category": "items"}}, "components": {"minecraft:max_stack_size": int(props.get("max_stack_size", 64))}}}
    if kind == "block":
        return f"blocks/{identifier.replace(':', '_')}.json", {"format_version": ".".join(map(str, min_engine)), "minecraft:block": {"description": {**description, "menu_category": {"category": "construction"}}, "components": {"minecraft:destructible_by_mining": {"seconds_to_destroy": float(props.get("destroy_time", 1.0))}, "minecraft:destructible_by_explosion": {"explosion_resistance": float(props.get("explosion_resistance", 1.0))}}}}
    if kind in {"recipe", "crafting_recipe", "processing_recipe"}:
        result = props.get("result", "minecraft:stone")
        return f"recipes/{identifier.replace(':', '_')}.json", {"format_version": "1.20.10", "minecraft:recipe_shapeless": {"description": {"identifier": identifier}, "tags": ["crafting_table"], "ingredients": [{"item": x} for x in props.get("ingredients", ["minecraft:stone"])], "unlock": [{"item": "minecraft:stone"}], "result": {"item": result if ":" in str(result) else f"minecraft:{result}"}}}
    if kind in {"loot", "loot_table"}:
        return f"loot_tables/{identifier.replace(':', '/')}.json", {"pools": [{"rolls": 1, "entries": [{"type": "item", "name": props.get("item", "minecraft:stone"), "weight": 1}]}]}
    if kind == "entity":
        return f"entities/{identifier.replace(':', '_')}.json", {"format_version": ".".join(map(str, min_engine)), "minecraft:entity": {"description": {**description, "is_spawnable": True, "is_summonable": True}, "component_groups": {}, "components": {"minecraft:type_family": {"family": ["converted"]}, "minecraft:health": {"value": float(props.get("health", 20)), "max": float(props.get("health", 20))}}, "events": {}}}
    if kind == "spawn_rule":
        entity = props.get("entity", identifier)
        return f"spawn_rules/{identifier.replace(':', '_')}.json", {"format_version": "1.8.0", "minecraft:spawn_rules": {"description": {"identifier": entity, "population_control": "animal"}, "conditions": [{"minecraft:spawns_on_surface": {}, "minecraft:weight": {"default": 10}, "minecraft:herd": {"min_size": 1, "max_size": 1}}]}}
    if kind == "structure":
        return f"structures/{identifier.replace(':', '/')}.mcstructure", _empty_structure()
    return None


def _script_modules(ir: dict[str, Any], plan: dict[str, Any]) -> dict[str, str]:
    index = _feature_index(plan)
    approved = []
    rejected = []
    for behavior in sorted(ir.get("behaviors", []), key=lambda x: str(x.get("id"))):
        feature = index.get((f"behavior.{behavior.get('trigger', {}).get('type')}", str(behavior.get("id"))))
        (approved if _approved(feature, behavior) else rejected).append({**behavior, "classification": (feature or {}).get("classification", "UNPLANNED")})
    behavior_data = _canonical(approved)
    state_data = _canonical([x for x in ir.get("state", []) if x.get("evidence") or x.get("override_provenance")])
    ui_data = _canonical([x for x in ir.get("ui_intent", []) if x.get("evidence") or x.get("override_provenance")])
    return {
        "scripts/main.js": "import { world, system } from '@minecraft/server';\nimport { registerGeneratedEvents, behaviors } from './events/generated.js';\nimport { startScheduler } from './runtime/scheduler.js';\nregisterGeneratedEvents();\nstartScheduler();\nsystem.run(()=>{const key='mccompiler:runtime_boots';const boots=Number(world.getDynamicProperty(key)||0)+1;world.setDynamicProperty(key,boots);console.warn(`[mccompiler] runtime initialized behaviors=${behaviors.length} persistent_boot=${boots}`);});\n",
        "scripts/events/generated.js": "import { world } from '@minecraft/server';\nimport { dispatch } from '../runtime/actions.js';\nexport const behaviors = " + behavior_data + ";\nconst eventMap={item_use:'itemUse',item_use_on_block:'itemUseOn',block_break:'playerBreakBlock',entity_hit:'entityHitEntity',entity_hurt:'entityHurt',entity_death:'entityDie',player_join:'playerSpawn',projectile_impact:'projectileHitEntity'};\nexport function registerGeneratedEvents(){for(const b of behaviors){const e=world.afterEvents[eventMap[b.trigger.type]];if(e)e.subscribe(ctx=>dispatch(b,ctx));}}\n",
        "scripts/runtime/actions.js": "// Conservative dispatcher: only evidence-backed IR reaches this module.\nexport function dispatch(behavior,context){for(const action of behavior.actions||[]){switch(action.type){case 'send_player_feedback': context.source?.sendMessage?.(action.message||behavior.id); break; case 'apply_effect': context.source?.addEffect?.(action.effect||'speed',action.duration||20); break; case 'damage': context.hitEntity?.applyDamage?.(action.amount||1); break; default: break;}}}\n",
        "scripts/runtime/state.js": "export const stateRequirements = " + state_data + ";\nexport function stateKey(id){return `mccompiler:${id.replace(/[^a-z0-9_.-]/gi,'_')}`;}\n",
        "scripts/runtime/scheduler.js": "import { system } from '@minecraft/server';\nimport { behaviors } from '../events/generated.js';\nimport { dispatch } from './actions.js';\nconst ticking=behaviors.filter(b=>['object_tick','scheduled_tick'].includes(b.trigger.type));\nexport function startScheduler(){if(ticking.length)system.runInterval(()=>{for(const b of ticking)dispatch(b,{})},20);}\n",
        "scripts/ui/forms.js": "import { ActionFormData } from '@minecraft/server-ui';\nexport const forms = " + ui_data + ";\nexport async function openGeneratedForm(player,id){const f=forms.find(x=>x.id===id);if(!f)return;const form=new ActionFormData().title(f.title||id).body(f.purpose||'');for(const c of f.controls||[])form.button(String(c));return form.show(player);}\n",
        "scripts/README.md": "Generated modules are deterministic. Unsupported and evidence-free behavior is intentionally omitted.\n",
        "tests/behavior-plan.json": {"approved": [x.get("id") for x in approved], "omitted": [{"id": x.get("id"), "reason": "unsupported, unplanned, or missing evidence"} for x in rejected]},
    }


def _copy_assets(ir: dict[str, Any], output: Path) -> list[dict[str, str]]:
    mappings: list[dict[str, str]] = []
    for mod in sorted(ir.get("mods", []), key=lambda x: str(x.get("id"))):
        source = Path((mod.get("source") or {}).get("path", ""))
        if not source.is_file() or source.suffix.lower() not in {".jar", ".zip"}:
            continue
        with zipfile.ZipFile(source) as archive:
            for name in sorted(archive.namelist()):
                parts = name.split("/")
                if len(parts) < 4 or parts[0] != "assets" or parts[2] not in {"textures", "sounds"}:
                    continue
                dest = output / "resource_pack" / "_source_assets" / Path(*parts[1:])
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(name))
                mappings.append({"source": f"{source.name}:{name}", "destination": dest.relative_to(output).as_posix()})
    return mappings


def _zip_deterministic(root: Path, archive: Path) -> None:
    members = sorted(p for p in root.rglob("*") if p.is_file() and p != archive)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in members:
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def compile_bedrock(ir: dict[str, Any], plan: dict[str, Any], output_dir: str | Path) -> Path:
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name in ("behavior_pack", "resource_pack", "scripts", "tests", "reports"):
        target = output / name
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
    for old in (output / "generated.mcaddon", output / ARCHIVE_NAME):
        if old.exists(): old.unlink()
    namespace, seed = _identity(ir, plan)
    min_engine, version = _target_min_version(ir), [0, 2, 0]
    ids = {role: _uuid(seed, role) for role in ("bp", "bp-data", "bp-script", "rp", "rp-data")}
    script_api = (ir.get("target") or {}).get("script_api_version", "2.0.0")
    if isinstance(script_api, list): script_api = ".".join(map(str, script_api))
    bp, rp = output / "behavior_pack", output / "resource_pack"
    _write(bp / "manifest.json", {"format_version": 2, "header": {"name": f"{namespace} reconstructed behavior", "description": "Deterministic output from minecraft-compiler-baseline", "uuid": ids["bp"], "version": version, "min_engine_version": min_engine}, "modules": [{"type": "data", "uuid": ids["bp-data"], "version": version}, {"type": "script", "language": "javascript", "entry": "scripts/main.js", "uuid": ids["bp-script"], "version": version}], "dependencies": [{"uuid": ids["rp"], "version": version}, {"module_name": "@minecraft/server", "version": str(script_api)}, {"module_name": "@minecraft/server-ui", "version": str(script_api)}], "metadata": {"authors": ["minecraft-compiler-baseline"], "generated_with": {"minecraft-compiler-baseline": [TOOL_VERSION]}}})
    _write(rp / "manifest.json", {"format_version": 2, "header": {"name": f"{namespace} reconstructed resources", "description": "Deterministic output from minecraft-compiler-baseline", "uuid": ids["rp"], "version": version, "min_engine_version": min_engine}, "modules": [{"type": "resources", "uuid": ids["rp-data"], "version": version}], "metadata": {"authors": ["minecraft-compiler-baseline"], "generated_with": {"minecraft-compiler-baseline": [TOOL_VERSION]}}})
    index = _feature_index(plan)
    generated, omitted = [], []
    for content in sorted(ir.get("content", []), key=lambda x: (str(x.get("kind")), str(x.get("identifier")))):
        kind, raw = str(content.get("kind")), str(content.get("identifier"))
        feature = index.get((f"content.{kind}", raw))
        native = _native_content(kind, _identifier(raw, namespace), content.get("properties") or {}, min_engine)
        if _approved(feature, content) and native:
            rel, data = native
            path = bp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data) if isinstance(data, bytes) else _write(path, data)
            generated.append({"id": raw, "kind": kind, "path": f"behavior_pack/{rel}", "classification": feature["classification"], "evidence": content.get("evidence", [])})
        else:
            omitted.append({"id": raw, "kind": kind, "classification": (feature or {}).get("classification", "UNPLANNED"), "reason": "unsupported content kind, unsupported strategy, or missing evidence"})
    modules = _script_modules(ir, plan)
    for rel, value in modules.items():
        if rel.startswith("scripts/"):
            _write(bp / rel, value)
            _write(output / rel, value)  # inspectable source mirror outside the pack
        else:
            _write(output / rel, value)
    assets = _copy_assets(ir, output)
    _write(rp / "_source_asset_map.json", assets)
    feature_report = [{"id": x.get("id"), "kind": x.get("kind"), "classification": x.get("classification"), "scores": x.get("scores"), "evidence": x.get("evidence", []), "limitations": (x.get("capability") or {}).get("limitations", [])} for x in plan.get("features", [])]
    _write(output / "reports" / "provenance.json", {"schema_version": "1.0.0", "features": feature_report, "generated_content": generated})
    _write(output / "reports" / "unsupported-and-approximations.json", {"unsupported": [x for x in feature_report if x["classification"] in {"UNSUPPORTED", "MANUAL_REDESIGN"}] + omitted, "approximations": [x for x in feature_report if "APPROXIMATION" in str(x["classification"])]})
    _write(output / "reports" / "conversion-report.md", _report(ir, plan, namespace, generated, omitted, assets))
    manifest = {"schema_version": "1.0.0", "generator": {"name": "minecraft-compiler-baseline", "version": TOOL_VERSION}, "determinism": {"seed_sha256": seed, "uuid_scheme": "UUID5", "archive_order": "lexicographic", "archive_timestamp": "1980-01-01T00:00:00Z"}, "packs": {"behavior": ids["bp"], "resource": ids["rp"]}, "generated": generated, "omitted": omitted, "plan_feature_ids": [x.get("id") for x in plan.get("features", [])]}
    _write(output / "conversion-manifest.json", manifest)
    _zip_deterministic(output, output / ARCHIVE_NAME)
    return output / ARCHIVE_NAME


def _report(ir: dict[str, Any], plan: dict[str, Any], namespace: str, generated: list[dict[str, Any]], omitted: list[dict[str, Any]], assets: list[dict[str, str]]) -> str:
    scores = plan.get("scores", {})
    lines = [f"# Conversion report: `{namespace}`", "", f"Generated content: **{len(generated)}**; copied assets: **{len(assets)}**; omitted content: **{len(omitted)}**.", "", "## Fidelity", ""]
    for key in ("technical_similarity", "gameplay_fidelity", "visual_fidelity", "persistence_fidelity", "multiplayer_fidelity", "extraction_confidence"):
        lines.append(f"- {key.replace('_', ' ').title()}: **{float(scores.get(key, 0)):.0%}**")
    lines.extend(["", "## Strategy coverage", ""])
    for name, count in sorted((plan.get("strategy_counts") or {}).items()): lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Safety", "", "No executable behavior was generated without evidence or explicit override provenance.", "Unsupported and approximate features are listed in `reports/unsupported-and-approximations.json`.", "Runtime validation has not been implied by static generation.", ""])
    return "\n".join(lines)
