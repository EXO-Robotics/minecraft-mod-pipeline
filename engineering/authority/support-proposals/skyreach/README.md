# Skyreach Creative support tranche

This directory contains exactly three bounded, authority-neutral proposals:

- `W1-001-SR`: selects only the already-written Skyreach subset of `W1-CREATIVE-001`, including the existing `aionbound:wing_bone_stay` requirement, and resolves Skyreach-only curiosity and presentation prose without creating another inventory identity.
- `W1-003-STORM-NEST`: proposes an executable envelope for the four authored Storm Nest phases and six authored Wind Roc attacks, with bounded adds, immutable pull scaling, reset/reload behavior, multiplayer ownership, existing-schema persistence, and ordered idempotent completion. Damage and effect/arena radii are not proposed.
- `W1-004-SR`: applies the already-written global loot/chest/reward envelopes to Skyreach and makes `aionbound:storm_pinion` the sole critical seal. Physical fulfillment is at-most-once with recovery entitlement; mastery/display rewards are optional and non-progressing.

Every file remains `PROPOSED_NOT_RATIFIED`. Nothing here changes the decision ledger or authorizes BP, RP, catalog, or runtime implementation. `W1-CREATIVE-005` and its five sidegrades remain deferred unchanged. The JSON files are canonical and the builder reproduces all JSON/Markdown bytes deterministically.

Run:

```sh
python3 engineering/authority/support-proposals/skyreach/test_skyreach_support_proposals.py
python3 tools/validate_wave1.py
```
