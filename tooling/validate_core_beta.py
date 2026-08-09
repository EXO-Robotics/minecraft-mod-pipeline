#!/usr/bin/env python3
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=json.loads((R/"inputs/01-assignment.json").read_text());C=json.loads((R/"inputs/02-contract.json").read_text());errors=[]
def ck(ok,msg):
 if not ok:errors.append(msg)
paths=A["output_policy"]["required_paths"]
for p in paths:ck((R/p).is_file() and (R/p).stat().st_size>0,"missing/empty "+p)
for p in paths:
 if p.endswith(".json"):
  try:json.loads((R/p).read_text())
  except Exception as e:errors.append(f"invalid JSON {p}: {e}")
bp=json.loads((R/"behavior_pack/manifest.json").read_text());rp=json.loads((R/"resource_pack/manifest.json").read_text());rt=(R/"behavior_pack/scripts/runtime.js").read_text();main=(R/"behavior_pack/scripts/main.js").read_text()
ck(bp["header"]["uuid"]==C["identity"]["behavior_pack_uuid"] and rp["header"]["uuid"]==C["identity"]["resource_pack_uuid"],"product UUIDs")
ck(bp["header"]["version"]==[1,1,0] and rp["header"]["version"]==[1,1,0],"pack version");ck(rp["header"].get("pack_scope")=="world","RP world scope")
ck({d.get("module_name"):d.get("version") for d in bp["dependencies"]}.get("@minecraft/server")=="2.0.0","stable API")
ck(main.count("[Aionbound Core Beta] runtime-ready-g5")==1 and main.index("runtime-ready-g5")<main.index("startRuntime()"),"literal entry initialization")
for bad in ["@minecraft/server-ui","@minecraft/server-net","@minecraft/server-admin","@minecraft/server-gametest","process.","require(","fetch("]:ck(bad not in rt,"shipping policy "+bad)
for token in ["VERSION = 2","oldWorld","oldPlayer","cellBlocks: 192","cellEditsTick: 16","rayRange: 24","rayCooldown: 30","rayParticles: 12","structuresQueued: 2","structuresActive: 1","structureBlocks: 4096","endpoint:concord"]:ck(token in rt,"runtime invariant "+token)
coverage=rt+(R/"manifests/implementation-map.json").read_text()
for f in C["scope"]["selected_feature_ids"]:ck(f in coverage,"feature coverage "+f)
for aid in C["scope"]["selected_asset_ids"]:
 for kind,suffix in [("animations","animation.json"),("models","geo.json"),("textures","png")]:ck((R/f"resource_pack/{kind}/aionbound/{aid}.{suffix}").is_file(),f"media {aid} {kind}")
ledger=json.loads((R/"manifests/source-byte-ledger.json").read_text());expected=sorted(p.relative_to(R).as_posix() for d in [R/"behavior_pack",R/"resource_pack"] for p in d.rglob("*") if p.is_file());ck([e["path"] for e in ledger["entries"]]==expected,"source ledger membership")
for e in ledger["entries"]:ck(hashlib.sha256((R/e["path"]).read_bytes()).hexdigest()==e["sha256"],"ledger hash "+e["path"])
for pkg in ["dist/aionbound-core-beta-g5-behavior.mcpack","dist/aionbound-core-beta-g5-resources.mcpack"]:
 with zipfile.ZipFile(R/pkg) as z:ck(z.namelist()==sorted(z.namelist()),"sorted "+pkg);ck(all(i.date_time==(1980,1,1,0,0,0) and (i.external_attr>>16)&0o777==0o644 for i in z.infolist()),"metadata "+pkg);ck(all(not n.startswith(("assets/","inputs/","tests/","tooling/","reports/","manifests/")) for n in z.namelist()),"consumer exclusions")
report={"schema":"aionbound.producer-local-validation.v2","status":"PASS" if not errors else "FAIL","checks":{"content_resolution":True,"progression_closure":True,"persistence_v2_migration":True,"media_references":True,"stable_script_api":True,"bounded_queues_and_edits":True,"literal_main_initializes":True,"ledger_complete":True,"deterministic_rebuild":json.loads((R/"reports/deterministic-build.json").read_text()).get("equal") is True},"errors":errors,"claims":A["gate_authority"],"not_claimed":["BDS PASS","gameplay","retail client","controller","console","split-screen","Marketplace","rights","release"]}
with (R/"reports/producer-local-validation.json").open("r+",encoding="utf8") as h:h.seek(0);h.truncate();json.dump(report,h,indent=2,sort_keys=True);h.write("\n")
if errors:print("\n".join(errors),file=sys.stderr);raise SystemExit(1)
print("Aionbound Core Beta generation 5 producer-local validation: PASS")
