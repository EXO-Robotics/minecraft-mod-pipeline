import hashlib, json, unittest
from pathlib import Path
import author_skyreach_plants as a

class TestSkyreachPlants(unittest.TestCase):
    def test_exact_scope_and_native_bytes(self):
        self.assertEqual(len(a.ASSETS),10)
        for s in a.SPECS:
            root=a.evidence(s.asset); gp=a.REPO/f"resource_pack/models/aionbound/skyreach/{s.asset}.geo.json"; tp=a.REPO/f"resource_pack/textures/aionbound/skyreach/plants/{s.asset}.png"
            self.assertEqual(gp.read_bytes(),(root/"native-exports/pass-2.geo.json").read_bytes())
            self.assertEqual(tp.read_bytes(),(root/f"native-project/textures/{s.asset}.png").read_bytes())
    def test_blocks_are_stable_bounded_and_have_no_economy(self):
        for s in a.SPECS:
            document=json.loads((a.REPO/f"behavior_pack/blocks/{s.asset}.block.json").read_text()); self.assertEqual(document["format_version"],"1.21.80"); b=document["minecraft:block"]
            c=b["components"]; self.assertNotIn("minecraft:loot",c); self.assertNotIn("menu_category",b["description"]); self.assertNotIn("minecraft:custom_components",c)
    def test_ecology_is_bounded_and_regional(self):
        total=0
        for s in a.SPECS:
            r=json.loads((a.REPO/f"behavior_pack/feature_rules/sr_ecology_{s.asset}.feature_rule.json").read_text())["minecraft:feature_rules"]
            text=json.dumps(r); self.assertIn('"mountain"',text); self.assertIn('"hills"',text); self.assertIn('"ocean"',text); total+=s.iterations/s.denominator
        self.assertLessEqual(total,0.25)
    def test_report_and_generator_are_deterministic(self):
        files,report=a.build(); self.assertEqual(report["status"],"PASS_STATIC_SOURCE_BINDING"); self.assertFalse(report["constraints"]["loot_or_acquisition_added"])
        for p,b in files.items(): self.assertEqual(p.read_bytes(),b,p)
if __name__=="__main__": unittest.main()
