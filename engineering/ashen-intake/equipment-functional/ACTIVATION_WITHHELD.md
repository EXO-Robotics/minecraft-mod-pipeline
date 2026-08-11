# Shared activation withheld

The dedicated service is not imported by `combat.js` or `runtime.js`, and `ash_repeater` is not added to the shared item router. This preserves the safety hold on persistent cooldowns, inventory mutation, damage, fire, and effect application.

## Minimal composition requiring explicit approval

1. Import `createAshenEquipmentService` from `./ashen_equipment.js` in `runtime.js`.
2. Instantiate one service with the existing `world`, `system`, state, arbiter, `EquipmentSlot`, and `EntityComponentTypes` dependencies.
3. Add `aionbound:ash_repeater: ashen_ranged` to `COMPLETED_ITEM_ROUTES`; add an `ashen_ranged` action that calls only `ashenEquipment.useRanged`.
4. In the existing `entityHurt` callback, call `ashenEquipment.routeMeleeHurt(event)` and `ashenEquipment.handlePlayerHurt(event)` alongside the existing combat calls, without conditional early returns.
5. At the existing 20-tick player cadence, call `ashenEquipment.tickPlayers()` beside `combat.tickPlayers()`.
6. Expose `ashenEquipment` from the runtime return object for transformed-source semantic testing.

No new subscription, interval, item identity, Creative sidegrade, natural entity path, or Briar Ring mutation is permitted.

## Required post-approval checks

- Transformed-source subscriber composition and stable API audit.
- Ash Repeater inventory mutation and selected-item durability semantics against the literal packaged entrypoint.
- Exact item/repair identifier closure.
- Bounded entity-query and particle budgets.

This is an activation plan, not proof that activation occurred.
