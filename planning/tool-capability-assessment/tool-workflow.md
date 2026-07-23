# Tool workflow

| Stage | Inputs → outputs | Modules and operations | Mode, validation, failure evidence | Maturity |
|---|---|---|---|---|
| Project | Path/profile → revisioned project | `project/store.py`, `create_project`, `open_project`, status/blockers/next-task | Deterministic; optimistic revisions and diagnostics | Proven by tests |
| Scan/inventory | Java source, supported JAR, or supplied modpack manifest → files, loader registrations, content and hashes | `scan.py`, `frontends/*`, `scan_mod`, `scan_modpack`, list/inspect operations | Deterministic recognized-pattern extraction; unknown constructs retained as evidence | Representative Fabric/legacy Forge and bounded JAR vocabulary only |
| Evidence/dependencies | Scan facts → stable IDs, provenance, calls/dependencies | query/analysis operations; javap/bytecode facts | Deterministic focused queries; missing source, tools, symbols, or unsupported bytecode produce diagnostics | Proven for fixtures, not arbitrary ecosystems |
| Behavior/state model | Evidence + proposals → Behavior IR/ModIR and ambiguity | `ir.py`, schemas, intent operations | AI proposes; acceptance is separate and revisioned; schema/provenance validation | Implemented; semantic completeness remains feature-specific |
| Planning | Accepted intent + target catalogs → strategy, risk, estimates | `planner.py`, `pattern_catalog.py`, planning operations | Catalog-driven comparison plus AI judgment; approval required for approximations | Implemented; catalogs are not runtime proof |
| Generation | Accepted plan/IR → BP/RP/script/form/world scaffolds | `bedrock.py`, generation operations | Deterministic outputs; protected custom handlers are not overwritten | Tested; breadth varies by frontend/feature |
| Validation | Outputs → schema/API/static/assets/performance/rights reports | `validate.py`, `creator_tools.py`, `marketplace.py`, `performance.py`, `rights.py` | Fail-closed diagnostics and artifact hashes; rights records do not grant rights | Proven static pipeline |
| Runtime | Hash-bound packs/world → BDS logs and behavior receipts | `runtime/bds.py`, `runtime/evidence.py`, runtime validation operations | Authorized local BDS adapter; stable/Preview evidence; no physical-client automation | Bounded benchmark proof |
| Fidelity/rights | Expected behavior + evidence → gaps, decisions, blockers | quality, rights, marketplace and reporting operations | AI/human review; human-only rights approval | Process implemented, clearance absent |
| Packaging | Valid packs/world → `.mcaddon`/`.mcworld` | backend/package operations | Deterministic clean packaging and Creator Tools invocation | Exact benchmark archives proven |

Architecturally present but not real-input proven includes broad loader coverage, arbitrary compiled control-flow recovery, complete cross-mod API semantics, general GUI conversion, and console execution. A successful package or BDS boot is not gameplay qualification.
