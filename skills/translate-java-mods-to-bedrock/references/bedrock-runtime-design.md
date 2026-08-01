# Bedrock runtime design

Use this reference when selecting Bedrock mappings or implementing shared state,
persistent devices, active items, multiplayer behavior, or console budgets.

## Select a supported mapping

Reconstruct player-facing function rather than Java implementation shape.
Replace loader hooks, mixins, arbitrary JVM state, custom networking, custom
renderers, and GUIs with supported Bedrock data/components, stable Script API,
structures, recipes, loot, animation controllers, and bounded
server-authoritative services.

Classify each role as:

- `NATIVE_MAPPING`: Bedrock data/components preserve the function.
- `STABLE_SCRIPT_REDESIGN`: stable Script API supplies bounded behavior.
- `ORIGINAL_SUBSTITUTE`: an authorized original Bedrock-native design replaces
  unsupported expression.
- `CONSOLIDATE`: multiple source roles share one Bedrock service.
- `DEFER`: the role is valid but outside the safe dependency closure.
- `BLOCKED`: no stable bounded mapping satisfies the contract.

Preserve ordinary Minecraft mining, crafting, inventory, survival, combat,
exploration, worlds, and multiplayer. Treat reconstructed systems as additive.
Use original fixed finishes or explicit substitutes instead of fragile attempts
to mimic arbitrary Java rendering.

## Build shared services before consumers

Freeze interfaces for identifiers, player identity, versioned persistence,
reconciliation, ownership, scheduling, telemetry, idempotency, cleanup, and
test hooks before parallel feature work. A workload must not create a competing
state authority when an admitted shared service exists.

For every active system define:

- population, queue, projectile, particle, scan, and persistence caps;
- cleanup behavior and cleanup-latency bounds;
- restart-safe versioned state and migration;
- duplicate/redundant event handling;
- two- and four-player ownership/isolation;
- a lower-cost configuration for the worst credible PS4 scene.

## Persistent world devices

Shard versioned records by dimension and coordinate, use revision
compare-and-swap, cap each shard and reconciliation batch, and quarantine
invalid schemas. Do not delete the authoritative record until owned world
artifacts are cleared. Preserve a bounded cleanup record when adjacent or paired
artifacts are unloaded or blocked.

Keep collision, appearance, ownership, interaction, and redstone as separate
requirements. Visual opacity does not imply collision, and directional visual
design does not imply one-way rendering.

## Active and moving items

Bind long-running use/charge operations to a unique dynamic property on the
non-stackable physical `ItemStack`, write it back to the container, and require
the marker for every continuation and completion. Bind durability and rollback
to the authoritative tracked slot, never implicitly to the selected slot.

When an active marked item may move, use event-local slot observations. Allow
at most one two-tick reconciliation callback for the exact operation generation.
Transfer authority only when the matching arrival is observed first; otherwise
cancel as loss. Duplicate, stale, completed, and superseded callbacks remain
inert. Permit at most one completion callback plus one pending reconciliation
callback per operation. Do not add inventory or world scans to recover stale
markers.

Test same-inventory movement, hotbar/inventory movement in both directions,
both event orders, true loss, unmarked replacement, duplicate events,
completion/cancellation races, two/four-player ownership, and exact tracked-slot
writes. Test controller-to-runtime handoff, not each layer in isolation.

## Presentation and reachability

Require paired BP/RP presentation for promoted items and wearables: behavior,
client texture or attachable, atlas registration, localization, and survival
acquisition. A server-loadable item without client binding remains
`INTEGRATED_ARTIFACT_ONLY`.

Trace acquisition/spawn through the public event surface, authoritative state
transition, reward/persistence, repeat behavior, and cleanup. Internal exports,
stress-only helpers, unobtainable recipes, or unspawnable entities are not
completed player features.

## Platform claims

Use “PS4 planning profile passed” for static budgets. Use `PS4_VERIFIED` only
after the exact frozen artifact completes the required Realm delivery,
controller-only, split-screen, multiplayer, persistence/reconnect, and
worst-case-scene checks on physical PS4. Keep desktop, authenticated identity,
Realms, controller, split-screen, and physical-console evidence independent.
