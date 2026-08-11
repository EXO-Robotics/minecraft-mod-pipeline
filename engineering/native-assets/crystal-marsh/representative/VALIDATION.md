# Crystal Marsh representative native repair gate

Status: `PASS_NATIVE_REPAIR_GATE`

Authority: integration commit `9235ff0fb375a025127888b618e2818994206d5a`, tree `b7d178ad9f1fc2a1581deb1dc3bb69eb82f3478d`.

The bounded seven-asset representative set was repaired and reopened twice in isolated Blockbench 5.1.6 over loopback-only CDP. The native projects preserve the frozen Packet 003 editable shape/UV signatures and exact texture bytes, normalize staged texture paths and public `aionbound` identifiers, add true native locators at canonical packet-export transforms, and contain exactly the animation roles declared by each frozen brief.

The aggregate receipt records 7/7 passing assets, 19 brief-declared clips, 10 true native locators, 75 native screenshots, seven labeled contact sheets, and zero captured warnings or errors. Every declared clip has a native Blockbench timeline capture. Pass 1 and pass 2 native geometry and animation exports are canonically equivalent for every asset.

Manual contact-sheet inspection confirms that all seven native captures are visible and class-distinct across orthographic, three-quarter, top, wireframe, atlas-underlay, and declared timeline views. This review does not elevate the packet art to final Golden promotion: true silhouette-only and player-scale proof, independent originality/control comparison, and Bedrock client visual review remain unrun.

The packet static `.geo.json` exports are authority for exact locator transforms. They are generator-authored rather than Blockbench-codec-authored, so whole-file equality with native codec output is informational only. Shape and UV preservation are bound to stable before/after editable-project signatures; native export determinism is bound to canonical pass-1/pass-2 equality.

This is native editable/codec repair evidence only. It does not prove BP/RP integration, gameplay, Creator Tools, BDS, Bedrock client behavior, multiplayer, physical PS4, Marketplace, or release readiness.

Run the deterministic checks with:

```sh
python3 engineering/native-assets/crystal-marsh/representative/build_contact_sheets.py
python3 engineering/native-assets/crystal-marsh/representative/build_representative_report.py
python3 -m unittest discover -s engineering/native-assets/crystal-marsh/representative -p 'test_*.py' -v
```
