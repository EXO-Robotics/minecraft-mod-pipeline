import hashlib, json, os, subprocess, sys, unittest, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[1]; MARKER="[Aionbound Core v0] runtime-ready-v1"; PACKAGES=["dist/aionbound-core-v0-g4-behavior.mcpack","dist/aionbound-core-v0-g4-resources.mcpack","dist/aionbound-core-v0-g4.mcaddon"]
class CoreV0(unittest.TestCase):
 def test_contract_manifest_and_runtime(self):
  c=json.loads((ROOT/"inputs/02-contract.json").read_text()); bp=json.loads((ROOT/"behavior_pack/manifest.json").read_text()); rp=json.loads((ROOT/"resource_pack/manifest.json").read_text()); script=next(m for m in bp["modules"] if m.get("type")=="script"); entry_rel=PurePosixPath(script["entry"]); self.assertNotIn("..",entry_rel.parts)
  entry=(ROOT/"behavior_pack"/entry_rel).read_text(); runtime=(ROOT/"behavior_pack/scripts/runtime.js").read_text(); self.assertEqual(len(c["scope"]["selected_feature_ids"]),13); self.assertEqual(entry.count(MARKER)+runtime.count(MARKER),1); self.assertEqual(entry.splitlines()[-2:],[f'console.warn("{MARKER}");',"startRuntime();"]); self.assertIn("const SOFT",runtime); self.assertIn("CAPS.editsTick",runtime); self.assertNotIn("@minecraft/server-ui",runtime); self.assertEqual(bp["header"]["version"], [1,0,3]); self.assertEqual(rp["header"]["version"],[1,0,3]); self.assertTrue(all(m["version"]==[1,0,3] for m in bp["modules"]+rp["modules"])); self.assertEqual({d.get("module_name"):d.get("version") for d in bp["dependencies"]}.get("@minecraft/server"),"2.0.0")
 def test_repair_closure(self):
  for p in sorted((ROOT/"behavior_pack/feature_rules").glob("*.feature_rule.json")): self.assertEqual(json.loads(p.read_text())["minecraft:feature_rules"]["description"]["identifier"],"aionbound:"+p.stem)
  for p in sorted((ROOT/"behavior_pack/recipes").glob("*.recipe.json")):
   recipe=json.loads(p.read_text())["minecraft:recipe_shapeless"]; ingredients={x["item"] for x in recipe["ingredients"]}; self.assertTrue(recipe.get("unlock")); self.assertTrue(all(x.get("item") in ingredients for x in recipe["unlock"]));
   if p.name=="stripvein_charge.recipe.json": self.assertEqual(ingredients,{"minecraft:paper","minecraft:gunpowder","minecraft:amethyst_shard"})
  for p in list((ROOT/"behavior_pack/blocks").glob("*.json"))+list((ROOT/"behavior_pack/items").glob("*.json")): self.assertNotIn("minecraft:custom_components",p.read_text())
 def test_package_membership_and_two_real_builds(self):
  env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}; snapshots=[]
  for _ in range(2):
   subprocess.run([sys.executable,str(ROOT/"tooling/build.py")],cwd=ROOT,check=True,env=env); snapshots.append({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in PACKAGES})
  self.assertEqual(snapshots[0],snapshots[1])
  with zipfile.ZipFile(ROOT/PACKAGES[2]) as z:
   self.assertEqual(z.namelist(),["aionbound-core-v0-g4-behavior.mcpack","aionbound-core-v0-g4-resources.mcpack"])
   for name in z.namelist(): self.assertEqual(z.read(name),(ROOT/"dist"/name).read_bytes())
 def test_source_ledger_complete(self):
  ledger=json.loads((ROOT/"manifests/source-byte-ledger.json").read_text()); expected=sorted(p.relative_to(ROOT).as_posix() for root in (ROOT/"behavior_pack",ROOT/"resource_pack") for p in root.rglob("*") if p.is_file()); self.assertTrue(ledger["complete"]); self.assertEqual(len(ledger["entries"]),106); self.assertEqual([e["path"] for e in ledger["entries"]],expected)
  for entry in ledger["entries"]: self.assertEqual((hashlib.sha256((ROOT/entry["path"]).read_bytes()).hexdigest(),(ROOT/entry["path"]).stat().st_size),(entry["sha256"],entry["size"]))
if __name__=="__main__": unittest.main()
