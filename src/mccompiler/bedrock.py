from __future__ import annotations

import hashlib
import base64
import json
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Any

from .io import write_json
from .api_catalog import ApiCatalog
from .targets import get_target


TOOL_VERSION = "0.2.0"
ARCHIVE_NAME = "converted-mod.mcaddon"
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
UUID_NAMESPACE = uuid.UUID("c9383f7f-e377-5cf8-af37-2a34029b29b9")
GENERATABLE = {"DIRECT", "SCRIPTED_EQUIVALENT", "RECONSTRUCTED", "BEHAVIORAL_APPROXIMATION", "VISUAL_APPROXIMATION"}
PLACEHOLDER_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
EVENT_SYMBOLS = {
    "item_use": ("itemUse", "world.afterEvents.itemUse"),
    "item_use_on_block": ("playerInteractWithBlock", "world.afterEvents.playerInteractWithBlock"),
    "block_interact": ("playerInteractWithBlock", "world.afterEvents.playerInteractWithBlock"),
    "block_break": ("playerBreakBlock", "world.afterEvents.playerBreakBlock"),
    "entity_hit": ("entityHitEntity", "world.afterEvents.entityHitEntity"),
    "entity_hurt": ("entityHurt", "world.afterEvents.entityHurt"),
    "entity_death": ("entityDie", "world.afterEvents.entityDie"),
    "entity_spawn": ("entitySpawn", "world.afterEvents.entitySpawn"),
    "player_join": ("playerSpawn", "world.afterEvents.playerSpawn"),
    "projectile_impact": ("projectileHitEntity", "world.afterEvents.projectileHitEntity"),
}
SCHEDULED_TRIGGERS = {"object_tick", "scheduled_tick", "state_transition"}
COMMON_RUNTIME_SYMBOLS = {
    ("@minecraft/server", name) for name in {
        "ItemStack", "MolangVariableMap", "world.getDimension", "world.dynamicProperties",
        "system.run", "system.runTimeout", "Entity.location", "Entity.dimension", "Entity.typeId",
        "Entity.remove", "Entity.applyDamage", "Entity.getComponent", "Entity.addEffect",
        "Entity.removeEffect", "Entity.setDynamicProperty", "Entity.getDynamicProperty",
        "Entity.teleport", "Entity.applyImpulse", "Player.sendMessage", "Player.startItemCooldown",
        "Player.getItemCooldown", "Dimension.spawnEntity", "Dimension.createExplosion",
        "Dimension.playSound", "Dimension.spawnParticle", "Dimension.runCommand",
        "Dimension.spawnItem", "Block.location", "Block.dimension", "Block.typeId", "Block.setType",
        "EntityInventoryComponent.container", "Container.addItem", "Container.size",
        "Container.getItem", "Container.setItem", "EntityHealthComponent.currentValue",
        "EntityHealthComponent.effectiveMax", "EntityHealthComponent.setCurrentValue",
        "ItemDurabilityComponent.damage",
    }
}


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
    raw_target = ir.get("target")
    target = raw_target if isinstance(raw_target, dict) else {}
    for marker in target.get("version_markers", []):
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
        recipe_format = str(props.get("format_version", "1.26.0"))
        result = props.get("result", "minecraft:stone")
        result_item = result if ":" in str(result) else f"minecraft:{result}"
        result_data: dict[str, Any] = {"item": result_item}
        if int(props.get("count", 1)) != 1:
            result_data["count"] = int(props["count"])
        if props.get("recipe_type") == "shaped":
            pattern = props.get("pattern")
            key = props.get("key")
            if not isinstance(pattern, list) or not pattern or not all(isinstance(row, str) and 1 <= len(row) <= 3 for row in pattern) or len(pattern) > 3:
                raise ValueError(f"Shaped recipe {identifier} requires one to three pattern rows of at most three characters")
            if not isinstance(key, dict) or not key:
                raise ValueError(f"Shaped recipe {identifier} requires a nonempty key map")
            used = {character for row in pattern for character in row if character != " "}
            if used != set(key) or any(not isinstance(symbol, str) or len(symbol) != 1 or not isinstance(item, str) for symbol, item in key.items()):
                raise ValueError(f"Shaped recipe {identifier} key map must exactly cover one-character pattern symbols")
            ingredients = {symbol: {"item": item} for symbol, item in sorted(key.items())}
            unlock_items = sorted(set(str(item) for item in key.values()))
            body = {"description": {"identifier": identifier}, "tags": ["crafting_table"], "pattern": pattern, "key": ingredients, "unlock": [{"item": item} for item in unlock_items], "result": result_data}
            return f"recipes/{identifier.replace(':', '_')}.json", {"format_version": recipe_format, "minecraft:recipe_shaped": body}
        ingredient_items = [str(item) for item in props.get("ingredients", ["minecraft:stone"])]
        body = {"description": {"identifier": identifier}, "tags": ["crafting_table"], "ingredients": [{"item": item} for item in ingredient_items], "unlock": [{"item": item} for item in sorted(set(ingredient_items))], "result": result_data}
        return f"recipes/{identifier.replace(':', '_')}.json", {"format_version": recipe_format, "minecraft:recipe_shapeless": body}
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


