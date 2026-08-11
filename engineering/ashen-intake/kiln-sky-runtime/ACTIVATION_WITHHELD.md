# Kiln Sky activation withheld

Shared runtime composition was not authorized in this lane and remains intentionally absent from `behavior_pack/scripts/runtime.js`.

## Minimal integration diff requiring approval

Only the integration owner may authorize and apply these shared-loop changes:

1. Import `createKilnSkyService` and `resolveKilnSkyArena` from `./kiln_sky.js`, plus `createAshenRewardHooks` from `./ashen_rewards.js`.
2. Instantiate the Ashen reward hooks with the existing injected `ItemStack`, random source, exact arena resolver, and an `isArenaComplete` callback reading the exact durable Kiln Sky world completion key.
3. Instantiate one Kiln Sky service with the existing `world`, `system`, state service, bounded entity query, reward hooks, and Codex callbacks. Codex event IDs must come from the Ashen Codex lane; this service does not invent them.
4. Call `kilnSky.reconcile()` beside the other encounter reconciliation calls and `kilnSky.tick()` once inside the existing bounded tick callback.
5. In the synchronous block-interaction guard, call the Ashen cache guard beside the existing Thorn Court cache guard.
6. In the deferred block interaction, resolve the exact Ember Forge signature. Begin only from its lodestone anchor; on eligible player interaction, prefer `recoverHorn(player)` when an entitlement is pending, otherwise call `begin(player, arena)`.
7. In the existing entity-death callback, call `kilnSky.bossDeath(event)` beside `thornCourt.bossDeath(event)`.
8. Expose `kilnSky` from the runtime return object for semantic testing.

No new subscription, interval, radius, damage value, natural Ash Drake spawn path, or boss reward identity is permitted by this integration.

## Preconditions before activation

- Integration owner explicitly approves the shared runtime mutation.
- Ashen Codex event IDs are present in the catalog, or the Codex callbacks remain no-op until that lane lands.
- `aionbound:ash_drake_horn` and every reward material are registered in the integrated item lane; `ItemStack` construction cannot be claimed before identifier closure.
- The exact Ember Forge structure signature remains unchanged or its authoritative assembly evidence is re-bound.

## Proof boundary

This file is an activation plan, not evidence that activation occurred. No build or BDS was run.
