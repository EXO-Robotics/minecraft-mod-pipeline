# Requirement traceability matrix

## Status rules

- `IMPLEMENTED`: authoritative repository evidence demonstrates the current requirement.
- `PARTIAL`: useful implementation exists, but the full requirement or qualification gate is not proven.
- `NOT_IMPLEMENTED`: no qualifying implementation exists.
- `EXTERNAL_BLOCKED`: completion requires unavailable external hardware, access, rights evidence, partner review, or authority. This status is not used for ordinary engineering work.
- `DOCUMENTED`: the requirement contract or scaffold exists; this does not imply implementation.

This matrix describes the repository at the documentation-scaffolding milestone. Existing tests passing does not promote broader requirements unless those tests cover them.

| ID | Requirement | Status | Current evidence / missing proof |
|---|---|---|---|
| DOC-01 | Product architecture | `DOCUMENTED` | `docs/product-architecture.md` |
| DOC-02 | Target profiles | `DOCUMENTED`; implementation `PARTIAL` | Executable profiles and Marketplace/data-only unit gates exist; end-to-end qualification does not |
| DOC-03 | AI tool interface | `DOCUMENTED`; implementation `PARTIAL` | Project/analysis/planning subset and JSON-lines adapter are tested; required operation catalog is incomplete |
| DOC-04 | Java adapters | `DOCUMENTED`; implementation `PARTIAL` | Authentic-pattern Fabric/Forge source fixtures pass; broad API and compiled-JAR qualification remain |
| DOC-05 | Behavior IR/evidence | `DOCUMENTED`; implementation `PARTIAL` | Existing versioned IR/evidence baseline lacks full source indexes/project persistence |
| DOC-06 | Capability catalog | `DOCUMENTED`; implementation `PARTIAL` | Initial symbol/version and target catalogs are tested; full symbol/source/device coverage is not proven |
| DOC-07 | Reconstruction patterns | `DOCUMENTED`; implementation `PARTIAL` | Existing small pattern set is not the required Marketplace library |
| DOC-08 | Rights system | `DOCUMENTED`; implementation `PARTIAL` | Schemas and fail-closed human-review evaluator are tested; no actual human-cleared corpus/package evidence |
| DOC-09 | Creator Tools | `DOCUMENTED`; implementation `PARTIAL` | Pin/policy/recorded-output adapter tested; no live official-tool Benchmark A run |
| DOC-10 | Performance budgets | `DOCUMENTED`; implementation `PARTIAL` | Static budget and attributable exception gates tested; runtime/device measurements absent |
| DOC-11 | Controller redesign | `DOCUMENTED`; runtime status `UNVERIFIED` | No physical controller benchmark evidence |
| DOC-12 | Persistence/migrations | `DOCUMENTED`; implementation `PARTIAL` | Ordered/journaled migration primitives tested; in-game recovery, reconnect and machine restoration unproven |
| DOC-13 | Validation | `DOCUMENTED`; implementation `PARTIAL` | Profile, symbol, rights, static performance and packaging unit gates exist; live tools and real-action/runtime gates missing |
| DOC-14 | Console testing | `DOCUMENTED`; execution `EXTERNAL_BLOCKED` | Protocol/checklists exist; physical hardware/Realm execution not recorded |
| DOC-15 | Known limitations | `DOCUMENTED` | `docs/known-limitations-marketplace.md` |
| DOC-16 | Corpus methodology | `DOCUMENTED`; corpus `NOT_IMPLEMENTED` | Metrics/splits defined; real legal corpus and holdout absent |
| DOC-17 | User guide | `IMPLEMENTED` for baseline | Existing `docs/user-guide.md`, with Marketplace documents indexed separately |
| DOC-18 | Agent guide | `DOCUMENTED`; operations `PARTIAL` | Initial shared operation registry and stdio adapter pass tests; full operation/MCP surface remains |
| DOC-19 | Reproduction commands | `DOCUMENTED` | `docs/reproduction.md`; baseline-only non-qualification warning included |
| ARCH-01 | Persistent conversion project | `PARTIAL` | Full layout, revisioned store, resume and initial operation subset are unit tested; workflow/catalog incomplete |
| ARCH-02 | Protected custom content | `PARTIAL` | Protected project directories and layout tests exist; full generation-preservation workflow remains unproven |
| ARCH-03 | Clean consumer/build boundary | `PARTIAL` | Marketplace output/no-debug unit tests pass; live candidate archive/tool inspection remains |
| API-01 | Symbol-level stable API validation | `PARTIAL` | Initial catalog and unknown-symbol rejection tested; complete emitted-symbol coverage/source verification absent |
| API-02 | Independent server/server-ui resolution | `IMPLEMENTED` for current catalog | Independent resolution and UI-only dependency tests pass |
| API-03 | Fail-closed event adapters | `PARTIAL` | Unmapped required trigger fails compilation; real Minecraft actions remain untested |
| FRONT-01 | Modern Fabric semantics | `PARTIAL` | Authentic-pattern metadata/source fixture test passes; full API and compiled-JAR qualification missing |
| FRONT-02 | Forge 1.7.10 semantics | `PARTIAL` | Authentic-pattern metadata/manifest/source fixture test passes; full API and compiled-JAR qualification missing |
| FRONT-03 | Compiled-JAR evidence | `PARTIAL` | Controlled fixture parity via `javap`; no general loader-neutral fact model |
| GEN-01 | Baseline BP/RP/script generation | `PARTIAL` | Deterministic scaffolds and profile-aware outputs exist; product fidelity/runtime not qualified |
| GEN-02 | `.mcaddon` generation | `PARTIAL` for production | Deterministic baseline archive and clean Marketplace-output unit checks exist; live candidate qualification is missing |
| GEN-03 | `.mcworld` generation | `NOT_IMPLEMENTED` | No qualifying generator/evidence |
| VAL-01 | Current repository unit suite | `IMPLEMENTED` | 56 tests passed in this documentation verification run |
| VAL-02 | Real-action event integration | `NOT_IMPLEMENTED` | Internal dispatch tests cannot satisfy this gate |
| VAL-03 | Persistence/multiplayer/migration | `NOT_IMPLEMENTED` end-to-end | Required scenario set lacks evidence |
| VAL-04 | Creator Tools suites | `PARTIAL` | Recorded adapter tests pass; no live official-tool candidate run |
| VAL-05 | Performance limits | `PARTIAL` | Static limits/approvals tested; runtime limits and device evidence absent |
| BENCH-A | Original Marketplace showcase | `DOCUMENTED`; implementation `NOT_IMPLEMENTED` | Specification, expected behavior, rights declaration, and checklists only |
| BENCH-B | Rights-cleared real mod | `DOCUMENTED`; implementation `NOT_IMPLEMENTED` | No mod selected; selection criteria explicitly preserve this state; eventual clearance requires human review |
| CON-01 | Local Windows | `UNVERIFIED` | No Benchmark A artifact or run |
| CON-02 | Realm Windows | `EXTERNAL_BLOCKED` | Requires artifact, Minecraft/Realm access, and execution |
| CON-03 | PS4/PS5 | `EXTERNAL_BLOCKED`, `UNVERIFIED` | Requires physical hardware/account/Realm route; no results fabricated |
| CON-04 | Xbox One/Series | `EXTERNAL_BLOCKED`, `UNVERIFIED` | Requires physical hardware/account/Realm route; no results fabricated |
| RIGHTS-01 | Human Marketplace clearance | `EXTERNAL_BLOCKED` | Compiler cannot provide legal authority; no review has occurred |
| MARKET-01 | Marketplace candidate | `NOT_IMPLEMENTED` | Required technical/rights/evidence gates do not pass |
| MARKET-02 | Marketplace submission/approval | `EXTERNAL_BLOCKED` | Microsoft/authorized publishing authority only |

## Documentation completion mapping

All documentation subjects named by the product specification have a dedicated document or existing baseline guide. Console and benchmark files use `UNVERIFIED`/`NOT_RUN` defaults and contain no fabricated evidence. This documentation milestone does not satisfy any production implementation or platform gate by itself.
