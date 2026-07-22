# Architecture Proposal

The long-term project can be split into three logical repositories, but the
baseline keeps them together so the contract is exercised end to end.

```text
minecraft-compiler-core
  ModIR, evidence graph, planner, patterns, fidelity model

minecraft-frontends
  metadata, JavaParser, ASM, Forge, NeoForge, Fabric, Quilt, assets, traces

minecraft-bedrock-backend
  behavior pack, resource pack, Script API, GameTest, validation, packaging
```

## Baseline pipeline

```text
Input JAR/source/modpack
  -> Scanner frontend
  -> ModIR + evidence paths
  -> Capability planner + Pattern Library
  -> Bedrock backend scaffold
  -> Static validator
  -> Runtime/GameTest validator
  -> fidelity report
```

## Stable contracts

### Evidence

Every extracted fact should include:

- source archive/path
- source kind: metadata, asset, source, bytecode, runtime, human
- confidence
- extraction rule
- unresolved references

### Behavior IR

The next IR revision should add:

```yaml
behavior:
  id: example_mod:projectile_item
  trigger: item_use
  actor: player
  conditions:
    - sneaking
  actions:
    - spawn_projectile
  state:
    cooldown_ticks: 40
  evidence: []
  confidence: proposed
```

### Strategy plan

Each feature receives one of:

`DIRECT`, `SCRIPTED`, `RECONSTRUCTED`, `APPROXIMATED`, `MANUAL`, `UNSUPPORTED`.

The plan must record why the strategy was selected and which Bedrock capability or
pattern justified it.

