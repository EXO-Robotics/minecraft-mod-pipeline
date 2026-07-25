# Bedrock, console, and Marketplace gates

Use current official documentation before implementation or eligibility claims:

- Custom entity introduction: https://learn.microsoft.com/en-us/minecraft/creator/documents/introductiontoaddentity
- Cooperative add-on guidelines: https://learn.microsoft.com/en-us/minecraft/creator/documents/practices/guidelinesforbuildingcooperativeaddons
- Creator documentation home: https://learn.microsoft.com/en-us/minecraft/creator/
- Marketplace partner program: https://www.minecraft.net/en-us/partner

## Engineering defaults

- Keep a canonical asset ID and, when needed, record its explicit binding to the creator-project runtime namespace.
- Use the creator-project runtime namespace consistently in geometry, client entity, animation, animation controller, render controller, behavior entity, files, and localization keys.
- Put entity textures under `textures/<creator_project>/entity/`, loot tables under `loot_tables/<creator_project>/entities/`, and functions under `functions/<creator_project>/<game_or_asset>/`.
- Put block and item textures under
  `textures/<creator_project>/<game_or_asset>/blocks/` and `items/` when the
  active cooperative profile rejects loose top-level `textures/blocks` or
  `textures/items` folders.
- Declare a suitable `min_engine_version`.
- Set resource-pack `pack_scope` to `world` when required by the current Creator Tools profile.
- Declare corresponding resource/behavior pack UUID dependencies. If the active Creator Tools profile requires reciprocal dependencies, validate that exact relationship rather than assuming one-way linkage is enough.
- Avoid experiments, vanilla overrides, and `runtime_identifier`.
- Keep behavior server-authoritative so multiplayer clients agree.
- Keep packs comfortably below current published file-count and uncompressed-size guidance.
- Bound pathfinding entities, ticking blocks, scripts, particles, translucent surfaces, and simultaneous animations.
- Test on the weakest target console, not just a development Mac or Windows PC.
- Use one render method for all faces in a material-instance group and every
  finish permutation. Do not mix `opaque` with `blend` or other transparent
  pipelines in the same block definition. A fully opaque texture can still look
  solid while using the group's common transparent pipeline.

## Frozen-package qualification

Build the `.mcaddon` deterministically with stable entry ordering, timestamps, and permissions. Run current Creator Tools `addon` and `currentplatform` checks against that exact file. Preserve:

- Creator Tools version and profile.
- Commands, exit codes, stdout, and stderr.
- Frozen package SHA-256.
- Input and report hashes.

An offline Creator Tools CLI may emit a network/debug prelude even when local validation succeeds; preserve the complete log and classify by the command exit code and structured findings.

After any package-affecting edit, rebuild and rerun all package gates. Do not promote when the frozen package SHA differs from the SHA in a Creator Tools or BDS receipt.

## Rights defaults

- Keep a provenance ledger for source files and references.
- Create models, textures, animation, sounds, names, and lore from scratch or use assets with documented commercial redistribution rights.
- Preserve a broad mechanic or genre idea only; do not reproduce distinctive expression.
- Marketplace acceptance is a review outcome, not a property that can be certified locally.

## Readiness language

Use:

- “Blockbench-valid” after source/editor inspection.
- “Bedrock desktop-tested” after a clean-world runtime test.
- “PS4-tested” only after physical hardware verification.
- “Marketplace candidate” before submission.
- “Marketplace approved” only after confirmed approval.

Creator Tools success establishes content-profile compliance for the tested artifact; it does not establish gameplay correctness, console performance, physical PS4 compatibility, or Marketplace approval.

Creator Tools and BDS are complementary. A package can pass `addon` and
`currentplatform` yet fail BDS component loading. Require zero BDS content-log
errors for materials, manifests, components, and scripts before promotion.
