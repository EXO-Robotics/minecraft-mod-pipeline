# Thorn Court runtime report

Status: **STATIC SEMANTIC PASS — RUNTIME UNQUALIFIED**

The isolated G8 lane implements the ratified `W1-003-THORN-COURT` and `W1-004-WW-CH1` encounter, reward-guard, and persistence semantics without modifying the immutable proposal bytes.

The service admits one arena session through `boss:thorn_court`, requires five seconds of continuous arena residency before pull, spawns and tags a dedicated `aionbound:thorn_stalker` apex shell, locks scaling at 360/486/612/738 health for one through four pull participants, and enforces the approved phase, timing, leash, wipe, late-join, disconnect, add-cap, reload-reset, and terminal rules.

Only a participant-caused death of the tagged session shell can complete the encounter. Ecology shells and command-style deaths cannot create a seal or trophy. First eligible completion persists the world stamp, per-player completion, virtual chapter-seal credit, and trophy entitlement before attempting physical delivery. Physical delivery uses an at-most-once guard. A synchronous refusal is retryable; a crash-uncertain inflight claim can recover museum/display fulfillment but never emits a second physical trophy. Repeat clears reopen the bounded material-package and separate-arena-chest hooks while never repeating the chapter seal or trophy entitlement. Briar Elk and Mosskip mastery trophies do not occur in any critical predicate.

## Composition boundary

- `thornCourt.begin(player, block.location)` is the arena-start interface.
- `rewardHooks.deliverTrophy` defaults to the approved `aionbound:thorn_stalker_skull` item.
- `rewardHooks.grantMaterialPackage` and `rewardHooks.openArenaChest` are narrow hooks for the separately owned Whisperwood loot/economy lane.
- The start action still needs an approved arena-anchor route before natural discovery is closed.

## Proof boundary

Focused semantic tests pass 13/13 and the composed Node suite passes 60/60. This proves source composition and deterministic state-machine semantics only.

The ratified proposal does not authorize numeric projectile damage, special hit radii, or snare strength. The runtime therefore exposes the exact attack telegraph/active/recovery stages as entity tags, implements approved bounded Howl Call adds, and retains the existing Thorn Stalker shell AI as the live melee carrier. Client-visible stage presentation, effective scaled health, multiplayer behavior, restart behavior, and performance remain for the already-defined Checkpoint 1. No BDS, client, console, or release claim is made here.
