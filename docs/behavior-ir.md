# Behavior IR and evidence

Behavior IR describes gameplay intent without Java or Bedrock implementation details.

```yaml
id: example:teleport_item/use
owner: example:teleport_item
trigger: item_use
conditions:
  - actor_is_sneaking
actions:
  - kind: teleport_actor
state_reads:
  - player:cooldown
state_writes:
  - player:cooldown
feedback:
  - sound
  - particle
evidence_ids: [ev-001, ev-002]
confidence: 0.84
review:
  proposed_by: ai
  accepted_by: null
  status: proposed
```

Evidence may reference source file/class/method/field/line/AST, bytecode class/method/offset, resource path, registration path, extraction rule, analyzer version, source mode, confidence, and conflicts. Arbitrary generated code is not an IR action.

Intent is separated from implementation strategy. One intent can be reconstructed data-first, with stable scripts, by approved redesign, or not at all. State records scope, ownership, persistence, schema version, migration obligations, and multiplayer isolation.

Fingerprints use normalized semantic fields and versioned algorithms. Migration is deterministic and fail-closed. Conflicting or insufficient evidence produces ambiguity; it never silently promotes a proposal to accepted intent.

