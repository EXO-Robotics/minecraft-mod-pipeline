# ADR 0001: Deterministic Python source frontend with `javap` fallback

- Status: Accepted
- Date: 2026-07-22

## Context

Inputs range from source trees to release-only JARs. Source offers line-precise declarations and control/data-flow evidence. The JDK `javap` tool can disassemble classes and expose private members, descriptors, bytecode, constants, annotations and optional line tables, but cannot recreate source intent. See [Oracle `javap`](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javap.html) (accessed 2026-07-22).

## Decision

Implement orchestration and the canonical source frontend in Python with deterministic traversal, parsing, normalization and serialization. Do not make a network model or an IDE index a required compiler stage. For JAR-only inputs, invoke a detected, version-pinned JDK 21 `javap` using canonical flags and parse its output into lower-confidence evidence. Archive paths, selected multi-release version, command/tool version and hashes are mandatory provenance.

Source and bytecode findings share an evidence interface but retain distinct `source_mode` and confidence. Regex is candidate discovery only. Missing JDK disables the bytecode analyzer with an actionable diagnostic; it does not change source results.

## Consequences

Builds remain inspectable and offline reproducible. Java grammar evolution requires maintained fixtures. `javap` output parsing is tool-version-sensitive and must be golden-tested. Obfuscated/reflection-heavy mods frequently need overrides or manual redesign.

