# Dependency, rights, and rollback

The feature is dependency-closed: Bedrock packs, stable `@minecraft/server` 2.0.0, and repository-local build/qualification code only. It does not depend on Mossback Forager or any other Forest Wave feature.

All shipped production expression in this slice is newly authored for this project. No Java implementation, third-party model, texture, animation, sound file, recipe, code, lore, or identifier was used. The built-in `random.orb` sound is referenced as temporary platform-provided presentation; no sound binary is redistributed.

Contamination scan target: namespace, source, manifests, generated packs, and editable assets. Expected finding: no Java-fidelity marker and no third-party production material.

Rollback before publication is local and recoverable:

1. Preserve any unrelated working-tree files.
2. Switch to parent commit `e25c151d9a434a067eda3de2a94a42bbb4d16fba`.
3. Delete the local feature branch only after confirming the checkpoint commit is no longer needed.
4. Remove imported internal test packs/worlds from the test client manually; no Realm or public deployment exists.
