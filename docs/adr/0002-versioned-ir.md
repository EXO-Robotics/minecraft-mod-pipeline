# ADR 0002: Versioned ModIR and BehaviorIR

- Status: Accepted
- Date: 2026-07-22

## Context

Loader/source/bytecode analyzers and Bedrock backends evolve independently. Directly generating packs from scanner matches would couple uncertain evidence to target syntax and make changes unreviewable.

## Decision

Use versioned, schema-validated ModIR and BehaviorIR as the only planner input. ModIR represents content, resources, registrations, dependencies and platform intent. BehaviorIR represents triggers, conditions, actions, state, presentation, UI and networking intent. Every semantic node links to evidence/conflicts/override provenance and has a stable readable fingerprint plus versioned canonical hash.

Schemas are append-only within a minor version. Breaking meaning or canonicalization increments the major version. Explicit pure migrations transform old documents, preserve original fingerprints in migration provenance, and are golden-tested. Unknown required fields fail closed.

## Consequences

Frontends and backends can evolve separately; plans and reports become diffable. Schema and fingerprint migrations add maintenance cost, but prevent silent reinterpretation and allow deterministic regeneration tests.

