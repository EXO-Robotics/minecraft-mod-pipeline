# Cross-factory observation and comparison

Use this reference when a campaign needs runtime observation beyond package
load, or when comparing two reconstruction factories.

## Reusable controls

### Bind every result to a complete tuple

Recompute the candidate SHA-256 immediately before each gate. Record the
candidate commit/tree/generation, package hash, runtime binary hash, container
digest and architecture, fixture/world hash, collector version, dependency
lock, scenario version, and calibration authority. Stop on any mismatch.

### Separate baseline from instrumentation

Run an uninstrumented candidate-only baseline first. Put observers, GameTest
drivers, simulated players, and protocol actors in disposable test lanes. Keep
test packs outside the shipping `.mcaddon`.

Calibrate instrumentation against the baseline. Quarantine observations if the
collector changes candidate bytes, initial state, inventory, progression,
namespace, product errors, spawning, or timing outside declared bounds.
Instrumentation failure is an evidence failure, not a product defect.

### Use explicit observation states

Represent every required field as one of:

- `OBSERVED_TRUE`
- `OBSERVED_FALSE`
- `NOT_OBSERVED`
- `UNSUPPORTED_BY_ADAPTER`
- `INCONCLUSIVE`
- `CLIENT_REQUIRED`

Never translate absence into false.

### Route outcomes by cause

Use distinct terminal classes:

- `PASS_EQUIVALENT`
- `PASS_APPROVED_SUBSTITUTE`
- `PRODUCT_DEFECT`
- `ORACLE_INSUFFICIENT`
- `CLIENT_REQUIRED`
- `INCONCLUSIVE`
- `INFRASTRUCTURE_BLOCKED`

Authorize production repair only for `PRODUCT_DEFECT` backed by acceptable
evidence. Repair the collector, runtime, fixture, or authority for the other
failure classes without creating a product generation.

### Distinguish actors and claim boundaries

Treat real retail clients, protocol actors, simulated players, and direct test
hooks as different evidence classes. Calibrate per scenario family; one match
does not authorize global equivalence.

A protocol actor may prove the normal network session, spawn, reconnect,
concurrent identities, packet delivery, and fields it actually observes. It
does not prove retail UI, rendering, audio, controller ergonomics, XUID or
online-auth ownership, Realms, split-screen, or physical-console behavior.

### Keep scenarios platform-neutral

Define scenario and behavior IDs, fixture authority, actors, minimum evidence
class, abstract actions, required observation fields, comparison mode,
tolerances, missing-evidence outcome, cleanup deadline, and total time bound.
Keep runtime commands and source identifiers inside private adapters.

Use `EXACT`, `STRUCTURAL`, `BOUNDED`, `INVARIANT`, and
`APPROVED_SUBSTITUTE` as appropriate. Add `DISTRIBUTIONAL` only for genuinely
variable mechanics with a declared sampling plan and acceptance bounds.

### Reconcile durable results

Prefer this authority flow:

`evidence commit -> hash-chained run ledger -> sanitized Git mailbox event ->
SQLite projection -> reconciliation`

Treat Git and immutable artifacts as authority. Treat SQLite as a projection,
not an independent source of truth. Fail closed when candidate, evidence,
mailbox, and projection identities disagree.

Keep lifecycle states separate: candidate submission, mechanical admission,
runtime qualification, bounded-slice qualification, integration,
client/platform qualification, and release. Do not infer integration from a
legacy message-type label when controlling structured fields say otherwise.

### Learn from repairs

Bind each accepted product finding to one consolidated sanitized repair
requirement, one rejected generation, one worker regression ID, the exact
replacement-generation receipt, and one independent retest result. Preserve
failed generations and failed authoring attempts. Move recurring public failure
families into task-pack local matrices and shared validators while keeping
hidden variants private.

Prefer a bounded coherent vertical slice that completes the full gate loop over
a broad partially observed feature set. Register slice qualification without
implying integration, client proof, console proof, or release.

### Compare factories quantitatively

Record first-submission T1 pass rate, Stable/Preview load rate, percentage with
network-player evidence, fixtures and restart cycles, duplication/loss and
persistence failures, average repair generations, false product-failure rate,
queue time per gate, proven BDS slots, orphaned runtime objects, complete-hash
receipt rate, sanitized-repair rate, and remaining platform gates.

Do not combine these into one score unless the weighting and evidence scope are
frozen in advance.

## Do not import blindly

- Do not add a gate merely because another campaign uses it. Require it only
  when it closes a material risk or evidence gap.
- Do not copy campaign identifiers, source names, private adapters, hashes,
  fixtures, scenarios, pass counts, hidden cases, or mutable runtime state.
- Do not make a campaign depend on a shared observation service when its
  existing mechanically equivalent lane is already authoritative.
- Do not treat Mineflayer, a Bedrock protocol library, GameTest, simulated
  players, or direct hooks as a retail client.
- Do not treat offline identity as proof of XUID, online authentication, Xbox
  persistence, or Realms behavior.
- Do not expose candidate-private state merely to make an observer convenient.
  Mark the field unsupported or use a separately authorized private audit.
- Do not reject a candidate because an observer cannot see a private namespace.
  Return insufficient evidence unless another accepted source proves a defect.
- Do not count repeated clean boots as semantic coverage or use restart volume
  to inflate confidence in an unobserved behavior.
- Do not treat Stable or Preview lifecycle qualification as Stable or Preview
  network-player semantic qualification. Record those gates separately.
- Do not treat a packaged test double or private mutation harness as an
  ordinary Bedrock player. It proves only its calibrated internal path.
- Do not use `DISTRIBUTIONAL` where an exact count or invariant is required.
- Do not globally trust fake or simulated players after one calibration.
- Do not treat worker-thread count as runtime capacity. Apply backpressure from
  proven BDS, client, and audit slots.
- Do not insert a redundant semantic-review gate when an existing independent
  audit already owns the same boundary; strengthen the existing gate instead.
