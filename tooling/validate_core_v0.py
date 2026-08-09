#!/usr/bin/env python3
import hashlib, json, os, subprocess, sys, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
A=json.loads((ROOT/"inputs/01-assignment.json").read_text()); C=json.loads((ROOT/"inputs/02-contract.json").read_text()); paths=A["output_policy"]["required_paths"]
MARKER="[Aionbound Core v0] runtime-ready-v1"; PACKAGES=["dist/aionbound-core-v0-g4-behavior.mcpack","dist/aionbound-core-v0-g4-resources.mcpack","dist/aionbound-core-v0-g4.mcaddon"]; errors=[]
def check(ok,msg):
 if not ok: errors.append(msg)
def digest(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
for p in paths: check((ROOT/p).exists() and (ROOT/p).stat().st_size>0,"missing/empty "+p)
for p in paths:
 if p.endswith(".json"):
  try: json.loads((ROOT/p).read_text())
  except Exception as e: errors.append(f"invalid JSON {p}: {e}")
bp=json.loads((ROOT/"behavior_pack/manifest.json").read_text()); rp=json.loads((ROOT/"resource_pack/manifest.json").read_text()); scripts=[m for m in bp["modules"] if m.get("type")=="script"]
check(bp["header"]["uuid"]=="2cf5e36d-e80f-5a00-9d46-adefbac35524","BP UUID"); check(rp["header"]["uuid"]=="3b13350a-2634-5083-948e-29f3fef39a45","RP UUID")
check(len(scripts)==1 and scripts[0].get("uuid")=="a84ee37d-6102-5c17-a730-c868647dbc5a","script module")
check(bp["header"]["version"]==rp["header"]["version"]==[1,0,3] and all(m.get("version")==[1,0,3] for m in bp["modules"]+rp["modules"]),"pack versions")
check(next(d["version"] for d in bp["dependencies"] if d.get("uuid")==rp["header"]["uuid"])==[1,0,3] and next(d["version"] for d in rp["dependencies"] if d.get("uuid")==bp["header"]["uuid"])==[1,0,3],"reciprocal dependency versions")
check({d.get("module_name"):d.get("version") for d in bp["dependencies"]}.get("@minecraft/server")=="2.0.0","stable API dependency")
entry_rel=PurePosixPath(scripts[0].get("entry","")) if scripts else PurePosixPath(); check(bool(str(entry_rel)) and not entry_rel.is_absolute() and ".." not in entry_rel.parts,"safe manifest entrypoint")
entry_path=ROOT/"behavior_pack"/entry_rel; entry=entry_path.read_text() if entry_path.is_file() else ""; runtime=(ROOT/"behavior_pack/scripts/runtime.js").read_text()
check(entry.count(MARKER)==1,"packaged entrypoint marker literal count"); check(runtime.count(MARKER)==0,"runtime marker literal absent"); check(entry.splitlines()[-2:]==[f'console.warn("{MARKER}");',"startRuntime();"],"marker immediately before runtime invocation")
for forbidden in ["@minecraft/server-ui","@minecraft/server-net","@minecraft/server-admin","@minecraft/server-gametest"]: check(forbidden not in runtime,"forbidden shipping import "+forbidden)
roots=(ROOT/"behavior_pack",ROOT/"resource_pack"); source_paths=sorted(p.relative_to(ROOT).as_posix() for root in roots for p in root.rglob("*") if p.is_file()); text="\n".join((ROOT/p).read_text(errors="ignore") for p in source_paths if not p.endswith(".png"))
coverage=text+(ROOT/"manifests/implementation-map.json").read_text()
for f in C["scope"]["selected_feature_ids"]: check(f in coverage,"feature coverage "+f)
check("@minecraft/server" in runtime,"stable server API import"); check("aionbound:" in text and "geometry.aionbound." in text and "animation.aionbound." in text,"namespace/reference closure")
for p in sorted((ROOT/"behavior_pack/feature_rules").glob("*.feature_rule.json")):
 rule=json.loads(p.read_text())["minecraft:feature_rules"]; check(rule["description"]["identifier"]=="aionbound:"+p.stem,"feature-rule filename identifier "+p.name)
for p in sorted((ROOT/"behavior_pack/recipes").glob("*.recipe.json")):
 recipe=json.loads(p.read_text())["minecraft:recipe_shapeless"]; ingredients={x["item"] for x in recipe["ingredients"]}; check(bool(recipe.get("unlock")) and all(x.get("item") in ingredients for x in recipe.get("unlock",[])),"recipe unlock ingredient "+p.name)
 if p.name=="stripvein_charge.recipe.json": check(ingredients=={"minecraft:paper","minecraft:gunpowder","minecraft:amethyst_shard"},"unique Stripvein recipe ingredients")
for p in list((ROOT/"behavior_pack/blocks").glob("*.json"))+list((ROOT/"behavior_pack/items").glob("*.json")): check("minecraft:custom_components" not in p.read_text(),"custom_components absent "+p.name)
ledger=json.loads((ROOT/"manifests/source-byte-ledger.json").read_text()); check([e["path"] for e in ledger["entries"]]==source_paths,"source ledger completeness")
check(ledger.get("complete") is True and len(ledger["entries"])==106,"106-entry complete source ledger")
for e in ledger["entries"]: check(digest(e["path"])==e["sha256"] and (ROOT/e["path"]).stat().st_size==e["size"],"ledger byte identity "+e["path"])
expected={PACKAGES[0]:[p.removeprefix("behavior_pack/") for p in source_paths if p.startswith("behavior_pack/")],PACKAGES[1]:[p.removeprefix("resource_pack/") for p in source_paths if p.startswith("resource_pack/")]}
for package,names_expected in expected.items():
 with zipfile.ZipFile(ROOT/package) as z:
  names=z.namelist(); prefix="behavior_pack" if "behavior" in package else "resource_pack"; check(names==names_expected,"exact sorted constituents "+package); check(all(i.date_time==(1980,1,1,0,0,0) and ((i.external_attr>>16)&0o777)==0o644 for i in z.infolist()),"archive metadata "+package); check(all(z.read(n)==(ROOT/prefix/n).read_bytes() for n in names),"constituent bytes "+package)
with zipfile.ZipFile(ROOT/PACKAGES[2]) as z:
 addon_names=["aionbound-core-v0-g4-behavior.mcpack","aionbound-core-v0-g4-resources.mcpack"]; check(z.namelist()==addon_names,"addon membership"); check(all(z.read(n)==(ROOT/"dist"/n).read_bytes() for n in addon_names),"addon constituent equality")
env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}; subprocess.run([sys.executable,str(ROOT/"tooling/build.py")],cwd=ROOT,check=True,env=env); first={p:digest(p) for p in PACKAGES}; subprocess.run([sys.executable,str(ROOT/"tooling/build.py")],cwd=ROOT,check=True,env=env); second={p:digest(p) for p in PACKAGES}; check(first==second,"two real builds equal")
report={"schema":"aionbound.producer-local-validation.v1","status":"PASS" if not errors else "FAIL","checks":{"json":True,"feature_rule_filename_identifier":not any("feature-rule" in e for e in errors),"recipe_unlock_data":not any("recipe unlock" in e for e in errors),"custom_components_absent":not any("custom_components" in e for e in errors),"manifest_declared_entrypoint_marker":not any("marker" in e for e in errors),"stable_api_policy":not any("API" in e or "import" in e for e in errors),"complete_membership":not any("membership" in e or "ledger" in e for e in errors),"deterministic_rebuild":first==second},"errors":errors,"claims":["IMPLEMENTED","STATIC_QUALIFIED","CANDIDATE_READY_FOR_INDEPENDENT_AUDIT"],"not_claimed":["BDS PASS","gameplay","retail client","controller","console","split-screen","Marketplace","rights","release"]}
with (ROOT/"reports/producer-local-validation.json").open("r+",encoding="utf-8") as h: h.seek(0); h.truncate(); json.dump(report,h,indent=2,sort_keys=True); h.write("\n")
if errors: print("\n".join(errors),file=sys.stderr); raise SystemExit(1)
print("Aionbound Core v0 generation 4 producer-local validation: PASS")
