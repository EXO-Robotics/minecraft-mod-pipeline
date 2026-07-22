# ADR 0005: AI output is an advisory proposal, never compiler authority

Status: accepted

## Decision

Optional AI integrations terminate at a versioned `ai-proposal-1.0.0` envelope. The core compiler has no network or model dependency. An adapter may package a candidate interpretation, but the envelope must carry traceable source evidence, prompt template identity and digest, provider/model/adapter provenance, confidence, proposal status, human review state, and a canonical SHA-256 digest.

Validation is deterministic and fail-closed. Unknown fields, missing evidence, invalid confidence, altered digests, or weakened authority flags are rejected. Proposal status is limited to `proposed` or `withdrawn`; it does not imply execution authority.

A reviewer may mark a proposal accepted, but acceptance is still advisory. To affect compilation, a separate override must name the same target, bind the exact proposal ID and digest, and contain a human author and reason. The existing override mechanism remains the only authority. The adapter returns a validated override document; it never applies an AI-authored patch directly.

## Consequences

Deterministic compilation and the supported feature set work with AI disabled. Model changes cannot silently alter generated packs, accepted suggestions remain auditable, and stale or tampered proposals cannot be substituted after review. Integrators are responsible for model invocation outside this boundary and must not place credentials, raw network clients, or provider SDK requirements in the compiler core.
