# Ashen representative native repair gate

Status: `PASS_NATIVE_REPAIR_GATE`

Authority: integration commit `0a55eee35c3206155cb8fd96fb40ba86ac17af4c`, tree `8da0fe27110cb8edccf71087982ac956e15fbcf6`.

The bounded seven-asset representative set was repaired and reopened twice in isolated Blockbench 5.1.6 over a loopback-only CDP endpoint. The native projects preserve the frozen packet's editable shape/UV signature and exact texture bytes, add true native locators at canonical packet transforms, and contain exactly the animation roles declared by each frozen brief.

The aggregate receipt records 7/7 passing assets, 20 brief-declared clips, 11 true native locators, 76 native screenshots, and zero captured warnings or errors. Every clip has a Blockbench timeline screenshot. Pass 1 and pass 2 native geometry and animation exports are canonically equivalent for every asset.

The packet static `.geo.json` exports are authority for exact locator transforms. They are generator-authored rather than Blockbench-codec-authored, so whole-file equality with native codec output is informational only. Shape and UV preservation are instead bound to stable before/after editable-project signatures; native export determinism is bound to canonical pass-1/pass-2 equality.

This is a native editable/codec repair gate only. It does not prove BP/RP integration, gameplay, BDS, Bedrock client behavior, multiplayer, physical PS4, Marketplace, or release readiness. Golden promotion remains withheld pending true-silhouette and player-scale fixed proof, independent originality/control comparison, and client visual review.

Run the deterministic checks with:

```sh
python3 engineering/native-assets/ashen/representative/build_representative_report.py
python3 -m unittest discover -s engineering/native-assets/ashen/representative -p 'test_*.py' -v
```
