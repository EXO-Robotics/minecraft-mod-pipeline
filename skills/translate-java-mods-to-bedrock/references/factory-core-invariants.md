# Factory core invariants

Use this reference when starting, resuming, repairing, qualifying, integrating,
or reporting a Java-to-Bedrock campaign.

## Authority and lanes

- Bind every source, contract, activation, candidate, runtime, fixture,
  collector, and result to immutable hashes.
- Keep raw Java material, private observations, source identifiers, and hidden
  cases in evidence/control lanes. Give production only sanitized contracts,
  opaque IDs, and approved neutral infrastructure.
- Require process-level isolation and a receipt for every production,
  integration, visual-production, or repair process. A clean prompt or clean
  output scan does not prove isolated authorship.
- Store mutable campaign facts in task packets and durable repositories, not in
  skills or chat prose.

## Candidate lifecycle

Keep these states distinct:

```text
worker-local complete
-> immutable candidate submitted
-> mechanically admitted
-> runtime qualified
-> bounded slice qualified
-> integrated
-> client/platform qualified
-> released
```

Do not let a broad legacy message type override explicit structured fields. In
particular, an accepted slice with `integrated: false` is not integrated.

Freeze implementation/package bytes before downstream gates. Preserve rejected
generation `N`; a material repair publishes exactly `N+1`. Never retry unchanged
bytes or amend a frozen candidate. Keep evidence-only commits separate and
carry package-bound evidence forward only after exact hash equality is proven.

## Test ownership and evidence

- Workers own declared local tests and candidate freeze, never T1, BDS, T10,
  integration, retail client, Realms, controller, split-screen, PS4, or release.
- T1 owns mechanical admission, not gameplay.
- BDS baseline owns exact-package load, lifecycle, save, and restart.
- Instrumented and protocol-client lanes own only behavior their calibrated
  collectors can observe.
- T10 owns independent contract evaluation and hidden cases, not repair.
- Named client/platform owners retain UI, rendering, input, account, Realm,
  split-screen, and physical-console claims.

Separate Stable and Preview lifecycle qualification from Stable and Preview
network-player semantics. A clean boot, direct hook, test double, mutation
harness, GameTest, or SimulatedPlayer result cannot establish ordinary network
event delivery unless that actor/path was calibrated for the assertion.

Use typed comparison modes: `EXACT`, `STRUCTURAL`, `BOUNDED`, `INVARIANT`,
`APPROVED_SUBSTITUTE`, `DISTRIBUTIONAL`, and `CLIENT_REQUIRED`. Missing or
unsupported observations yield `ORACLE_INSUFFICIENT`, `CLIENT_REQUIRED`,
`INCONCLUSIVE`, or `INFRASTRUCTURE_BLOCKED`, never an invented product defect.

## Vertical slices and repairs

Prefer the smallest coherent player-facing dependency closure over feature
count. Register a qualified slice without implying integration or release, and
name its deferred systems and later gates.

Every production task pack should declare applicable local cases for first use,
repeat/redundant use, invalid input, partial/malformed/old state, migration,
duplicate delivery, exact resource accounting, persistence/restart, second
player, cleanup, and bounded scheduling. Mark irrelevant cases explicitly.

Trace every downstream product finding mechanically:

```text
finding ID
-> consolidated sanitized repair requirement
-> worker regression ID
-> replacement generation receipt
-> independent retest result
```

Move recurring failures left into shared validators or worker-local matrices,
but keep hidden variants private. Repair infrastructure, collectors, fixtures,
or authority without creating a product generation when no defect is proven.

## Capacity and recovery

Scale by actionable queue pressure and proven service slots, not by a fixed
worker/tester/auditor ratio. More threads do not create more BDS, client, or
audit capacity. Apply upstream backpressure when qualification saturates.

Resume solely from committed repositories, append-only mailbox history,
SQLite projections, hash-bound dispatch state, and activation attestations. One
semantic dispatch identity creates at most one worker. Preserve failed and
inconclusive experiments.
