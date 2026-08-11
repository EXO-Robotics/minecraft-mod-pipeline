# Whisperwood Progression Runtime Scaffold

Status: **IMPLEMENTED — RATIFIED PROGRESSION AND THORN COURT ANCHOR**

This slice wires all ten authored Whisperwood anchors into the existing compositional interaction router, Codex registry v2, and schema-v4 player persistence.

## Implemented

- Interacting with the lodestone inside the authored `forest_waystone` assembly records the exact existing `landmark:forest_waystone` player stamp. Duplicate interaction is idempotent and the stamp survives a state-service restart.
- Interacting with the barrel inside the authored `broken_wagon` assembly records the exact existing `landmark:broken_wagon` player stamp. The catalog labels this as the approved `ww_to_ah` transition hook.
- The wagon activation completes the Codex-state Ashen rumor with the approved hint, “East wind smells like a fireplace that never goes out.” No map-scrap item is created.
- Interacting with the lodestone inside the authored `ancient_totem` assembly records `landmark:ancient_totem` and starts only the ratified Thorn Court arming sequence. Its nearby `hollow_wood` signature prevents ordinary lodestones and the forest waystone from starting the encounter.
- Rotation-aware authored block signatures distinguish anchors from ordinary player-placed lodestones and barrels. Vanilla interaction is not canceled.
- All handlers compose through the existing route action list; no early return suppresses adjacent discovery handlers.

## Deliberately withheld

The Creative authority does not bind a teleport network contract, world-shared activation, or a shipping map-scrap identity. Those elements remain absent. The rumor is deliberately represented only as compact Codex/structure state.

Loot and reward delivery are owned by the ratified economy and Thorn Court lanes. No build, BDS run, or candidate operation is included here.

## Evidence

Run:

`node --test engineering/whisperwood-intake/progression-runtime/test_whisperwood_progression_runtime.mjs`

The test proves exact catalog bindings, rotation-aware authored-signature discrimination, duplicate safety, persistence across service recreation, compositional routing, and the withheld-scope boundary.
