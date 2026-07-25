# Reconstruction Skill Pack

This directory is the repository-tracked gold copy of the reusable Codex
workflows used by the Java-to-Bedrock reconstruction system.

## Included roles

- `translate-java-mods-to-bedrock`: campaign controller, evidence abstraction,
  contract transfer, sandbox enforcement, qualification, and final claims.
- `produce-bedrock-cleanroom-feature`: bounded evidence-blind feature owner.
- `integrate-bedrock-subsystem`: evidence-blind dependency-wave integration.
- `audit-java-bedrock-cleanroom`: post-freeze semantic, originality, lineage,
  isolation, determinism, and BDS audit.
- `blockbench-build-bedrock-assets`: original Bedrock asset construction and
  qualification.
- `produce-golden-blockbench-asset`: evidence-blind custom visual production.
- `audit-golden-blockbench-asset`: post-freeze visual and originality audit.

## Process-level clean-room rule

Context isolation is necessary but insufficient. Every production and repair
agent must execute through the recorded filesystem sandbox. A valid receipt
binds the process ID, command, sandbox launcher/profile/environment hashes,
prompt/context hash, tool hashes, inputs, outputs, timestamps, exit status,
negative-access checks, candidate commit, and package hashes.

Contamination scans prove only that prohibited expression was not detected.
Clean-room success additionally requires evidence that copying was technically
prevented during every authoring and repair process.

Before another large campaign, run the one-feature sandbox rehearsal described
in `translate-java-mods-to-bedrock/references/production-sandbox.md`.

## Bedrock qualification rule

Static validation, Creator Tools, Stable BDS, Preview BDS, desktop client,
Realm, controller, split-screen, and physical PS4 results remain separate.
BDS-only schema failures must become generator regressions and rejection
mutations. Historical tests remain bound to immutable candidates and use
`SUPERSEDED_ASSERTION` when a later repair makes their path or hash obsolete.

The repository copy is authoritative for review and version history. Install
or refresh the complete pack from a fresh clone with:

```sh
python3 tools/bootstrap_pipeline.py --check-only --json
python3 tools/bootstrap_pipeline.py --json
```

The installer refuses to overwrite divergent installed skills unless
`--replace-skills` is supplied; replaced copies are retained in a timestamped
backup. See `docs/bootstrap.md` for the complete portable setup.
