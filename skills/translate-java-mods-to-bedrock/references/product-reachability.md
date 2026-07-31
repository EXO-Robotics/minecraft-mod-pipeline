# Product reachability and completion

Use this gate before calling a Bedrock feature player-facing, survival-complete,
or part of a finished progression loop.

## Keep three claims separate

- `ARTIFACT_PRESENT`: definitions, assets, tests, or helper functions exist.
- `SERVER_LOADABLE`: the exact pack loads and its registered modules initialize.
- `PLAYER_REACHABLE_FEATURE`: a normal player can acquire, trigger, observe, and
  complete the feature through the shipped pack.

The first two do not imply the third.

## Trace the complete path

Record one hash-bound reachability trace per promoted feature:

```text
acquisition or natural spawn
→ usable inventory/world state
→ registered Bedrock event or component
→ authoritative handler
→ feature state transition
→ reward/drop/unlock/persistent result
→ repeat/cleanup behavior
```

Require:

- A legitimate recipe, loot, spawn rule, structure, ritual, admin-independent
  encounter path, or documented vanilla acquisition dependency.
- A runtime caller for every required exported model/service function.
- Valid input dependencies and no stress-test-only summon path.
- Failure, duplicate, ownership, restart, and cleanup behavior.
- At least one current-candidate integration test that begins at the public
  acquisition/trigger surface rather than calling the internal function.

For progression, trace every edge. A craftable key with no registered use
handler, an elite without a spawn/encounter path, or a boss reachable only by a
test function fails the gate.

## Evidence and reporting

Use:

- `PLAYER_REACHABLE_FEATURE_PASS`
- `INTEGRATED_ARTIFACT_ONLY`
- `TEST_FIXTURE_ONLY`
- `CLIENT_EVENT_DELIVERY_PENDING`
- `SURVIVAL_ACQUISITION_BLOCKED`

BDS can prove pack loading and server-side fixture execution. It cannot prove
real controller input or actual client event delivery. Keep
`CLIENT_EVENT_DELIVERY_PENDING` until a real Bedrock client exercises the exact
public path.
