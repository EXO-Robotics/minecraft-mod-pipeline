# Whisperwood equipment native repair B

Scope: exactly 13 Packet 006 assets — four Whisperwood armor pieces, five Whisperwood accessories, and four Whisperwood trophies.

Status: **BLOCKBENCH_NATIVE_PASS_ONLY**

Each copied editable source was normalized to `geometry.aionbound.<asset>`, rebound to a portable staged `textures/<asset>.png`, given a true native `effect` locator using the transform and parent from the canonical packet geometry export, and passed two native save-close-reopen/export cycles. Pass-1 and pass-2 geometry and animation exports are canonically equivalent for all 13 assets. Every native receipt records zero Blockbench warnings and errors.

The two briefs declaring role clips were authored through Blockbench's native animation API:

| Asset | Exact clip | Timeline proof |
|---|---|---|
| `moss_charm` | `animation.aionbound.moss_charm.idle_sway` | `evidence/moss_charm/screenshots/timeline-idle_sway-0.750.png` |
| `moon_sap_pendant` | `animation.aionbound.moon_sap_pendant.pulse` | `evidence/moon_sap_pendant/screenshots/timeline-pulse-1.200.png` |

All packet texture files remain exact 32×32 RGBA bytes. No texture was upscaled or resampled. The aggregate validator checks PNG signature, CRCs, complete decompression, dimensions/channels, source-byte hashes, namespaces, locator equivalence, exact declared clips, screenshot hashes, zero-warning receipts, and two-pass export equivalence.

Run:

```sh
python3 engineering/native-assets/whisperwood/equipment-b/validate_equipment_b.py
```

This evidence does not modify or prove BP/RP integration, gameplay behavior, loot, recipes, Bedrock client rendering, Stable BDS, physical PS4, or Marketplace acceptance.
