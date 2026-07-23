# Callable operations

The versioned registry and JSON-lines agent adapter expose registered handlers in these groups. “Callable” means dispatchable, not guaranteed to succeed without project state, artifacts, authorization, or runtime infrastructure.

| Group | Questions and structured results | Judgment still required |
|---|---|---|
| Project | Create/open; status; unresolved work; blockers; next task. Returns revision, diagnostics, artifacts, provenance. | Priority and approvals |
| Analysis | Scan mod/modpack; list/inspect mods, content, behavior, state, assets, mixins, coremods, packets and GUIs; trace dependencies/callers/callees; show evidence; compare source/JAR. | Meaning of incomplete or dynamic Java behavior |
| Intent | Extract/propose/accept/edit/reject intent; list ambiguity/unsupported features. | Player-facing intent and ambiguity resolution |
| Planning | Compare strategies; plan feature; set/accept/reject strategy/approximation; record redesign; select pattern; apply override; estimate fidelity/performance. | Whether an approximation is acceptable |
| Generation | Generate item, block, entity, projectile, recipe, loot, structure, spawn rule, animation, form, script scaffold, packs, world, and package. | Protected custom behavior and original design |
| Validation | Validate IR/API/target/rights/static/scripts/assets/performance; install/start runtime; behavior/multiplayer/persistence checks; inspect logs; compare expected; report. | Interpreting physical usability and release fitness |
| Safe editing/reporting | Protected implementations, patterns, provenance patches, mappings, rights evidence, quality and Marketplace-candidate reports. | Authority, rights, and publication decisions |
| Distillation | Inventory identity; cluster; score value/effort/console/pattern/progression; select quarter; explain; roadmap; record review adjustments. | Input quality, commercial taste, originality, final scope |

Structured envelopes prevent hallucination by carrying stable IDs, project revision, diagnostics, artifacts, and provenance. State-gated operations fail explicitly rather than fabricating results. See `src/mccompiler/operations/registry.py`, `src/mccompiler/agent/stdio_server.py`, and `tests/test_agent_operation_catalog.py`.
