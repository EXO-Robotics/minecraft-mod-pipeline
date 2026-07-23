# Dependency, rights, provenance, and rollback

## Dependency closure

The feature depends only on Bedrock behavior/resource packs, stable `@minecraft/server` 2.0.0, native item/projectile components, and repository-local build/qualification code. The Preview GameTest pack is explicitly `never_ship` and is not included in either importable production artifact. No Mossback Forager or other Forest Wave feature is required.

## Originality and provenance

All production expression in this slice is newly authored for this project:

- Sling and projectile names, role, recipe, values, and localization.
- Editable Blockbench models and native Bedrock geometry exports.
- Item, entity, and projectile textures and icon.
- Sling animation and controller.
- Impact particle.
- Behavior definitions, functions, recipes, scripts, tests, and reports.

No Java implementation, third-party model, texture, animation, sound, recipe, code, lore, identifier, or distinctive expression was used. No sound file ships in this slice. Authoring evidence is recorded in `prototypes/blockbench/resonance_sling/originality-and-authoring.json`.

Contamination scan scope: production namespace, manifests, generated packs, scripts, reports, editable assets, and archives. Required result: no Java-fidelity marker, third-party production material, Forge/Fabric/Mixin runtime assumption, external service, or experimental API in the shipped packs.

## Rollback

Rollback is local and recoverable:

1. Preserve unrelated working-tree files, especially `prototypes/blockbench/phase_anchor_test.bbmodel`.
2. Retain the checkpoint commit hash from `checkpoint-manifest.json`.
3. Switch to parent baseline `e25c151d9a434a067eda3de2a94a42bbb4d16fba` only if the entire feature must be removed.
4. Delete the local feature branch only after confirming the checkpoint is no longer needed.
5. Remove imported internal-test packs/worlds manually from test clients. No Realm, push, tag, publication, or release exists.