def _projectile_definition(identifier: str, min_engine: list[int]) -> dict[str, Any]:
    return {"format_version": ".".join(map(str, min_engine)), "minecraft:entity": {"description": {"identifier": identifier, "is_spawnable": False, "is_summonable": True}, "component_groups": {}, "components": {"minecraft:type_family": {"family": ["converted_projectile"]}, "minecraft:collision_box": {"width": 0.25, "height": 0.25}, "minecraft:physics": {}, "minecraft:projectile": {"power": 1.0, "gravity": 0.05, "on_hit": {"remove_on_hit": {}}}}, "events": {}}}


def _script_modules(ir: dict[str, Any], plan: dict[str, Any], *, debug: bool) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str], list[dict[str, str]]]:
    index = _feature_index(plan)
    approved: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for behavior in sorted(ir.get("behaviors", []), key=lambda x: str(x.get("id"))):
        feature = index.get((f"behavior.{behavior.get('trigger', {}).get('type')}", str(behavior.get("id"))))
        (approved if _approved(feature, behavior) else rejected).append({**behavior, "classification": (feature or {}).get("classification", "UNPLANNED")})
    behavior_data = _canonical(approved)
    state_data = _canonical([x for x in ir.get("state", []) if x.get("evidence") or x.get("override_provenance")])
    ui_data = _canonical([x for x in ir.get("ui_intent", []) if x.get("evidence") or x.get("override_provenance")])
    owned_data = _canonical(sorted({str(x.get("identifier")) for x in ir.get("content", []) if x.get("kind") in {"item", "block", "entity"} and x.get("identifier")}))
    requirements: set[tuple[str, str]] = set(COMMON_RUNTIME_SYMBOLS)
    for behavior in approved:
        trigger = str((behavior.get("trigger") or {}).get("type"))
        if trigger in EVENT_SYMBOLS:
            requirements.add(("@minecraft/server", EVENT_SYMBOLS[trigger][1]))
        elif trigger in SCHEDULED_TRIGGERS:
            requirements.add(("@minecraft/server", "system.runInterval"))
            requirements.update({
                ("@minecraft/server", "world.afterEvents.playerInteractWithBlock"),
                ("@minecraft/server", "world.afterEvents.playerBreakBlock"),
                ("@minecraft/server", "world.afterEvents.entitySpawn"),
                ("@minecraft/server", "world.afterEvents.entityDie"),
                ("@minecraft/server", "system.currentTick"),
            })
        else:
            raise ValueError(f"unmapped required trigger: {trigger} ({behavior.get('id')})")
        if any(action.get("type") in {"update_persistent_state", "set_entity_phase"} for action in behavior.get("actions", [])):
            requirements.add(("@minecraft/server", "world.dynamicProperties"))
    if ui_data != "[]":
        requirements.update({("@minecraft/server-ui", name) for name in ("ActionFormData", "ActionFormData.title", "ActionFormData.body", "ActionFormData.button", "ActionFormData.show")})
    if debug:
        requirements.add(("@minecraft/server", "system.afterEvents.scriptEventReceive"))
    target = get_target(plan.get("target_profile"))
    catalog = ApiCatalog.load_default()
    catalogued = [requirement for requirement in requirements if requirement in catalog.symbols]
    uncatalogued = [{"module": module, "symbol": symbol, "reason": "emitted Script API use is absent from the stable symbol catalog"} for module, symbol in sorted(requirements - set(catalogued))]
    versions, api_evidence = catalog.resolve_versions(catalogued, marketplace=target.identifier == "MARKETPLACE_ADDON_STABLE")
    event_map = {trigger: signal for trigger, (signal, _) in EVENT_SYMBOLS.items()}
    modules: dict[str, Any] = {
        "scripts/main.js": "import { world, system } from '@minecraft/server';\nimport { registerGeneratedEvents, behaviors } from './events/generated.js';\nimport { startScheduler } from './runtime/scheduler.js';\nregisterGeneratedEvents();\nstartScheduler(behaviors);\nsystem.run(()=>{console.warn(`[mccompiler] runtime initialized behaviors=${behaviors.length}`);});\n",
        "scripts/events/generated.js": "import { world } from '@minecraft/server';\nimport { dispatch } from '../runtime/actions.js';\nimport { registerActive, unregisterActive } from '../runtime/scheduler.js';\nexport const behaviors = " + behavior_data + ";\nconst owned=new Set(" + owned_data + ");\nexport const eventMap=" + _canonical(event_map) + ";\nconst scheduled=new Set(['object_tick','scheduled_tick','state_transition']);\nconst key=b=>`${b.dimension.id}:${b.location.x}:${b.location.y}:${b.location.z}`;\nconst matches=(b,c)=>{if(!owned.has(b.owner.identifier))return true;const ids=[c.itemStack?.typeId,c.block?.typeId,c.entity?.typeId,c.hitEntity?.typeId,c.hurtEntity?.typeId,c.deadEntity?.typeId];return ids.includes(b.owner.identifier)};\nexport function registerGeneratedEvents(){for(const b of behaviors){if(scheduled.has(b.trigger.type))continue;world.afterEvents[eventMap[b.trigger.type]].subscribe(ctx=>{if(matches(b,ctx))dispatch(b,ctx)});}const ticking=behaviors.some(b=>scheduled.has(b.trigger.type));if(ticking){world.afterEvents.playerInteractWithBlock.subscribe(e=>registerActive(key(e.block),{block:e.block,source:e.player,owner:e.block.typeId}));world.afterEvents.playerBreakBlock.subscribe(e=>unregisterActive(key(e.block)));world.afterEvents.entitySpawn.subscribe(e=>registerActive(e.entity.id,{target:e.entity,owner:e.entity.typeId}));world.afterEvents.entityDie.subscribe(e=>unregisterActive(e.deadEntity.id));}}\n",
        "scripts/runtime/actions.js": """// Conservative dispatcher: only evidence-backed IR reaches this module.
import { world, system, ItemStack, MolangVariableMap } from '@minecraft/server';
import { openGeneratedForm } from '../ui/forms.js';
const actor=c=>c.source||c.player||c.damagingEntity;
const target=c=>c.hitEntity||c.hurtEntity||c.deadEntity||c.target;
function location(c,a,t){try{return a?.location||t?.location||c.block?.location||c.location||{x:0,y:0,z:0}}catch{return c.location||{x:0,y:0,z:0}}}
function dimension(c,a,t){try{return a?.dimension||t?.dimension||c.block?.dimension||world.getDimension('overworld')}catch{return c.block?.dimension||world.getDimension('overworld')}}
const stateOwner=c=>actor(c)||target(c)||world;
export function stateKey(behavior,c,key){const p=c.block?.location,d=c.block?.dimension?.id;const suffix=p?`${d}:${p.x}:${p.y}:${p.z}:${key}`:key;return `mccompiler:${behavior.owner.identifier}:${suffix}`.replace(/[^a-z0-9_.:-]/gi,'_')}
export function readState(behavior,c,key){return stateOwner(c).getDynamicProperty?.(stateKey(behavior,c,key))??0}
export function writeState(behavior,c,key,value){stateOwner(c).setDynamicProperty?.(stateKey(behavior,c,key),value)}
export function conditionPass(x,behavior,c){const a=actor(c),t=target(c);switch(x.type){case 'player_sneaking':return !!a?.isSneaking;case 'held_item_match':return c.itemStack?.typeId===x.identifier;case 'target_entity_match':return t?.typeId===x.identifier;case 'block_match':return c.block?.typeId===x.identifier;case 'dimension_match':return a?.dimension?.id===x.identifier;case 'random_probability':return Math.random()<(x.probability??1);case 'cooldown_ready':return (a?.getItemCooldown?.(x.category||behavior.id)||0)===0;case 'state_comparison':{const value=Number(readState(behavior,c,x.key));return x.operator==='>='?value>=x.value:x.operator==='>'?value>x.value:x.operator==='<='?value<=x.value:x.operator==='<'?value<x.value:value===x.value}case 'health_threshold':{const h=(t||a)?.getComponent?.('minecraft:health');if(!h)return false;const ratio=h.currentValue/h.effectiveMax;return (x.min_ratio_exclusive===undefined||ratio>x.min_ratio_exclusive)&&(x.max_ratio_inclusive===undefined||ratio<=x.max_ratio_inclusive)}case 'client_server_side':return x.side!=='client';case 'configuration_flag':return x.enabled!==false;case 'dependency_presence':return x.present!==false;default:return true;}}
export function conditionsPass(behavior,c){return (behavior.conditions||[]).every(x=>conditionPass(x,behavior,c))}
export function dispatch(behavior,c={}){if(!conditionsPass(behavior,c))return false;const a=actor(c),t=target(c),d=dimension(c,a,t),p=location(c,a,t);for(const x of behavior.actions||[]){if(x.condition&&!conditionPass(x.condition,behavior,c))continue;switch(x.type){case 'spawn_entity':d.spawnEntity(x.entity||'minecraft:pig',p);break;case 'spawn_projectile':{const e=d.spawnEntity(x.entity||'minecraft:snowball',p);e.applyImpulse?.(x.velocity||{x:0,y:0,z:1});break}case 'remove_entity':t?.remove?.();break;case 'create_explosion':d.createExplosion(p,x.power||1,{breaksBlocks:x.breaks_blocks??false,source:a});break;case 'damage':t?.applyDamage?.(x.amount||1);break;case 'heal':{const h=t?.getComponent?.('minecraft:health');h?.setCurrentValue?.(Math.min(h.effectiveMax,h.currentValue+(x.amount||1)));break}case 'apply_effect':(t||a)?.addEffect?.(x.effect||'speed',x.duration||20,{amplifier:x.amplifier||0});break;case 'remove_effect':(t||a)?.removeEffect?.(x.effect||'speed');break;case 'play_sound':d.playSound(x.sound||'random.orb',p);break;case 'spawn_particles':d.spawnParticle(x.particle||'minecraft:basic_flame_particle',p,new MolangVariableMap());break;case 'set_block':case 'replace_block':c.block?.setType?.(x.block||'minecraft:stone');break;case 'break_block':c.block?.setType?.('minecraft:air');break;case 'place_structure':d.runCommand?.(`structure load ${x.structure||'mccompiler:placeholder'} ${p.x} ${p.y} ${p.z}`);break;case 'teleport':a?.teleport?.(x.location||p,{dimension:d});break;case 'apply_velocity':a?.applyImpulse?.(x.velocity||{x:0,y:0,z:0});break;case 'modify_item_durability':{const durability=c.itemStack?.getComponent?.('minecraft:durability');if(durability)durability.damage=Math.max(0,durability.damage+(x.amount||1));break}case 'add_item':{const item=new ItemStack(x.item||'minecraft:stone',x.amount||1);const bag=a?.getComponent?.('minecraft:inventory')?.container;if(bag)bag.addItem(item);else d.spawnItem(item,{x:p.x,y:p.y+1,z:p.z});break}case 'remove_item':{const bag=a?.getComponent?.('minecraft:inventory')?.container;if(bag)for(let i=0;i<bag.size;i++){const item=bag.getItem(i);if(item?.typeId===(x.item||'minecraft:stone')){bag.setItem(i);break}}break}case 'update_persistent_state':{const current=Number(readState(behavior,c,x.key||behavior.id));const value=x.operation==='increment'?current+(x.amount||1):x.operation==='decrement'?current-(x.amount||1):(x.value??1);writeState(behavior,c,x.key||behavior.id,value);break}case 'start_cooldown':a?.startItemCooldown?.(x.category||behavior.id,x.ticks||20);break;case 'set_entity_phase':(t||a)?.setDynamicProperty?.('mccompiler:phase',x.value||1);console.warn(`[mccompiler] phase ${behavior.id} -> ${x.value||1}`);break;case 'trigger_behavior':system.run(()=>dispatch({...behavior,id:x.behavior||behavior.id,actions:x.actions||[]},c));break;case 'send_player_feedback':a?.sendMessage?.(x.message||behavior.id);break;case 'open_interaction_ui':if(a)system.run(()=>openGeneratedForm(a,x.ui||behavior.id));break;case 'schedule_delayed_action':system.runTimeout(()=>dispatch({...behavior,actions:x.actions||[]},c),x.ticks||1);break;default:console.warn(`[mccompiler] unresolved runtime action ${x.type} in ${behavior.id}`);break;}}return true;}
""",
        "scripts/runtime/state.js": "export const stateRequirements = " + state_data + ";\nexport function stateKey(id){return `mccompiler:${id.replace(/[^a-z0-9_.-]/gi,'_')}`;}\n",
        "scripts/runtime/scheduler.js": "import { system } from '@minecraft/server';\nimport { dispatch } from './actions.js';\nconst active=new Map();let cursor=0;const TICK_BUDGET=32;\nexport function registerActive(id,context){active.set(id,{id,context,lastSeen:system.currentTick});}\nexport function unregisterActive(id){active.delete(id);}\nconst invalid=e=>{try{return e.context.target&&e.context.target.isValid===false}catch{return true}};\nexport function startScheduler(behaviors){const ticking=behaviors.filter(b=>['object_tick','scheduled_tick','state_transition'].includes(b.trigger.type));if(!ticking.length)return;system.runInterval(()=>{const entries=[...active.values()];if(!entries.length)return;let used=0;while(used<Math.min(TICK_BUDGET,entries.length)){const entry=entries[cursor%entries.length];cursor=(cursor+1)%entries.length;if(invalid(entry)){active.delete(entry.id);continue}for(const b of ticking){if(entry.context.owner!==b.owner.identifier)continue;const phase=(b.actions||[]).find(x=>x.type==='set_entity_phase')?.value;if(phase&&entry.context.target?.getDynamicProperty?.('mccompiler:phase')===phase)continue;dispatch(b,entry.context);}used++;}for(const [id,e] of active){if(system.currentTick-e.lastSeen>72000||invalid(e))active.delete(id);}},1);}\n",
        "scripts/ui/forms.js": (("import { ActionFormData } from '@minecraft/server-ui';\nexport const forms = " + ui_data + ";\nexport async function openGeneratedForm(player,id){const f=forms.find(x=>x.id===id);if(!f)throw new Error(`[mccompiler] missing generated form ${id}`);const form=new ActionFormData().title(f.title||id).body(f.purpose||'');for(const c of f.controls||[])form.button(String(c));return form.show(player);}\n") if ui_data != "[]" else "export const forms=[];\nexport async function openGeneratedForm(_player,id){throw new Error(`[mccompiler] form unavailable ${id}`);}\n"),
        "scripts/README.md": "Generated modules are deterministic. Unsupported and evidence-free behavior is intentionally omitted.\n",
        "tests/behavior-plan.json": {"approved": [x.get("id") for x in approved], "omitted": [{"id": x.get("id"), "reason": "unsupported, unplanned, or missing evidence"} for x in rejected]},
    }
    if debug:
        modules["scripts/tests/contracts.js"] = "import { world, system } from '@minecraft/server';\nimport { dispatch } from '../runtime/actions.js';\nexport function registerRuntimeTestCommands(behaviors){system.afterEvents.scriptEventReceive.subscribe(e=>{if(e.id!=='mccompiler:test')return;const b=behaviors.find(v=>v.id===e.message);if(!b)return;const p={x:0,y:100,z:0};dispatch(b,{source:e.sourceEntity,location:p});});}\n"
        modules["scripts/main.js"] += "import { registerRuntimeTestCommands } from './tests/contracts.js';\nregisterRuntimeTestCommands(behaviors);\n"
    modules["scripts/runtime/actions.js"] = modules["scripts/runtime/actions.js"].replace(
        "else d.spawnItem(item,{x:p.x,y:p.y+1,z:p.z});break",
        "else d.spawnItem(item,{x:p.x,y:p.y+1,z:p.z});console.warn(`[mccompiler] item output ${x.item||'minecraft:stone'} behavior=${behavior.id}`);break",
    )
    modules["scripts/runtime/actions.js"] = modules["scripts/runtime/actions.js"].replace(
        "export function readState(behavior,c,key){return stateOwner(c).getDynamicProperty?.(stateKey(behavior,c,key))??0}",
        "export function readState(behavior,c,key){try{return stateOwner(c).getDynamicProperty?.(stateKey(behavior,c,key))??0}catch{console.warn('[mccompiler] unavailable state owner');return 0}}",
    ).replace(
        "export function writeState(behavior,c,key,value){stateOwner(c).setDynamicProperty?.(stateKey(behavior,c,key),value)}",
        "export function writeState(behavior,c,key,value){try{stateOwner(c).setDynamicProperty?.(stateKey(behavior,c,key),value)}catch{console.warn('[mccompiler] unavailable state owner')}}",
    )
    modules["scripts/runtime/scheduler.js"] = modules["scripts/runtime/scheduler.js"].replace(
        "const invalid=e=>{try{return e.context.target&&e.context.target.isValid===false}catch{return true}};",
        "const invalid=e=>{try{const t=e.context.target;if(!t)return false;const p=t.location;if(p&&(p.y<-64||p.y>320))return true;t.getDynamicProperty?.('mccompiler:phase');return false}catch{return true}};",
    )
    return modules, api_evidence, versions, uncatalogued


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


