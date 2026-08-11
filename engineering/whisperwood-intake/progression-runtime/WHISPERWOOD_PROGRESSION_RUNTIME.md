# Whisperwood Progression Runtime Scaffold

Status: **IMPLEMENTED — AUTHORITY-COMPLETE NON-LOOT SCOPE ONLY**

This slice wires two authored Whisperwood assembly anchors into the existing compositional interaction router and v4 player persistence.

## Implemented

- Interacting with the lodestone inside the authored `forest_waystone` assembly records the exact existing `landmark:forest_waystone` player stamp. Duplicate interaction is idempotent and the stamp survives a state-service restart.
- Interacting with the barrel inside the authored `broken_wagon` assembly records the exact existing `landmark:broken_wagon` player stamp. The catalog labels this as the approved `ww_to_ah` transition hook.
- Nearby authored block signatures distinguish these anchors from ordinary player-placed lodestones and barrels. Vanilla interaction is not canceled.
- Both handlers compose through the existing route action list; no early return suppresses adjacent discovery handlers.

## Deliberately withheld

The Creative authority approves the Waystone activation concept and the wagon's qualitative Ashen pointer, but it does not bind a teleport network contract, world-shared activation, exact rumor text, a new Ashen-rumor stamp, or a shipping map-scrap identity. Those elements remain absent. The wagon hook is therefore silent persistent scaffolding, not a claimed player-visible Ashen rumor feature.

No loot, reward item, boss behavior, new identifier, build, BDS run, or candidate operation is included.

## Evidence

Run:

`node --test engineering/whisperwood-intake/progression-runtime/test_whisperwood_progression_runtime.mjs`

The test proves exact catalog bindings, authored-signature discrimination, duplicate safety, persistence across service recreation, silence, compositional routing, and the withheld-scope boundary.
