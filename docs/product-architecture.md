# Product architecture

## Mission and authority boundary

The product is an AI-assisted Minecraft Java-mod reconstruction and Marketplace-candidate build system. It preserves gameplay intent through Bedrock-native implementations; it is not a JVM, source translator, legal-clearance engine, or Marketplace approval simulator.

The compiler may establish `VALID_MCADDON` and, once every documented gate is evidenced, `MARKETPLACE_CANDIDATE`. Only Microsoft or an authorized publishing workflow can establish `MARKETPLACE_SUBMITTED` or `MARKETPLACE_APPROVED`.

## Required pipeline

```text
Java input
  -> scanner and loader frontend
  -> evidence graph
  -> intent extraction and review
  -> Content IR / Behavior IR
  -> reconstruction planner
  -> target and capability resolution
  -> Bedrock backend
  -> static and runtime validation
  -> rights and performance gates
  -> console benchmark
  -> fidelity and conversion reports
```

Each boundary has a versioned, serializable contract. Semantic claims flow only from evidence or an accepted decision. A backend may not invent behavior to fill an evidence gap.

## Persistent project model

The planned conversion workspace separates durable inputs and decisions from disposable build products:

```text
conversion-project/
  project.yaml
  input/{source,jars,mods,configuration}/
  analysis/{inventory.json,dependency-graph.json,registrations.json,evidence,diagnostics,source-index}/
  ir/{content.json,behaviors.json,state.json,presentation.json,ui-intent.json,networking-intent.json}/
  decisions/{strategies.yaml,overrides.yaml,redesigns.yaml,omissions.yaml,approvals.yaml}/
  rights/{rights-manifest.yaml,evidence,review.yaml}/
  bedrock/{behavior_pack,resource_pack,scripts}/
  custom/{scripts,entities,models,assets}/
  tests/
  runtime/
  console/
  dist/
  reports/
```

`custom/`, accepted decisions, rights evidence, and inputs are protected. Regeneration may replace only declared derived paths. Consumer archives are assembled from an explicit allowlist, never by recursively archiving a project or build root.

## Quality model

Every mechanic is separately scored for gameplay, visual, audio, interaction, controller, multiplayer, persistence, performance, stability, discoverability, feedback, and update compatibility. Its outcome is one of `IMPROVED`, `PARITY`, `ACCEPTABLE_REDESIGN`, `DEGRADED_WITH_APPROVAL`, `MANUAL_REDESIGN_REQUIRED`, or `UNSUPPORTED`.

No decorative substitute is a functional conversion. No required behavior may disappear silently. `IMPROVED` and `PARITY` require evidence; degradation requires an explicit decision; unsupported behavior remains visible in final reporting.

## Current baseline boundary

The current worktree provides persistent-project operations, target/profile and symbol checks, authentic-pattern Fabric/Forge source and JAR fixtures, rights/performance/persistence governance, protected custom implementation integration, official Creator Tools execution, and isolated BDS diagnostics. Benchmark B also contains deterministic pure migration logic, while real Minecraft execution of that migration remains unverified. These are substantial product foundations, not end-to-end qualification. Broad loader semantics, real player-action adapters, completed gameplay benchmarks, measured device performance, human rights clearance, and console verification remain unproven. See [requirement-traceability.md](requirement-traceability.md).
