import hashlib,json,subprocess,sys,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CoreBetaG5(unittest.TestCase):
 def test_manifest_policy(self):
  bp=json.loads((ROOT/"behavior_pack/manifest.json").read_text());rp=json.loads((ROOT/"resource_pack/manifest.json").read_text())
  self.assertEqual(bp["header"]["version"],[1,1,0]);self.assertEqual(rp["header"]["pack_scope"],"world")
  self.assertEqual({d.get("module_name"):d.get("version") for d in bp["dependencies"]}.get("@minecraft/server"),"2.0.0")
  self.assertEqual(bp["dependencies"][0]["uuid"],rp["header"]["uuid"]);self.assertEqual(rp["dependencies"][0]["uuid"],bp["header"]["uuid"])
 def test_runtime_public_edges_and_caps(self):
  r=(ROOT/"behavior_pack/scripts/runtime.js").read_text();m=(ROOT/"behavior_pack/scripts/main.js").read_text()
  self.assertEqual(m.count("[Aionbound Core Beta] runtime-ready-g5"),1);self.assertLess(m.index("runtime-ready-g5"),m.index("startRuntime()"))
  for token in ["oldWorld","oldPlayer","VERSION = 2","cellBlocks: 192","cellEditsTick: 16","rayRange: 24","rayCooldown: 30","rayParticles: 12","mountsWorld: 12","bossesWorld: 3","system.run(()=>useProgressBlock","endpoint:concord"]: self.assertIn(token,r)
  for bad in ["@minecraft/server-ui","@minecraft/server-net","@minecraft/server-admin","@minecraft/server-gametest","process.","require(","fetch("]:self.assertNotIn(bad,r)
 def test_progression_and_media_closure(self):
  r=(ROOT/"behavior_pack/scripts/runtime.js").read_text()
  for x in ["gloam","brine","vent","cinderglass","storm","abyss","boneplain","riftscar","twinbond","chrono_robo_sentinel","royal_moth_empress","basalt_behemoth","rift_colossus","ash_sovereign_wyrm","tide_empress_wyrm","trophy_concord_scale"]:self.assertIn(x,r)
  for aid in json.loads((ROOT/"inputs/02-contract.json").read_text())["scope"]["selected_asset_ids"]:
   for kind,suffix in [("animations","animation.json"),("models","geo.json"),("textures","png")]:self.assertTrue((ROOT/f"resource_pack/{kind}/aionbound/{aid}.{suffix}").is_file())
 def test_archive_determinism(self):
  target=ROOT/"dist/aionbound-core-beta-g5.mcaddon";before=hashlib.sha256(target.read_bytes()).hexdigest();subprocess.run([sys.executable,str(ROOT/"tooling/build.py")],cwd=ROOT,check=True);self.assertEqual(before,hashlib.sha256(target.read_bytes()).hexdigest())
  with zipfile.ZipFile(target) as z:self.assertEqual(z.namelist(),["aionbound-core-beta-g5-behavior.mcpack","aionbound-core-beta-g5-resources.mcpack"])
if __name__=="__main__":unittest.main()
