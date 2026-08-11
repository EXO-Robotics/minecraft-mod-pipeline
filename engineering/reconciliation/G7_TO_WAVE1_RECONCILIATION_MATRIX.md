# G7 → Wave 1 Reconciliation Matrix

Authority: G7 commit `042018eac3bd32b76d135219b9f59502dd4f4692`, tree `5542639f4c1a932ff1f354dee07dfe448b6491bd`.

This matrix owns successor disposition. `KEEP` preserves a proven pattern; `REFINE` repairs or extends it; `REPLACE` substitutes approved Wave 1 content while retaining no identity promise; `SUPERSEDE` removes an older product identity from the active Wave 1 surface; `DEFER` keeps it out of Wave 1 until authority exists.

| G7 system | G7 evidence | Disposition | Wave 1 action / exit condition |
|---|---:|---|---|
| Immutable lineage and source-byte ledger | commit/tree, package hashes, ledger | KEEP | Preserve exact G7 parent and issue a new successor generation only. |
| BP/RP reciprocal manifests | one BP, one RP, Script API 2.0.0 | REFINE | Preserve UUID lineage, increment successor versions, keep stable API only. |
| Deterministic pack builder | two-build equality independently reproduced | KEEP | Make generation parameter explicit; outputs and receipts must be evidence-derived. |
| Frozen G7 dist | exact G7 packages | SUPERSEDE | Never rewrite; successor builds use new names/hashes. |
| Runtime bootstrap | literal `scripts/main.js`, marker | REFINE | Preserve minimal bootstrap; generation-specific marker; exact packaged-entrypoint test. |
| Runtime composition | service factory in `runtime.js` | KEEP | Extend through composed services; no global router redesign. |
| Interaction router | discovery/actions compose; G6 early-return class closed | KEEP | Add Wave 1 routes without reintroducing early return or handler suppression. |
| Catalog/identity registry | G7 routes, items, encounters | REPLACE | Normalize approved packet IDs to `aionbound:<warehouse_id>`; migrate retained G7 IDs explicitly. |
| Persistence schema v3 | world/player migrations, journals, encounters | REFINE | Extend idempotently for Wave 1 discovery, ownership, rewards, equipment, and endgame; preserve old semantics. |
| Runtime arbiter and budgets | explicit query/edit/entity/effect caps | REFINE | Retain as baseline evidence; tune locality/spawn scheduling before raising caps. |
| Chaos outcomes | 18 outcomes, bounded service | REFINE | Correct at-most-once terminology and crash-window behavior; retain guards and caps. |
| Chaos temporary block budget | cap says 48, implementation offsets 4 | REFINE | Align declared and effective budgets; prove cleanup semantics with targeted tests. |
| Codex state model | topic/stamp/goals persistence | KEEP | Reuse schema and discovery stamps. |
| Codex presentation/content | chat-driven G7 pages | REPLACE | Populate approved creatures/plants/resources/structures/equipment/bosses and replace chat spam as primary UX. |
| Combat/equipment service | weapon, armor, accessory effects | REFINE | Rebind to Packet 006, two-accessory cap, provenance, durability/repair, and lateral roles. |
| Existing G7 items (56) | registered and packaged | REPLACE | Retain only explicitly mapped infrastructure/utility identities; Packet 006 and approved ecosystem items own active content. |
| Existing G7 weapons (10) | archetype framework | REFINE | Reuse safe behavior patterns; approved Packet 006 weapons own names/art/progression. |
| Existing armor (8) | equipment framework | REFINE | Expand to approved 10 pieces and bind set identity without pure stat laddering. |
| Existing accessories (6) | functional offhand roles | REFINE | Expand/replace with approved 10 and cap concurrent effects at 2. |
| Trophy Edge | G7 item and assembled geometry | REFINE | Preserve item `aionbound:trophy_edge`; rebuild acquisition/ignition against four seals and Twinbond authority. |
| Existing entities (24) | behavior JSON, geometry, animations | SUPERSEDE | Approved 40 packet creatures own Wave 1 ecology; retain only explicitly mapped behavior architecture, not cast identity. |
| Entity AI/motion patterns | movement/navigation/combat on selected entities | REFINE | Role-specific ambient/neutral/hostile/aerial behavior; no generic statue completion. |
| Generic generated animations | idle/action emitted broadly | REPLACE | Bind role-correct clips only; static blocks/items do not inherit fake animation completion. |
| Existing bosses / boss ladder | admission, ownership keys, reward guards | REPLACE | Retain admission/guard architecture; approved four apex identities and ticketed envelopes own content. |
| G7 Twinbond pair | Ash/Tide composition | DEFER | Do not treat as approved finale; replace only after `W1-CREATIVE-002` resolves exact inputs. |
| Existing blocks (49) | packaged registry | REFINE | First repair 32 Stable-BDS geometry/material pairs; then map/replace with approved ecosystem blocks. |
| Resource-pack block bindings | terrain texture/material references | REFINE | Close every BP/RP block reference and preserve one compatible render method per material group. |
| Feature definitions (33) | ore/structure distribution framework | KEEP | Reuse feature architecture where compatible. |
| Feature rules (33) | worldgen placement rules | REFINE | Repair 19 filename/identifier mismatches; retune to approved spacing/density/biome identity. |
| Natural spawn rules (10) | bounded registry presence | REPLACE | Approved 40-creature ecology owns rules; registry density remains separate from loaded density. |
| Authored structures (15) | `.mcstructure` pipeline | REFINE | Reuse structure loading/generation; replace encounter identity with approved 40 props/structure roles. |
| Structure runtime service | queued placement/reward framework | KEEP | Preserve bounded queue, locality, reward guards; rebind sites and loot identities. |
| Pocket/cell generation | bounded owner-aware cell jobs | DEFER | Keep out of active Wave 1 path unless the contract explicitly consumes it. |
| Stripvein utility | bounded edit jobs/cooldown | DEFER | Keep only if Packet 006 tool/progression mapping approves it. |
| Technology devices (3) | salvage, press, survey | DEFER | Preserve code as evidence; reintroduce only through approved equipment/progression relationships. Foundry stays held. |
| Loot tables (32) | valid static table infrastructure | REPLACE | Approved ecosystem/boss identities and `W1-CREATIVE-004` ranges own final economy. |
| Recipes (55) | recipe infrastructure and unlock shape | REPLACE | Rebuild coherent approved resource→component→equipment graph; remove dead/colliding legacy recipes. |
| Recipe registration after Gate 0 | 12 recipes fail downstream of invalid blocks | REFINE | Repair block registration first, then require affected recipe closure. |
| Item icons and inventory presentation | mixed final/placeholder G7 art | REPLACE | Packet design language and normal Bedrock UI readability own shipping presentation. |
| Attachable/render-controller framework | 32 attachables, shared controllers | KEEP | Reuse only after exact geometry/texture/animation identity normalization. |
| Localization | G7 names/text | REFINE | Replace active content strings with approved Wave 1 identities and useful Codex language. |
| Sound bindings | mostly existing/vanilla behavior cues | REFINE | Bind role-appropriate approved/existing sounds; missing original audio becomes support, not invented proof. |
| Progression spine | G7 pilgrimage/endpoint beta | REPLACE | Bind Spawn→WW→AH→CM→SR→Pilgrimage→Trophy Edge→Twinbond while preserving sandbox freedom. |
| Encounter reward persistence | active/terminal journals | REFINE | Preserve idempotent guards; bind per-player/world semantics after boss ticket resolution. |
| G7 semantic test suite | 14 focused tests pass | REFINE | Retain safe semantics, add crash-window and Wave 1 route coverage, correct packaged-entrypoint naming. |
| Stale G6 Python suite | 5/5 fail and invokes legacy mutating build | SUPERSEDE | Quarantine/retire or adapt; never include in default successor discovery unchanged. |
| Literal packaged-entrypoint proof | current test transforms source | REPLACE | Extract exact built archive and execute its shipped entrypoint with production-equivalent mocks. |
| Producer validators | counts/static closure | REFINE | Derive results from captured checks; add Stable-BDS defect classes missed by static admission. |
| Declarative PASS receipts | hardcoded PASS/count facts | REPLACE | Generate receipts from evidence and reject mutation/hardcoded success. |
| Mechanical admission | exact Git extraction, hashes, JSON/API checks | KEEP | Retain as narrow pre-BDS gate; extend with packaged-media decode and block/feature schema checks. |
| Client/controller/PS4/Realms/Marketplace | not run | DEFER | Remain manual/external gates; never inherit from BDS. |

## Gate 0 successor defects

The exact G7 package reached ready state, emitted the shipped marker, shut down cleanly, and reopened the same world in two Stable BDS cycles. Substrate classification nevertheless failed with the same defect classes in both cycles:

- 32 missing geometry/material-instance pairs plus 32 block parse failures;
- 19 feature-rule identifier/filename mismatches;
- 32 downstream recipe diagnostics across 12 recipes.

These are successor `REFINE` work. G7 remains immutable.

## Integration ownership

- Integration owner: `codex/aionbound-wave1-g8-integration`.
- Subagent branches may produce commits but may not declare packages or candidates.
- The integration owner cherry-picks reviewed commits only after scope and tests are verified.
- Final freeze is blocked while any Phase 0 support ticket remains open.
