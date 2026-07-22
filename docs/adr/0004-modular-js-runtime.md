# ADR 0004: Modular generated JavaScript runtime

- Status: Accepted
- Date: 2026-07-22

## Context

Scripted equivalents need shared event dispatch, scheduling, persistent state, forms and diagnostics. Per-feature intervals/subscriptions scale poorly and make generated output difficult to validate. Bedrock forms are asynchronous and some operations are restricted in before-event execution; ticking behavior is also constrained by simulation state. Sources: [Script API](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server/minecraft-server?view=minecraft-bedrock-stable), [ActionFormData](https://learn.microsoft.com/en-us/minecraft/creator/scriptapi/minecraft/server-ui/actionformdata?view=minecraft-bedrock-stable), and [simulation/ticking guide](https://learn.microsoft.com/en-us/minecraft/creator/documents/simulationrenderdistanceguide?view=minecraft-bedrock-stable) (accessed 2026-07-22).

## Decision

Generate small deterministic modules: bootstrap, event router, behavior dispatch tables, state store/migrations, bounded machine scheduler, entity/boss controllers, form adapters, diagnostics and test hooks. Subscribe once per event family and dispatch by identifiers. Use one budgeted scheduler with indexes and invalidation, not one interval per machine. Defer mutations out of restricted contexts. Namespace/version dynamic properties and surface errors without crashing unrelated features.

No module may depend on Node APIs. Stable Script API imports and exact versions come only from the target profile. Preview APIs require an explicit opt-in profile and cannot be labeled generally compatible.

## Consequences

Generated runtime behavior is auditable, testable and scalable. The shared runtime becomes compatibility-critical and needs fixture coverage on every supported BDS profile. Shared failures must be isolated through guarded dispatch and diagnostics.