def _resource_content(ir: dict[str, Any], rp: Path, namespace: str) -> list[dict[str, Any]]:
    """Generate complete, visibly-placeholder RP contracts for reconstructed content."""
    items = [_identifier(str(x.get("identifier")), namespace) for x in ir.get("content", []) if x.get("kind") == "item"]
    blocks = [_identifier(str(x.get("identifier")), namespace) for x in ir.get("content", []) if x.get("kind") == "block"]
    entities = [_identifier(str(x.get("identifier")), namespace) for x in ir.get("content", []) if x.get("kind") == "entity"]
    entities += [str(a.get("entity")) for b in ir.get("behaviors", []) for a in b.get("actions", []) if a.get("type") == "spawn_projectile" and a.get("entity")]
    entities = sorted(set(entities))
    placeholders: list[dict[str, Any]] = []
    pack_key = f"mccompiler_{namespace}"
    item_data, terrain_data, block_data = {}, {}, {}
    for identifier in items:
        short = identifier.split(":", 1)[1]
        texture = f"textures/mccompiler/{namespace}/item_{short}"
        item_data[identifier] = {"textures": texture}
        path = rp / f"{texture}.png"; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(PLACEHOLDER_PNG)
        placeholders.append({"owner": identifier, "kind": "texture", "path": path.relative_to(rp.parent).as_posix(), "reason": "source binary absent"})
    for identifier in blocks:
        short = identifier.split(":", 1)[1]
        texture = f"textures/mccompiler/{namespace}/block_{short}"
        terrain_data[identifier] = {"textures": texture}
        block_data[identifier] = {"sound": "stone", "textures": identifier}
        path = rp / f"{texture}.png"; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(PLACEHOLDER_PNG)
        placeholders.append({"owner": identifier, "kind": "texture", "path": path.relative_to(rp.parent).as_posix(), "reason": "source binary absent"})
    if item_data: _write(rp / "textures/item_texture.json", {"resource_pack_name": f"{namespace}_resources", "texture_name": "atlas.items", "texture_data": item_data})
    if terrain_data: _write(rp / "textures/terrain_texture.json", {"resource_pack_name": f"{namespace}_resources", "texture_name": "atlas.terrain", "texture_data": terrain_data})
    if block_data: _write(rp / "blocks.json", {"format_version": [1, 1, 0], **block_data})
    geometry = {"format_version": "1.12.0", "minecraft:geometry": [{"description": {"identifier": f"geometry.{pack_key}.generated", "texture_width": 16, "texture_height": 16, "visible_bounds_width": 2, "visible_bounds_height": 2, "visible_bounds_offset": [0, 1, 0]}, "bones": [{"name": "root", "pivot": [0, 0, 0], "cubes": [{"origin": [-4, 0, -4], "size": [8, 8, 8], "uv": [0, 0]}]}]}]}
    if entities:
        _write(rp / "models/entity/generated.geo.json", geometry)
        _write(rp / "render_controllers/generated.render_controllers.json", {"format_version": "1.8.0", "render_controllers": {f"controller.render.{pack_key}.generated": {"geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]}}})
        _write(rp / "animations/generated.animation.json", {"format_version": "1.8.0", "animations": {f"animation.{pack_key}.idle": {"loop": True, "animation_length": 1.0}}})
        _write(rp / "animation_controllers/generated.controller.json", {
            "format_version": "1.10.0",
            "animation_controllers": {
                f"controller.animation.{pack_key}.idle": {
                    "initial_state": "default",
                    "states": {"default": {"animations": [f"animation.{pack_key}.idle"]}},
                }
            },
        })
    for identifier in entities:
        short = identifier.split(":", 1)[1]; texture = f"textures/mccompiler/{namespace}/entity_{short}"
        path = rp / f"{texture}.png"; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(PLACEHOLDER_PNG)
        _write(rp / f"entity/{identifier.replace(':', '_')}.entity.json", {"format_version": "1.10.0", "minecraft:client_entity": {"description": {"identifier": identifier, "materials": {"default": "entity_alphatest"}, "textures": {"default": texture}, "geometry": {"default": f"geometry.{pack_key}.generated"}, "animations": {"idle": f"animation.{pack_key}.idle"}, "animation_controllers": [{"idle": f"controller.animation.{pack_key}.idle"}], "render_controllers": [f"controller.render.{pack_key}.generated"], "spawn_egg": {"base_color": "#777777", "overlay_color": "#55AAFF"}}}})
        placeholders.append({"owner": identifier, "kind": "texture", "path": path.relative_to(rp.parent).as_posix(), "reason": "source binary absent"})
    lang = []
    for identifier in items: lang.append(f"item.{identifier}.name={identifier.split(':', 1)[1].replace('_', ' ').title()}")
    for identifier in blocks: lang.append(f"tile.{identifier}.name={identifier.split(':', 1)[1].replace('_', ' ').title()}")
    for identifier in entities: lang.append(f"entity.{identifier}.name={identifier.split(':', 1)[1].replace('_', ' ').title()}")
    if lang: _write(rp / "texts/en_US.lang", "\n".join(lang) + "\n"); _write(rp / "texts/languages.json", ["en_US"])
    _write(rp / "sounds/sound_definitions.json", {"format_version": "1.14.0", "sound_definitions": {}})
    return placeholders


def _zip_deterministic(root: Path, archive: Path, *, consumer_only: bool | None = None) -> None:
    if consumer_only is None:
        try:
            plan = json.loads((root / "reports/conversion-plan.json").read_text(encoding="utf-8"))
            consumer_only = get_target(plan.get("target_profile")).production
        except (OSError, json.JSONDecodeError, ValueError, AttributeError):
            consumer_only = False
    if consumer_only:
        members = sorted(p for folder in (root / "behavior_pack", root / "resource_pack") for p in folder.rglob("*") if p.is_file())
    else:
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
    for name in ("behavior_pack", "resource_pack", "tests", "reports"):
        output_section = output / name
        if output_section.exists():
            shutil.rmtree(output_section)
        output_section.mkdir(parents=True)
    for old in (output / "generated.mcaddon", output / ARCHIVE_NAME):
        if old.exists(): old.unlink()
    namespace, seed = _identity(ir, plan)
    min_engine, version = _target_min_version(ir), [0, 2, 0]
    ids = {role: _uuid(seed, role) for role in ("bp", "bp-data", "bp-script", "rp", "rp-data")}
    target_profile = get_target(plan.get("target_profile"))
    bp, rp = output / "behavior_pack", output / "resource_pack"
    bp_manifest: dict[str, Any] = {"format_version": 2, "header": {"name": f"{namespace} reconstructed behavior", "description": "Deterministic output from minecraft-compiler-baseline", "uuid": ids["bp"], "version": version, "min_engine_version": min_engine}, "modules": [{"type": "data", "uuid": ids["bp-data"], "version": version}], "dependencies": [{"uuid": ids["rp"], "version": version}], "metadata": {"authors": ["minecraft-compiler-baseline"], "generated_with": {"minecraft-compiler-baseline": [TOOL_VERSION]}}}
    _write(rp / "manifest.json", {"format_version": 2, "header": {"name": f"{namespace} reconstructed resources", "description": "Deterministic output from minecraft-compiler-baseline", "uuid": ids["rp"], "version": version, "min_engine_version": min_engine, "pack_scope": "world"}, "modules": [{"type": "resources", "uuid": ids["rp-data"], "version": version}], "dependencies": [{"uuid": ids["bp"], "version": version}], "metadata": {"authors": ["minecraft-compiler-baseline"], "generated_with": {"minecraft-compiler-baseline": [TOOL_VERSION]}}})
    index = _feature_index(plan)
    generated, omitted = [], []
    for content in sorted(ir.get("content", []), key=lambda x: (str(x.get("kind")), str(x.get("identifier")))):
        kind, raw = str(content.get("kind")), str(content.get("identifier"))
        feature = index.get((f"content.{kind}", raw))
        properties = dict(content.get("properties") or {})
        if kind == "entity" and any(
            behavior.get("owner", {}).get("identifier") == raw and behavior.get("trigger", {}).get("type") == "state_transition"
            for behavior in ir.get("behaviors", [])
        ):
            properties.setdefault("health", 200)
        native = _native_content(kind, _identifier(raw, namespace), properties, min_engine)
        if _approved(feature, content) and native and feature is not None:
            rel, data = native
            path = bp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data) if isinstance(data, bytes) else _write(path, data)
            generated.append({"id": raw, "kind": kind, "path": f"behavior_pack/{rel}", "classification": feature["classification"], "evidence": content.get("evidence", [])})
        else:
            omitted.append({"id": raw, "kind": kind, "classification": (feature or {}).get("classification", "UNPLANNED"), "reason": "unsupported content kind, unsupported strategy, or missing evidence"})
    projectile_evidence: dict[str, list[dict[str, Any]]] = {}
    for behavior in ir.get("behaviors", []):
        for action in behavior.get("actions", []):
            if action.get("type") == "spawn_projectile" and action.get("entity"):
                projectile_evidence.setdefault(str(action["entity"]), []).extend(behavior.get("evidence", []))
    for identifier, evidence_rows in sorted(projectile_evidence.items()):
        rel = f"entities/{identifier.replace(':', '_')}.json"
        _write(bp / rel, _projectile_definition(identifier, min_engine))
        generated.append({"id": identifier, "kind": "projectile", "path": f"behavior_pack/{rel}", "classification": "RECONSTRUCTED", "evidence": evidence_rows})
    modules: dict[str, Any] = {}
    api_evidence: list[dict[str, Any]] = []
    module_versions: dict[str, str] = {}
    uncatalogued_symbols: list[dict[str, str]] = []
    if target_profile.scripts:
        candidate_modules, api_evidence, module_versions, uncatalogued_symbols = _script_modules(ir, plan, debug=target_profile.debug_content)
        has_script_features = bool(json.loads(candidate_modules["tests/behavior-plan.json"])["approved"] if isinstance(candidate_modules["tests/behavior-plan.json"], str) else candidate_modules["tests/behavior-plan.json"]["approved"]) or bool(module_versions)
        if has_script_features:
            modules = candidate_modules
            bp_manifest["modules"].append({"type": "script", "language": "javascript", "entry": "scripts/main.js", "uuid": ids["bp-script"], "version": version})
            bp_manifest["dependencies"].extend({"module_name": name, "version": value} for name, value in sorted(module_versions.items()))
    _write(bp / "manifest.json", bp_manifest)
    custom_modules = [module for override in ir.get("applied_overrides", []) for module in override.get("custom_script_modules", [])]
    custom_imports = "".join(f"import './{str(module['destination']).removeprefix('scripts/')}';\n" for module in custom_modules)
    if custom_modules and not target_profile.scripts:
        raise ValueError(f"target profile {target_profile.identifier} prohibits custom script modules")
    if modules and custom_imports:
        modules["scripts/main.js"] = custom_imports + modules["scripts/main.js"]
    for rel, value in modules.items():
        if rel.startswith("scripts/"):
            _write(bp / rel, value)
            if target_profile.debug_content:
                _write(output / rel, value)  # development-only inspectable mirror
        else:
            _write(output / rel, value)
    for module in custom_modules:
        destination = str(module["destination"])
        _write(bp / destination, module["source"])
        if target_profile.debug_content:
            _write(output / destination, module["source"])
    if not (output / "tests/behavior-plan.json").exists():
        approved_ids: list[dict[str, Any]] = []
        omitted_ids: list[dict[str, Any]] = []
        feature_index = _feature_index(plan)
        for behavior in ir.get("behaviors", []):
            feature = feature_index.get((f"behavior.{behavior.get('trigger', {}).get('type')}", str(behavior.get("id"))))
            row = {"id": behavior.get("id"), "reason": "target profile does not emit scripts"}
            (approved_ids if target_profile.scripts and _approved(feature, behavior) else omitted_ids).append(row)
        _write(output / "tests/behavior-plan.json", {"approved": [row["id"] for row in approved_ids], "omitted": omitted_ids})
    assets = _copy_assets(ir, output)
    placeholders = _resource_content(ir, rp, namespace)
    _write(rp / "_source_asset_map.json", assets)
    feature_report = [{"id": x.get("id"), "kind": x.get("kind"), "classification": x.get("classification"), "scores": x.get("scores"), "evidence": x.get("evidence", []), "limitations": (x.get("capability") or {}).get("limitations", [])} for x in plan.get("features", [])]
    _write(output / "reports" / "modir.json", ir)
    _write(output / "reports" / "conversion-plan.json", plan)
    _write(output / "reports" / "provenance.json", {"schema_version": "1.0.0", "features": feature_report, "generated_content": generated})
    _write(output / "reports" / "api-usage.json", {"schema_version": "1.0.0", "target_profile": target_profile.identifier, "complete": not uncatalogued_symbols, "resolved_modules": module_versions, "symbols": api_evidence, "uncatalogued_symbols": uncatalogued_symbols})
    _write(output / "reports" / "unsupported-and-approximations.json", {"unsupported": [x for x in feature_report if x["classification"] in {"UNSUPPORTED", "MANUAL_REDESIGN"}] + omitted, "approximations": [x for x in feature_report if "APPROXIMATION" in str(x["classification"])] + placeholders})
    _write(output / "reports" / "conversion-report.md", _report(ir, plan, namespace, generated, omitted, assets))
    manifest = {"schema_version": "1.0.0", "generator": {"name": "minecraft-compiler-baseline", "version": TOOL_VERSION}, "determinism": {"seed_sha256": seed, "uuid_scheme": "UUID5", "archive_order": "lexicographic", "archive_timestamp": "1980-01-01T00:00:00Z"}, "packs": {"behavior": ids["bp"], "resource": ids["rp"]}, "generated": generated, "omitted": omitted, "plan_feature_ids": [x.get("id") for x in plan.get("features", [])]}
    _write(output / "conversion-manifest.json", manifest)
    report_json = {
        "schema_version": "1.0.0", "result": "generated_pending_runtime_validation",
        "input": {"metadata": ir.get("metadata"), "loader_versions": [{"id": x.get("id"), "loader": x.get("loader"), "version": x.get("version")} for x in ir.get("mods", [])], "source_mode": sorted({e.get("source_mode") for b in ir.get("behaviors", []) for e in b.get("evidence", []) if e.get("source_mode")})},
        "dependency_graph": ir.get("dependency_graph"), "content_inventory": ir.get("content"),
        "behavior_inventory": [{"id": b.get("id"), "trigger": b.get("trigger"), "actions": b.get("actions"), "fingerprint": b.get("fingerprint"), "confidence": b.get("confidence"), "evidence": b.get("evidence")} for b in ir.get("behaviors", [])],
        "strategies": feature_report, "generated_files": sorted(p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()),
        "direct": [x["id"] for x in feature_report if x["classification"] == "DIRECT"],
        "scripted_equivalents": [x["id"] for x in feature_report if x["classification"] == "SCRIPTED_EQUIVALENT"],
        "approximations": [x for x in feature_report if "APPROXIMATION" in str(x["classification"])] + placeholders,
        "manual_redesign": [x for x in feature_report if x["classification"] == "MANUAL_REDESIGN"],
        "unsupported": [x for x in feature_report if x["classification"] == "UNSUPPORTED"],
        "performance_risks": [x for x in feature_report if float((x.get("scores") or {}).get("performance_risk", 0)) >= .4],
        "experimental_api_usage": [], "licensing_notes": [x.get("licensing_note") for x in ir.get("applied_overrides", []) if x.get("licensing_note")],
        "validation": {"static": "pending validator", "integration": "pending validator", "runtime": "not-run"},
        "fidelity_scores": plan.get("scores"),
        "remaining_human_tasks": [x.get("id") for x in feature_report if (x.get("scores") or {}).get("human_review_required")],
    }
    _write(output / "reports" / "conversion-report.json", report_json)
    _zip_deterministic(output, output / ARCHIVE_NAME, consumer_only=target_profile.production)
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
