# Gameplay distillation and production-planning operations

This milestone separates source evidence from production-facing design. The
authoritative flow is:

`evidence → gameplay intent → rights filter → clean-room contract → experience graph → production wave`

The command and AI-operation surfaces use the same project, parameter, revision,
diagnostic, and artifact envelopes as other conversion-project operations.
Human-readable CLI output is the default; `--json` emits the unchanged operation
response. Success exits `0`; validation or policy failure exits `2`.

## Commands and operation names

| CLI command | AI operation | Purpose |
| --- | --- | --- |
| `create-rights-strategy` | `create_rights_strategy` | Create the default clean-room strategy or a fully evidenced authorized-adaptation strategy. |
| `register-rights-material` | `register_rights_material` | Register one material-level rights record. |
| `inspect-rights-material` | `inspect_rights_material` | Inspect a material record and its production disposition. |
| `build-gameplay-intent` | `build_gameplay_intent` | Derive auditable, abstract Gameplay Intent IR from evidence. |
| `validate-gameplay-intent` | `validate_gameplay_intent` | Validate evidence dispositions, confidence, rights states, and dependencies. |
| `export-clean-room-contract` | `export_clean_room_contract` | Export only production-allowlisted abstract fields. |
| `screen-product-similarity` | `screen_product_similarity` | Detect similarity risk without implying legal clearance. |
| `build-experience-graph` | `build_experience_graph` | Build the acceptance graph used for experience selection. |
| `calculate-experience-coverage` | `calculate_experience_coverage` | Calculate coverage against the acceptance graph. |
| `plan-production-wave` | `plan_production_wave` | Produce a bounded production-wave plan. |
| `validate-production-plan` | `validate_production_wave` | Validate scope, prerequisites, originality, cost, and qualification gates. |
| `show-production-plan` | `show_production_wave` | Read the current plan without mutating project state. |

Every command accepts `--project`. Mutating commands also accept
`--expected-revision`. Structured parameters are supplied with
`--parameters <json-file>`; `-` reads the parameter object from standard input.
Paths in requests and results are project-relative unless they identify the
project itself.

```sh
mccompiler create-rights-strategy \
  --project out/forest-project \
  --parameters rights-strategy-request.json \
  --expected-revision 3 \
  --json

mccompiler operation --request clean-room-export-operation.json
```

The equivalent AI request remains the canonical machine envelope:

```json
{
  "schema_version": "1.0.0",
  "request_id": "forest-clean-room-export-1",
  "operation": "export_clean_room_contract",
  "project": "out/forest-project",
  "expected_revision": 7,
  "parameters": {
    "intent_id": "analysis:forest_regional_charger"
  }
}
```

## Safety boundary

Analysis evidence, rights records, restricted expressions, source names, raw
source paths, restricted URIs, and third-party assets remain outside production
contracts. A failed allowlist, taint, rights, similarity, prerequisite, or
qualification check returns a stable diagnostic with remediation and does not
advance the project revision.

Similarity screening is risk detection only. `AUTOMATED_SCREEN_LOW_RISK` is not
legal clearance. Production planning stops at deterministic contracts and does
not authorize content production, Marketplace submission, or physical-platform
claims.

## Rights modes and material records

`clean_room_originalization` is the default because source access is not
permission to reuse source expression. It permits abstract gameplay-pattern
analysis while prohibiting third-party names, branding, distinctive expression,
and assets in production. `authorized_adaptation` is exceptional and fails
closed until material-level records prove commercial use, derivatives,
Marketplace distribution, and any applicable trademark permissions.

The ledger records code, binaries, models, textures, animation, audio, writing,
characters, structures, dependencies, documentation, and runtime observations
separately. A permissive code license does not license art. Unknown ownership,
noncommercial restrictions, incomplete commercial rights, and ambiguous
third-party content block direct production reuse. These automated rules support
review; professional legal review remains necessary.

## Analysis and production separation

Analysis-side evidence, rights ledgers, and Gameplay Intent IR remain under
`analysis/`. Production contracts, originality records, screening reports,
experience reports, and wave plans remain under `production/`. Consumer
assembly may consume approved production and generated paths only.

