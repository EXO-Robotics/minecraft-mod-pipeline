from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11 is the baseline runtime.
    tomllib = None

from .io import read_json, relaxed_json, version_list
from .ir import empty_ir
from .semantics import analyze_java, attach_fingerprints
from .frontends.jar_bytecode import class_constant_evidence
from .frontends.javap_analyzer import analyze_archive


CONTENT_DIRS = {
    "recipes": "/recipes/",
    "loot_tables": "/loot_tables/",
    "tags": "/tags/",
    "worldgen": "/worldgen/",
    "structures": "/structures/",
    "entities": "/entities/",
    "blocks": "/blocks/",
    "items": "/items/",
    "features": "/features/",
    "spawn_rules": "/spawn_rules/",
    "trading": "/trading/",
}

ASSET_DIRS = {
    "models": "/models/",
    "textures": "/textures/",
    "sounds": "/sounds/",
    "particles": "/particles/",
    "animations": "/animations/",
    "render_controllers": "/render_controllers/",
    "lang": "/lang/",
}


class ArchiveView:
    def __init__(self, path: Path):
        self.path = path
        self.is_archive = path.is_file() and (path.suffix.lower() in {".jar", ".zip", ".mrpack"})
        self._zip: zipfile.ZipFile | None = None
        if self.is_archive:
            self._zip = zipfile.ZipFile(path)

    def close(self) -> None:
        if self._zip:
            self._zip.close()

    def entries(self) -> list[str]:
        if self._zip:
            return sorted(name for name in self._zip.namelist() if not name.endswith("/"))
        return sorted(p.relative_to(self.path).as_posix() for p in self.path.rglob("*") if p.is_file())

    def read_bytes(self, entry: str) -> bytes:
        if self._zip:
            return self._zip.read(entry)
        return (self.path / entry).read_bytes()

    def read_text(self, entry: str) -> str | None:
        try:
            return self.read_bytes(entry).decode("utf-8")
        except (OSError, UnicodeDecodeError, KeyError):
            return None

    def sha256(self) -> str:
        digest = hashlib.sha256()
        for entry in self.entries():
            digest.update(entry.encode("utf-8"))
            digest.update(self.read_bytes(entry))
        return digest.hexdigest()


