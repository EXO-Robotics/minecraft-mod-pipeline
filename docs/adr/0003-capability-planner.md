# ADR 0003: Evidence-driven capability planner

- Status: Accepted
- Date: 2026-07-22

## Context

Bedrock data definitions and Script API cover many behaviors but do not host arbitrary JVM code, loader hooks, custom protocols or client rendering. A binary supported/unsupported flag hides useful reconstructions and dangerous approximations.

## Decision

Match BehaviorIR fingerprints against a versioned capability catalog and pattern catalog for an explicit target profile. Emit exactly one strategy class per planned unit: `DIRECT`, `SCRIPTED_EQUIVALENT`, `RECONSTRUCTED`, `BEHAVIORAL_APPROXIMATION`, `VISUAL_APPROXIMATION`, `MANUAL_REDESIGN`, or `UNSUPPORTED`.

Keep extraction confidence, capability confidence, behavioral fidelity, visual fidelity, performance risk and multiplayer/persistence risk as separate values. Each plan cites matched capability/pattern versions, required backend modules, validation obligations and unresolved evidence. Human overrides are versioned inputs and survive regeneration.

## Consequences

The report is honest about semantic distance and can block high-risk output. Catalog maintenance and target-profile testing become core engineering work. No score aggregation may upgrade an unsupported platform primitive into a supported claim.