Gameplay Intent IR records abstract role, fantasy, loops, combat, exploration,
reward function, progression, multiplayer, persistence, cleanup, performance,
and dependencies. Each claim uses `observed`, `inferred`, `selected`,
`redesigned`, `omitted`, or `unknown`, with evidence references, bounded
confidence, and concise audit rationale. Rights dispositions distinguish source
access, reusable expression, abstract mechanic reuse, direct reconstruction,
commercial asset rights, and the clean-room transition.

Taint labels make the boundary enforceable:

- `ANALYSIS_ONLY`, `RESTRICTED_EXPRESSION`, and `BLOCKED` cannot enter production.
- `ABSTRACTED_MECHANIC` may cross only through the exporter.
- `AUTHORIZED_FOR_PRODUCTION` requires evidenced authorization.
- `CLEAN_ROOM_ORIGINAL` marks independently created production expression.

The clean-room allowlist transfers generic gameplay role and patterns,
difficulty/progression functions, environmental family, performance limits,
multiplayer/persistence requirements, originality constraints, and
qualification requirements. It rejects source names, paths, evidence URIs,
hashes, assets, lore, localization, distinctive layouts/rewards, and instructions
to recreate named source material.

## Originality and similarity screening

Each future product element needs an originality record covering its seed,
design-profile revision, restrictions, independently created expression,
abstract mechanics retained, expression replaced, provenance, known
similarities, revisions, and screening status. Bramblehorn’s existing
Blockbench source, exports, asset registry, Creator Tools receipt, stable-BDS
receipt, and readiness matrix are admissible evidence; unavailable history must
remain `unknown`.

Similarity screening compares only supplied evidence for names, silhouette,
palette, texture/model hashes, structure layouts, phase ordering, reward
identity, text, progression, and distinctive combinations. Outcomes are risk
signals: `AUTOMATED_SCREEN_LOW_RISK`, `HUMAN_REVIEW_REQUIRED`,
`REVISION_REQUIRED`, `OMIT_PENDING_LICENSE`, or `SCREENING_INSUFFICIENT`.
Coverage gaps remain explicit. No outcome is legal clearance.

## Experience graph and deterministic waves

Acceptance graphs weight product experiences, declare dependencies, and specify
the evidence level required for acceptance. Weighted coverage is accepted
weight divided by total weight in basis points; dependency failures remain
blockers even when a child’s own evidence is strong.

Production-wave planning is deterministic: dependency-ready elements are
ordered by evidence, priority, and stable identifier, then admitted only while
preserving the authoritative 62/80 scope and its 18-unit reserve. The PS4 proxy
also exposes hard caps for script tick work, active entities, pathfinding,
projectiles, particles, texture memory, geometry, animation controllers,
persistence growth, multiplayer multiplication, cleanup latency, and the worst
credible scene. One hard-cap failure cannot be hidden by the composite score.
Deferred elements are reported, not silently dropped. A plan is a planning
contract, not authorization to make content.

The forest walkthrough is:

`signal ruin → three regional roles → two equipment upgrades → forest elite → persistent unlock → bounded chaos → repeatable trail reward loop`

Bramblehorn enters as server-qualified evidence for the regional-creature
experience; Mossback Forager, Gloamwing Stalker, Resonance Sling, Barkguard
Charm, Signal Ruin, Thornwarden Elite, Forest Attunement, Sporefall Event, and
the Renewed Trail Loop remain contract-only until their own evidence exists.
Bramblehorn's desktop-client, multiplayer-persistence, and physical-PS4 checks
remain pending. The PS4 model is a conservative planning proxy, never
physical-console proof.

## Adversarial refusals

Operations fail without mutation when asked to launder source names or
restricted references, treat unknown or noncommercial rights as reusable,
export prohibited taint, declare legal clearance, invent evidence, exceed
planning caps, ignore dependencies, start broad production, submit to
Marketplace, or promote server/proxy evidence to physical PS4 qualification.