def _json_text(view: ArchiveView, path: str) -> Any | None:
    text = view.read_text(path)
    if text is None:
        return None
    try:
        return relaxed_json(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _dependency(item: Any, optional: bool = False) -> dict[str, Any] | None:
    if isinstance(item, str):
        return {"id": item, "version": None, "optional": optional}
    if not isinstance(item, dict):
        return None
    dep_id = item.get("modId") or item.get("mod_id") or item.get("id") or item.get("name")
    if not dep_id:
        return None
    return {
        "id": str(dep_id),
        "version": item.get("version") or item.get("versionRange") or item.get("version_range"),
        "optional": bool(item.get("optional", optional)),
        "kind": item.get("type") or item.get("kind"),
    }


def _metadata(view: ArchiveView) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mods: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []

    fabric = "fabric.mod.json"
    data = _json_text(view, fabric)
    if isinstance(data, dict):
        mod_id = data.get("id") or view.path.stem
        deps = []
        for key, optional in (("depends", False), ("recommends", True), ("suggests", True), ("conflicts", True)):
            values = data.get(key, {})
            if isinstance(values, dict):
                deps.extend({"id": k, "version": v, "optional": optional, "kind": key} for k, v in values.items())
            elif isinstance(values, list):
                deps.extend(d for d in (_dependency(v, optional) for v in values) if d)
        mods.append({
            "id": mod_id,
            "name": data.get("name") or mod_id,
            "version": data.get("version"),
            "loader": "fabric",
            "dependencies": deps,
            "metadata": {"environment": data.get("environment"), "entrypoints": sorted((data.get("entrypoints") or {}).keys())},
        })
        evidence.append({"path": fabric, "kind": "fabric.mod.json"})

    quilt = "quilt.mod.json"
    data = _json_text(view, quilt)
    if isinstance(data, dict):
        loader = data.get("quilt_loader") if isinstance(data.get("quilt_loader"), dict) else data
        mod_id = loader.get("id") or view.path.stem
        deps = []
        for value in loader.get("depends", []) or []:
            if isinstance(value, dict):
                dep_id = value.get("id") or value.get("versions", {}).get("id")
                if dep_id:
                    deps.append({"id": dep_id, "version": value.get("versions"), "optional": False})
        mods.append({"id": mod_id, "name": loader.get("metadata", {}).get("name", mod_id), "version": loader.get("version"), "loader": "quilt", "dependencies": deps, "metadata": {}})
        evidence.append({"path": quilt, "kind": "quilt.mod.json"})

    for filename, loader in (("META-INF/mods.toml", "forge"), ("META-INF/neoforge.mods.toml", "neoforge")):
        text = view.read_text(filename)
        if not text or tomllib is None:
            continue
        try:
            parsed = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            continue
        mod_entries = parsed.get("mods") if isinstance(parsed.get("mods"), list) else []
        dependency_table = parsed.get("dependencies", {})
        for mod in mod_entries:
            if not isinstance(mod, dict):
                continue
            mod_id = mod.get("modId") or mod.get("mod_id") or view.path.stem
            deps: list[dict[str, Any]] = []
            if isinstance(dependency_table, dict):
                rows = dependency_table.get(mod_id, [])
                if isinstance(rows, dict):
                    rows = [rows]
                if isinstance(rows, list):
                    deps.extend(d for d in (_dependency(row) for row in rows) if d)
            mods.append({"id": mod_id, "name": mod.get("displayName") or mod_id, "version": mod.get("version"), "loader": loader, "dependencies": deps, "metadata": {"loader_version": mod.get("loaderVersion"), "description": mod.get("description")}})
        evidence.append({"path": filename, "kind": filename.rsplit("/", 1)[-1]})

    info = "mcmod.info"
    data = _json_text(view, info)
    if isinstance(data, dict):
        data = [data]
    if isinstance(data, list):
        for mod in data:
            if isinstance(mod, dict):
                mod_id = mod.get("modid") or mod.get("modId") or view.path.stem
                deps = [{"id": dep, "version": None, "optional": False} for dep in mod.get("dependencies", []) if isinstance(dep, str)]
                mods.append({"id": mod_id, "name": mod.get("name") or mod_id, "version": mod.get("version"), "loader": "forge-legacy", "dependencies": deps, "metadata": {}})
        evidence.append({"path": info, "kind": info})

    if not mods:
        mods.append({"id": re.sub(r"[^a-z0-9_]+", "_", view.path.stem.lower()).strip("_") or "unknown_mod", "name": view.path.stem, "version": None, "loader": "unknown", "dependencies": [], "metadata": {}})
    return mods, evidence


def _modpack_metadata(view: ArchiveView) -> dict[str, Any] | None:
    data = _json_text(view, "manifest.json")
    if isinstance(data, dict) and ("modLoaders" in data or "minecraft" in data and "files" in data):
        return {"format": "curseforge", "name": data.get("name"), "version": data.get("version"), "minecraft": data.get("minecraft"), "mod_loaders": data.get("modLoaders"), "file_count": len(data.get("files", []))}
    data = _json_text(view, "modrinth.index.json")
    if isinstance(data, dict):
        return {"format": "modrinth", "name": data.get("name"), "version_id": data.get("versionId"), "dependencies": data.get("dependencies", {}), "file_count": len(data.get("files", []))}
    data = _json_text(view, "modpack.json")
    if isinstance(data, dict) and isinstance(data.get("mods"), list):
        return {"format": "mccompiler-directory", "name": data.get("id"), "version": data.get("version"), "mods": data["mods"], "load_order": data.get("load_order", [])}
    return None


def _source_signals(view: ArchiveView, entries: list[str]) -> dict[str, int]:
    signals = Counter()
    for entry in entries:
        lower = entry.lower()
        if lower.endswith(".java"):
            text = view.read_text(entry) or ""
            tests = {
                "registration_calls": r"register(\w*)\s*\(",
                "event_annotations": r"@(SubscribeEvent|EventBusSubscriber|EventHandler)",
                "tick_hooks": r"(serverTick|onTick|tick\s*\(|TickEvent)",
                "item_interactions": r"(useOn|use\s*\(|onItemUse|InteractionResult)",
                "block_interactions": r"(onBlockActivated|useWithoutItem|use\s*\(.*Block)",
                "damage_hooks": r"(hurt\s*\(|LivingHurtEvent|DamageSource)",
                "network_hooks": r"(Packet|payload|CustomPacket|SimpleChannel|registerMessage)",
                "mixin_injections": r"@(Inject|Redirect|ModifyArg|ModifyVariable|Overwrite)",
                "ui_hooks": r"(Screen|Menu|ContainerScreen|ScreenHandler|Widget)",
                "reflection": r"(Class\.forName|Method\.invoke|Field\.get|Reflection)",
            }
            for name, pattern in tests.items():
                signals[name] += len(re.findall(pattern, text))
        if any(token in lower for token in ("/screen/", "/menu/", "/gui/", "containerscreen", "screenhandler")):
            signals["ui_hooks"] += 1
        if "mixin" in lower or lower.endswith("mixins.json") or "/mixins/" in lower:
            signals["mixin_injections"] += 1
        if "network" in lower or "packet" in lower:
            signals["network_hooks"] += 1
        if "tileentity" in lower or "blockentity" in lower:
            signals["tile_entities"] += 1
    return dict(sorted(signals.items()))


def _inventory(view: ArchiveView) -> dict[str, Any]:
    entries = view.entries()
    counts = Counter()
    namespaces = {"assets": set(), "data": set()}
    examples: defaultdict[str, list[str]] = defaultdict(list)
    for entry in entries:
        parts = entry.split("/")
        if len(parts) >= 3 and parts[0] in namespaces:
            namespaces[parts[0]].add(parts[1])
        lower = "/" + entry.lower().replace("\\", "/") + "/"
        for kind, marker in CONTENT_DIRS.items():
            if marker in lower:
                counts[kind] += 1
                if len(examples[kind]) < 5:
                    examples[kind].append(entry)
        for kind, marker in ASSET_DIRS.items():
            if marker in lower:
                counts[kind] += 1
                if len(examples[kind]) < 5:
                    examples[kind].append(entry)
    counts["java_sources"] = sum(e.lower().endswith(".java") for e in entries)
    counts["class_files"] = sum(e.lower().endswith(".class") for e in entries)
    counts["configs"] = sum(e.lower().startswith("config/") or "/config/" in e.lower() or e.lower().endswith((".toml", ".properties")) for e in entries)
    counts["total_files"] = len(entries)
    flags = set()
    lower_entries = [e.lower() for e in entries]
    special_inventory = {
        "mixins": sorted(e for e in entries if "mixin" in e.lower()),
        "access_transformers": sorted(e for e in entries if "access_transformer" in e.lower() or e.lower().endswith("accesstransformer.cfg")),
        "coremods": sorted(e for e in entries if "coremod" in e.lower()),
        "data_generators": sorted(e for e in entries if "datagen" in e.lower() or "data_generator" in e.lower()),
        "configuration": sorted(e for e in entries if "/config/" in f"/{e.lower()}" or e.lower().endswith((".toml", ".properties"))),
        "scripts": sorted(e for e in entries if e.lower().endswith((".js", ".kts", ".groovy", ".zs"))),
        "native_libraries": sorted(e for e in entries if e.lower().endswith((".dll", ".so", ".dylib", ".jnilib"))),
        "client_only": sorted(e for e in entries if any(token in e.lower() for token in ("/client/", "clientonly", "clientside"))),
        "server_only": sorted(e for e in entries if any(token in e.lower() for token in ("/server/", "serveronly", "serverside"))),
        "cross_mod_integrations": sorted(e for e in entries if any(token in e.lower() for token in ("/compat/", "/integration/", "/integrations/"))),
    }
    if any("mixins" in e or e.endswith("mixin.json") for e in lower_entries): flags.add("mixins")
    if any("access_transformer" in e or e.endswith("accesstransformer.cfg") for e in lower_entries): flags.add("access_transformers")
    if any("coremod" in e or "js" in Path(e).suffix.lower() and "core" in e.lower() for e in lower_entries): flags.add("coremods")
    if any(re.search(r"(?:^|/)(?:gui|screen|screens|menu|menus)(?:/|$)", e) for e in lower_entries): flags.add("custom_gui")
    if any("network" in e or "packet" in e for e in lower_entries): flags.add("network_packets")
    if any("renderer" in e or "render" in e or "/models/" in e for e in lower_entries): flags.add("client_rendering")
    if any("tileentity" in e or "blockentity" in e for e in lower_entries): flags.add("tile_entities")
    source_signals = _source_signals(view, entries)
    for signal, flag in (("mixin_injections", "mixins"), ("network_hooks", "network_packets"), ("ui_hooks", "custom_gui"), ("tile_entities", "tile_entities")):
        if source_signals.get(signal): flags.add(flag)
    return {"file_count": len(entries), "namespaces": {k: sorted(v) for k, v in namespaces.items()}, "content_counts": dict(sorted(counts.items())), "examples": dict(examples), "special_inventory": special_inventory, "risk_flags": sorted(flags), "source_signals": source_signals}


def _bedrock_target(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(root), "server_properties": {}, "version_markers": [], "active_packs": {"behavior": [], "resource": []}}
    properties = root / "data" / "server.properties"
    if properties.exists():
        for raw in properties.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in raw and not raw.lstrip().startswith("#"):
                key, value = raw.split("=", 1)
                result["server_properties"][key.strip()] = value.strip()
    result["version_markers"] = sorted(p.name for p in (root / "data").glob("bedrock_server-*") if p.is_file())
    world = root / "data" / "worlds" / result["server_properties"].get("level-name", "Bedrock level")
    for kind, filename in (("behavior", "world_behavior_packs.json"), ("resource", "world_resource_packs.json")):
        refs = read_json(world / filename) or []
        if isinstance(refs, list):
            result["active_packs"][kind] = refs
    return result


def scan_path(input_path: str | Path, bedrock_server: str | Path | None = None) -> dict[str, Any]:
    path = Path(input_path).expanduser().resolve()
    ir = empty_ir(str(path))
    if bedrock_server:
        ir["target"] = _bedrock_target(Path(bedrock_server).expanduser().resolve())
    if not path.exists():
        ir["errors"] = [f"Input does not exist: {path}"]
        return ir

    root_view = ArchiveView(path)
    try:
        ir["input"].update({"kind": "archive" if root_view.is_archive else "directory", "sha256": root_view.sha256()})
        ir["modpack"] = _modpack_metadata(root_view)
    finally:
        root_view.close()

    sources: list[Path] = []
    if path.is_file():
        sources = [path]
    else:
        if ir["modpack"] and ir["modpack"].get("format") == "mccompiler-directory":
            sources = [((path / row["source"]).resolve()) for row in ir["modpack"]["mods"] if isinstance(row, dict) and row.get("source")]
            sources = [source for source in sources if source.exists()]
        else:
            sources = sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {".jar", ".zip", ".mrpack"})
        if not sources:
            sources = [path]

    aggregate_counts = Counter()
    aggregate_signals = Counter()
    aggregate_flags: set[str] = set()
    semantic = {key: [] for key in ("content", "behaviors", "state", "presentation", "ui", "networking", "diagnostics")}
    bytecode_evidence: list[dict[str, Any]] = []
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for source in sources:
        view = ArchiveView(source)
        try:
            mods, metadata_evidence = _metadata(view)
            inventory = _inventory(view)
            for mod in mods:
                record = {**mod, "source": {"path": str(source), "sha256": view.sha256()}, "metadata_evidence": metadata_evidence, "inventory": inventory}
                ir["mods"].append(record)
                nodes[mod["id"]] = {"id": mod["id"], "name": mod.get("name"), "version": mod.get("version"), "loader": mod.get("loader"), "source": str(source)}
                for dep in mod.get("dependencies", []):
                    edges.append({"from": mod["id"], "to": dep["id"], "optional": dep.get("optional", False), "version": dep.get("version")})
            aggregate_counts.update(inventory["content_counts"])
            aggregate_signals.update(inventory["source_signals"])
            aggregate_flags.update(inventory["risk_flags"])
            for entry in view.entries():
                if entry.lower().endswith(".java"):
                    extracted = analyze_java(entry, view.read_text(entry) or "")
                    for key, values in extracted.items():
                        semantic[key].extend(values)
                elif entry.lower().endswith(".class"):
                    bytecode_evidence.append(class_constant_evidence(entry, view.read_bytes(entry)))
            if source.is_file() and inventory["content_counts"].get("class_files") and not inventory["content_counts"].get("java_sources"):
                extracted = analyze_archive(source)
                for key, values in extracted.items():
                    semantic[key].extend(values)
        finally:
            view.close()
    ir["dependency_graph"] = {"nodes": sorted(nodes.values(), key=lambda n: n["id"]), "edges": edges}
    ir["aggregate"] = {"content_counts": dict(sorted(aggregate_counts.items())), "asset_counts": {k: aggregate_counts.get(k, 0) for k in ASSET_DIRS}, "risk_flags": sorted(aggregate_flags), "source_signals": dict(sorted(aggregate_signals.items()))}
    if path.is_dir() and ir["modpack"] is None:
        ir["modpack"] = {"format": "directory", "name": path.name, "file_count": len(sources)}
    ir["metadata"] = {"mods": [{k: v for k, v in mod.items() if k in {"id", "name", "version", "loader"}} for mod in ir["mods"]]}
    ir["dependencies"] = ir["dependency_graph"]["edges"]
    ir["content"] = semantic["content"]
    declarations: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in ir["content"]:
        declarations[(str(item.get("kind")), str(item.get("identifier")))].append(item)
    conflicts = []
    for (kind, identifier), items in sorted(declarations.items()):
        source_files = sorted({str(e.get("source_file")) for item in items for e in item.get("evidence", []) if e.get("source_file")})
        if len(items) > 1 and len(source_files) > 1:
            conflicts.append({
                "severity": "error", "code": "identifier_conflict", "feature": identifier,
                "kind": kind, "sources": source_files,
                "evidence": [e for item in items for e in item.get("evidence", [])],
            })
    ir["registries"] = [
        {"kind": kind, "identifier": identifier, "declaration_count": len(items),
         "conflicted": any(row["feature"] == identifier and row["kind"] == kind for row in conflicts),
         "evidence": [e for item in items for e in item.get("evidence", [])]}
        for (kind, identifier), items in sorted(declarations.items())
    ]
    ir["behaviors"] = semantic["behaviors"]
    ir["state"] = semantic["state"]
    ir["presentation_requirements"] = semantic["presentation"]
    ir["ui_intent"] = semantic["ui"]
    ir["networking_intent"] = semantic["networking"]
    ir["diagnostics"] = semantic["diagnostics"] + conflicts
    ir["unsupported_hooks"] = [d for d in semantic["diagnostics"] if d.get("code") == "unsupported_hook"]
    ir["bytecode_evidence"] = bytecode_evidence
    ir["assets"] = [{"kind": kind, "count": count, "evidence": ir["mods"][0].get("inventory", {}).get("examples", {}).get(kind, []) if ir["mods"] else []} for kind, count in ir["aggregate"]["asset_counts"].items() if count]
    attach_fingerprints(ir)
    return ir
