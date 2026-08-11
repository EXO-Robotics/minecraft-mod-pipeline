# Whisperwood Codex runtime events

Status: `TARGETED_LOCAL_SEMANTIC_PASS`

Base authority: integration commit `df13d014447dbf3586eab0f373d3a1172e55edb1` and `WHISPERWOOD_CODEX_IMPLEMENTATION_MAP.json` SHA-256 `d9c1f4c5ad4fbc66afa284da4d2bcc03424b22d6f43c49c5ec76d99198cbc9bf`.

## Implemented boundary

- The existing compositional block router now evaluates legacy stamps, exact Codex events, and block actions independently. A discovery does not suppress another discovery or action.
- Player interaction with the 10 integrated Whisperwood blocks and 10 integrated plants records their exact map-authorized complete discovery event.
- Player interaction with six map-authorized Whisperwood creatures records the exact partial observation event.
- Player-caused death records the exact complete event for the three creatures with explicit detail transitions and the four creatures whose primary discovery is defeat. Non-player deaths and the three creatures without a death transition do not advance the Codex.
- The existing Waykeeper interaction notice remains an independently composed entity action.
- The death subscription invokes Codex routing, the existing boss-death handler, and the existing Glasswing handler unconditionally in a stable order. No early return lets one handler suppress the others.
- Codex discovery remains silent. No guidance, reward, loot, UI, manifest, or asset changes were added.

The block-interaction signal is a bounded discovery hook requested for this integration slice. It is not evidence of a dedicated block-break, harvest, or recipe-crafting telemetry surface even when the canonical Creative event key ends in `harvested` or `crafted`.

## Evidence

```text
node --test tests/wave1_codex_runtime_events.test.mjs tests/wave1_codex_v4.test.mjs tests/g7_runtime_semantics.test.mjs
29 tests, 29 pass, 0 fail

python3 -m unittest engineering/whisperwood-intake/codex/test_whisperwood_codex_map.py -v
6 tests, 6 pass, 0 fail
```

Covered assertions include exact map parity, all 20 BP block identifiers, six observation routes, seven death routes, player-cause enforcement, duplicate-safe v4 persistence, no Codex chat output, legacy block-action composition, Waykeeper action preservation, and unconditional Codex/boss/Glasswing death-handler composition.

## Proof boundary

This is source-level and Node/Python semantic evidence. It does not prove Bedrock event delivery, block-break or recipe telemetry, natural encounter discoverability, UI, loot, BP/RP packaging, deterministic build, Stable BDS, Bedrock client behavior, multiplayer, console behavior, or candidate readiness.
