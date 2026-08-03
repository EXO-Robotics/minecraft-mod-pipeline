# Live campaign lessons and portability status

Updated: 2026-08-03

This document records operating lessons learned from real factory campaigns
without importing either campaign's source evidence, queues, task IDs, paths,
mailbox history, credentials, candidates, receipts, or runtime state.

Every mechanism below has one explicit portability status:

- `BUNDLED_HERE`: implemented and tested in this repository.
- `STUDIO_PROVEN_PORT_PENDING`: exercised successfully in the Studio factory,
  but not yet included in this portable distribution.
- `REQUIRED_NOT_IMPLEMENTED`: required by a discovered safety boundary, but no
  qualified portable implementation exists yet.

An AI must not infer that a Studio-proven mechanism is available locally. It
must inspect this checkout and fail closed when the required validator, adapter,
or broker is absent.

## Lessons that apply to every campaign

### Keep state claims narrow

A candidate can pass worker-local checks, T1, an exact Stable BDS lifecycle,
calibrated observation, and T10 for one bounded server-owned slice. That does
not make the slice integrated, prove the whole campaign, or satisfy a retail
client, console, Realms, Marketplace, legal, publication, or release gate.

Preserve these states separately:

1. candidate submitted;
2. mechanically admitted;
3. runtime-qualified on a named server channel;
4. observed with a named actor and capability envelope;
5. semantically qualified for a bounded slice;
6. integrated into a frozen product;
7. qualified by separately owned client or platform gates;
8. privately frozen or publicly released under separate authority.

### Separate candidate generations from activation ordinals

A candidate generation changes only when product bytes materially change.
Every worker launch or reactivation gets its own activation ordinal and
receipt, including host-only recovery. Therefore a new activation may preserve
the same candidate generation and exact product hash.

- `CONTINUE_NONTERMINAL` gathers missing evidence or completes an authorized
  non-product step. It does not authorize product edits.
- `RECOVERY_AFTER_INTERRUPTION` may repair the host, launcher, credentials, or
  delivery path while preserving the exact candidate bytes.
- `REPAIR_REQUIRED` is reserved for one consolidated product defect against
  generation `N` and authorizes exactly one material replacement `N+1`.

Never consume a generation number merely to rerun unchanged bytes or seek a
more favorable qualification streak. Preserve an infrastructure-blocked
predecessor separately from a later instrumented or recovered activation.

### Reuse standing campaign authority only when mechanically bound

A recorded standing launch authority can cover routine `NEW_PACK`,
`CONTINUE_NONTERMINAL`, `REPAIR_REQUIRED`, `RECOVERY_AFTER_INTERRUPTION`, and
bounded T2 work when all of the following remain exact: campaign, frozen source,
rights basis, private/local scope, clean-room security model, lane, role,
allowed roots, denied roots, and receipt policy.

A new user decision is still required when rights, source scope, security
model, authenticated identity, Realms, retail client, console, publication, or
release scope changes. Standing authority is valid only when a repository-owned
validator binds it to the activation. If that validator is absent, ask the user
rather than treating prose or an old chat as authority.

### Treat instrumentation as evidence, never product

Preserve a candidate-only baseline. GameTest, observer, protocol-client, and
diagnostic overlays run in separate disposable fixtures against the same exact
candidate. They never enter the candidate archive or become proof beyond their
calibrated actor and scenario.

Offline protocol identities can prove bounded local delivery, reconnect,
ownership separation, inventory observation, and player/world scoping. They do
not prove authenticated XUID, Xbox persistence, Realms, retail UI, controller,
split-screen, rendering, audio, or physical-console behavior.

### Do not hand a sandboxed worker the host Docker socket

Mounting or exposing the host Docker socket to a production worker defeats its
filesystem boundary because the worker can ask the host daemon to mount paths
outside the lane. A worker that needs a privileged host action must submit a
declarative request to a controller-owned, least-authority executor. The
executor must validate the assignment, allowlisted action, exact inputs and
outputs, denied paths, lifecycle, cleanup, and receipt before acting.

Until that broker exists, an activation blocked before worker startup is
`INFRASTRUCTURE_BLOCKED`. It produced no product finding, no oracle finding, and
no candidate. Denied startup must be recorded without copying credentials or
private evidence into logs.

## Portable implementation inventory

| Capability | Status | Portable interpretation |
|---|---|---|
| SQLite jobs, leases, events, receipts, and recovery | `BUNDLED_HERE` | Available after local initialization and rehearsal. |
| Independent Git mailbox and immutable candidate generations | `BUNDLED_HERE` | Durable authority; runtime projections remain diagnostic. |
| Hash-bound dispatch and adaptive role-pool scaling | `BUNDLED_HERE` | Duplicate delivery and service caps are mechanically represented. |
| macOS deny-by-default production launcher and process receipt | `BUNDLED_HERE` | Use only with explicit roots and denied-path probes. |
| Candidate-only and instrumented observation role contracts | `BUNDLED_HERE` | Evidence semantics are documented; external clients and servers are not bundled. |
| Standing campaign launch-authority validator | `STUDIO_PROVEN_PORT_PENDING` | The contract is documented here; this checkout must not assume the validator exists. |
| Exact BDS channel adapter and hardened runtime authority | `STUDIO_PROVEN_PORT_PENDING` | BDS/Docker binaries and the newer adapter implementation are not in this branch. |
| External worker projection into committed mailbox state | `STUDIO_PROVEN_PORT_PENDING` | Do not substitute chat summaries for the missing projection. |
| Fresh-repository task-pack compatibility and hardened receipt bindings | `STUDIO_PROVEN_PORT_PENDING` | Port and independently test before claiming parity with Studio. |
| Native Blockbench bridge and extended visual-production pipeline | `STUDIO_PROVEN_PORT_PENDING` | The bundled visual skills do not imply the newer Studio bridge is present. |
| Controller-owned least-authority privileged executor/broker | `REQUIRED_NOT_IMPLEMENTED` | Required before a sandboxed worker may request host-owned privileged actions. |
| Receipt-preserving denial and pre-start failure logger | `REQUIRED_NOT_IMPLEMENTED` | Must record the stop without secrets, evidence, or false product state. |

## Porting rule

Port mechanisms as small reviewed changes with tests, then change their status
to `BUNDLED_HERE`. Never copy a live factory root. A new machine creates its own
control root, synthetic rehearsal receipt, campaign authority, mailbox, queues,
candidate history, external-gate receipts, and credentials.
