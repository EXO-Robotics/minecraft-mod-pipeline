# Requirement traceability matrix

## Status rules

- `IMPLEMENTED`: authoritative repository evidence demonstrates the current requirement.
- `PARTIAL`: useful implementation exists, but the full requirement or qualification gate is not proven.
- `NOT_IMPLEMENTED`: no qualifying implementation exists.
- `EXTERNAL_BLOCKED`: completion requires unavailable external hardware, access, rights evidence, partner review, or authority. This status is not used for ordinary engineering work.
- `DOCUMENTED`: the requirement contract or scaffold exists; this does not imply implementation.

This matrix describes the repository after the executable Benchmark A foundation and pinned Creator Tools validation. Tests promote only the requirements they directly exercise.

| ID | Requirement | Status | Current evidence / missing proof |
|---|---|---|---|
| DOC-01 | Product architecture | `DOCUMENTED` | `docs/product-architecture.md` |
| DOC-02 | Target profiles | `DOCUMENTED`; implementation `PARTIAL` | Executable profiles and Marketplace/data-only unit gates exist; end-to-end qualification does not |
| DOC-03 | AI tool interface | `IMPLEMENTED` operation catalog; external execution `PARTIAL` | All 76 required names dispatch; persistent artifact-backed workflow and safe edits run, while unmanaged runtime operations fail closed |
| DOC-04 | Java adapters | `DOCUMENTED`; implementation `PARTIAL` | Authentic-pattern Fabric/Forge source fixtures and defined source/JAR semantic parity pass when a JDK is available; broad API qualification remains |
| DOC-05 | Behavior IR/evidence | `DOCUMENTED`; implementation `PARTIAL` | Versioned IR/evidence and persistent project storage exist; exhaustive source indexes and broad corpus qualification remain |
| DOC-06 | Capability catalog | `DOCUMENTED`; implementation `PARTIAL` | Initial symbol/version and target catalogs are tested; full symbol/source/device coverage is not proven |
| DOC-07 | Reconstruction patterns | `IMPLEMENTED` baseline catalog | Required Marketplace pattern families have IR shapes, strategies, limitations, performance notes, and test contracts; runtime qualification remains separate |
| DOC-08 | Rights system | `DOCUMENTED`; implementation `PARTIAL` | Schemas and fail-closed human-review evaluator are tested; no actual human-cleared corpus/package evidence |
| DOC-09 | Creator Tools | `IMPLEMENTED` for Benchmark A/B static validation | Pinned official Creator Tools 0.17.6 passed `addon` and `currentplatform` with zero errors/warnings on exact hash-bound archives; no approval is implied |
| DOC-10 | Performance budgets | `DOCUMENTED`; implementation `PARTIAL` | Static budget and attributable exception gates tested; runtime/device measurements absent |
| DOC-11 | Controller redesign | implementation `PARTIAL`; runtime `UNVERIFIED` | Benchmark B uses stable `ActionFormData` for cancel-safe lock-removal confirmation and independently resolves `server-ui` 2.0.0; no real form or physical controller benchmark evidence |
| DOC-12 | Persistence/migrations | `DOCUMENTED`; implementation `PARTIAL` | Benchmark B validates revisioned records, normalizes sparse records, migrates one nonempty v0 lock through a state-preserving BDS pack upgrade, and reads it on a third boot; interrupted writes, reconnect, player-created state and machine restoration remain unproven |
| DOC-13 | Validation | `DOCUMENTED`; implementation `PARTIAL` | Profile, symbol, rights, static performance, packaging, live Creator Tools, and isolated BDS boot/restart gates exist; real player-action execution is missing |
| DOC-14 | Console testing | `DOCUMENTED`; execution `EXTERNAL_BLOCKED` | Protocol/checklists exist; physical hardware/Realm execution not recorded |
| DOC-15 | Known limitations | `DOCUMENTED` | `docs/known-limitations-marketplace.md` |
| DOC-16 | Corpus methodology | evaluator `IMPLEMENTED`; real corpus `NOT_IMPLEMENTED` | All required threshold metrics and holdout discipline are executable and fail closed; legally reviewed real corpus/holdout is absent |
| DOC-17 | User guide | `IMPLEMENTED` for baseline | Existing `docs/user-guide.md`, with Marketplace documents indexed separately |
| DOC-18 | Agent guide | `DOCUMENTED`; operation workflow `IMPLEMENTED` locally | All required names dispatch; Benchmark A passes the persistent create-to-report workflow; runtime execution still requires an external adapter |
| DOC-19 | Reproduction commands | `DOCUMENTED` | `docs/reproduction.md`; baseline-only non-qualification warning included |
| ARCH-01 | Persistent conversion project | `IMPLEMENTED` foundation | Full layout, revisioned store, intent lifecycle, safe protected edits, generation, validation, reports, and resume are tested; runtime-backed execution remains partial |
| ARCH-02 | Protected custom content | `IMPLEMENTED` foundation | Registered custom scripts/assets are staged, API-audited, packaged, regenerated deterministically, and source-preservation tested |
| ARCH-03 | Clean consumer/build boundary | `IMPLEMENTED` foundation | Exact Benchmark A/B archives exclude project evidence, reports, tests, Java payloads, and debug collateral and pass official static inspection |
| API-01 | Symbol-level stable API validation | `PARTIAL` | Initial catalog and unknown-symbol rejection tested; complete emitted-symbol coverage/source verification absent |
| API-02 | Independent server/server-ui resolution | `IMPLEMENTED` for current catalog | Independent resolution and UI-only dependency tests pass |
| API-03 | Fail-closed event adapters | `PARTIAL` | Unmapped required trigger fails compilation; real Minecraft actions remain untested |
| FRONT-01 | Modern Fabric semantics | `PARTIAL` | Authentic-pattern metadata/source fixture test passes; full API and compiled-JAR qualification missing |
| FRONT-02 | Forge 1.7.10 semantics | `PARTIAL` | Authentic-pattern metadata/manifest/source fixture test passes; full API and compiled-JAR qualification missing |
| FRONT-03 | Compiled-JAR evidence | `PARTIAL` | Loader-neutral class/annotation/method/invoke/field/constant/resource facts and defined Fabric/Forge parity exist; current host lacks a usable JDK and broad real-mod qualification remains |
| GEN-01 | Baseline BP/RP/script generation | `PARTIAL` | Deterministic scaffolds and profile-aware outputs exist; product fidelity/runtime not qualified |
| GEN-02 | `.mcaddon` generation | `PARTIAL` for production | Deterministic clean archive and live official static validation pass for Benchmark A; gameplay/runtime qualification is missing |
| GEN-03 | `.mcworld` generation | `IMPLEMENTED` foundation | Deterministic world archive, embedded BP/RP bindings, minimal little-endian `level.dat`, and artifact hashes are tested; Minecraft runtime import remains unverified |
| VAL-01 | Current repository unit suite | `IMPLEMENTED` | 136 tests pass; one compiled-Java test is skipped because this host has no usable JDK; strict mypy passes 56 source files |
| VAL-02 | Real-action event integration | `NOT_IMPLEMENTED` | Internal dispatch tests cannot satisfy this gate |
| VAL-03 | Persistence/multiplayer/migration | `PARTIAL` runtime | Revision-checked state, schema validation, pure adverse migration cases, a nonempty BDS upgrade, migrated-record restart, and narrow diagnostic persistence pass; player actions, interrupted writes, reconnect, and multiplayer remain unverified |
| VAL-04 | Creator Tools suites | `IMPLEMENTED` for Benchmark A/B static artifacts | Live pinned official suites passed with artifact-bound checked-in summaries; runtime and Marketplace approval remain separate |
| VAL-05 | Performance limits | `PARTIAL` | Static limits/approvals tested; runtime limits and device evidence absent |
| BENCH-A | Original Marketplace showcase | `IMPLEMENTED` static benchmark; BDS diagnostic `PARTIAL` | Executable 21-family fixture, IR/quality/test contracts, clean archive, live Creator Tools, and isolated server diagnostics exist; real player-action qualification remains |
| BENCH-B | Rights-cleared real mod | technical reconstruction `PARTIAL`; rights `REVIEW_REQUIRED` | Pinned DoorLock evidence drives a deterministic clean-room package with lock controller, revisioned migration, stable controller confirmation, complete unresolved fidelity records, Creator Tools pass, and three-cycle BDS upgrade proof; gameplay fidelity and human rights review remain |
| CON-01 | Local Windows | `UNVERIFIED` | Benchmark A artifact exists, but no Minecraft for Windows runtime run is recorded |
| CON-02 | Realm Windows | `EXTERNAL_BLOCKED` | Requires artifact, Minecraft/Realm access, and execution |
| CON-03 | PS4/PS5 | `EXTERNAL_BLOCKED`, `UNVERIFIED` | Requires physical hardware/account/Realm route; no results fabricated |
| CON-04 | Xbox One/Series | `EXTERNAL_BLOCKED`, `UNVERIFIED` | Requires physical hardware/account/Realm route; no results fabricated |
| RIGHTS-01 | Human Marketplace clearance | `EXTERNAL_BLOCKED` | Compiler cannot provide legal authority; no review has occurred |
| MARKET-01 | Marketplace candidate | `NOT_IMPLEMENTED` | Static Benchmark A tooling passes, but human rights, runtime, Realm, performance, controller, and console evidence gates do not |
| MARKET-02 | Marketplace submission/approval | `EXTERNAL_BLOCKED` | Microsoft/authorized publishing authority only |

## Documentation completion mapping

All documentation subjects named by the product specification have a dedicated document or existing baseline guide. Console and benchmark files use `UNVERIFIED`/`NOT_RUN` defaults and contain no fabricated evidence. This documentation milestone does not satisfy any production implementation or platform gate by itself.
