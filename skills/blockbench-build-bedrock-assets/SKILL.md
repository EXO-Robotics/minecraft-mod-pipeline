---
name: blockbench-build-bedrock-assets
description: Create, remake, animate, path, export, and validate original low-poly assets in Blockbench for native Minecraft Bedrock add-ons, including blocks, entities, animals, bosses, trees, props, items, textures, geometry JSON, animation controllers, and server-authoritative AI. Use when Codex needs to implement a clean-room Java-mod reconstruction contract, replace restricted Java-mod assets, preserve an abstract gameplay role without copying protected expression, automate or operate Blockbench, add console-conscious animation or pathfinding, prepare Bedrock resource/behavior pack files, or assess PS4 and Minecraft Marketplace readiness.
---

# Build Bedrock Assets in Blockbench

Create original assets that retain a gameplay role or broad theme without copying a third party's model, texture, name, lore, sound, animation, or other distinctive expression. Treat every result as a Marketplace candidate until it passes Microsoft review and physical-console testing.

For custom geometry or material visual work, read
`references/golden-cleanroom-pipeline.md` before writing the production brief.
Use the Golden pipeline for typed visual contracts, native round-trip evidence,
fixed proof views, computed heuristics, two critique cycles, art-direction
scoring, and originality repair.

## Start with the asset brief

Record:

- Asset class: block, attachable/item, static prop, entity, animal, boss, tree, or biome kit.
- Gameplay role and silhouette goals.
- Original name and a unique lowercase namespace.
- Required states, animations, sockets/locators, sounds, drops, spawning, and interactions.
- Target texture size and conservative geometry/animation budgets.
- Provenance for every model, texture, sound, and reference.
- A class-specific typed visual contract and fixed proof-render contract when
  the asset has custom geometry, rigging, animation, or material art direction.

When the asset belongs to a Java-mod reconstruction, accept only the
consumer-safe clean-room design contract, opaque Gameplay Intent ID,
originality constraints, Bedrock output contract, and console budget as
production inputs. Reject source paths, evidence URIs, decompiled material,
restricted hashes, Java asset files, source identities, or analysis-ledger
references. Do not browse analysis evidence while authoring the asset.

Keep the reconstruction evidence state separate from the asset gate. A planning
contract does not authorize model production; require its rights disposition
and originality requirements. Report Blockbench and asset validation results
back to the reconstruction wave without advancing BDS, desktop, or physical PS4
statuses.

Preserve abstract function only when remaking licensed material. Change the silhouette, proportions, construction, surface language, palette, naming, animation personality, and lore. Do not trace or recolor the source asset.

## Choose the native Bedrock form

- Use a Bedrock Block project for full-cube or custom block geometry.
- Use a Bedrock Entity project for mobs, animated props, bosses, and complex plants.
- Use an attachable or item pipeline for held/worn assets.
- Split biome work into reusable blocks, plants, entities, particles, sounds, and world-generation configuration; a biome is not one Blockbench file.

Prefer the simplest representation that supports the intended gameplay. Read `references/bedrock-marketplace-gates.md` before deciding the file set or claiming console readiness.

Do not create a Blockbench project merely to satisfy a checklist. For ordinary
full-cube blocks, simple collision variants, and flat item icons that need only
original 16x16 textures, use native block/item JSON and record Blockbench as
`NOT_APPLICABLE` with a reason. Use Blockbench only when custom geometry,
attachables, locators, rigging, UV layout, or animation materially supports the
approved function.

For Java-mod-to-Bedrock work, use
`$translate-java-mods-to-bedrock` to perform evidence intake, rights
classification, Gameplay Intent distillation, and wave orchestration. This skill
owns only original asset production and its asset-specific validation gates.

## Build the source model

1. Create an original concept sheet or written shape grammar.
2. Set a small texture atlas: usually 16x16 or 32x32 for blocks and 32x32 or 64x64 for entities.
3. Construct geometry from a restrained number of cubes.
4. Name groups and bones semantically.
5. Put pivots at real joints; test rotations before adding animation.
6. Add only locators required by particles, held items, riders, projectiles, or attachments.
7. Keep UV islands readable and avoid unnecessary transparency or high-frequency noise.
8. Save the editable `.bbmodel` as source, but do not ship it as the runtime format.

Use native-shaped UUIDs and resolve all element, group, animator, and keyframe
links. Bind every textured face to the declared atlas. A JSON file that parses
but cannot survive Blockbench reopen/save/reopen is not a valid source model.

For UI operation, use the `computer-use:computer-use` skill. Re-inspect the current app state before every action. Open models through Blockbench's File menu when Finder double-click or direct app launch is unreliable. For repeatable automation, prefer a Blockbench plugin or explicit native export over depending on undocumented `.bbmodel` internals. Read `references/blockbench-automation.md`.

Never represent a locator as a named group or empty bone. In `.bbmodel`, create a real locator element and place it in the intended outliner bone. A convincing editor hierarchy is insufficient: native export is the authority.

Shared serializers must emit nested outliner group objects and native locator
elements. Reject flattened UUID-only hierarchies. Validate all references
recursively and detect cycles before export.

## Export native Bedrock geometry

Export with Blockbench's native Bedrock geometry exporter and retain the editable `.bbmodel` separately.

First reopen the `.bbmodel` in Blockbench, use **File > Save Project**, then export geometry and animations through their native codecs. Keep source and native exports separate. Compare expected and exported bone, cube, and locator counts; inspect `minecraft:geometry[].bones[].locators` directly.

Verify:

- `format_version` is supported by the target Bedrock release.
- The geometry identifier is namespaced and intentional.
- Texture width and height match the source atlas.
- Bone parents exist and no parent cycle is present.
- Cube UV rectangles fit within the atlas.
- Pivot and rotation values are finite.
- No Java-only model, rendering, mixin, Forge, or Fabric assumption remains.

Run:

```bash
python3 scripts/validate_bedrock_asset.py \
  --geometry path/to/model.geo.json \
  --texture path/to/texture.png \
  --namespace mypack \
  --required-locator effect
```

Treat script success as static validation, not as proof of in-game or Marketplace acceptance.

## Integrate the add-on

Create only the files the asset needs:

- Resource pack: geometry, textures, client entity or block definitions, render controllers, animations, animation controllers, particles, sounds, localization, and manifest.
- Behavior pack: server entity or block definitions, components/component groups, events, spawn rules, loot tables, recipes, functions, and manifest.

Use one canonical asset identity and document any binding to a Marketplace-safe runtime namespace. Apply the runtime namespace consistently to geometry, animation, controller, render-controller, entity, and file identifiers. Follow cooperative add-on folder conventions under the creator-project directory; do not scatter loose textures, loot tables, or functions. Avoid vanilla overrides, `runtime_identifier`, experiments, and Java-edition dependencies. Put gameplay decisions in behavior-pack/server-authoritative files. Bound spawning, ticking, pathfinding, particles, animation complexity, and simultaneous entity counts for console hardware.

For block materials, use one render method within each
`minecraft:material_instances` group and its finish permutations. Bedrock BDS
rejects mixed opaque and transparent material instances even when Creator Tools
passes. When one face needs transparency, use one compatible pipeline for the
whole group; fully opaque pixels may remain visually solid. Verify the exact
frozen package in Stable and Preview BDS and inspect content logs for zero
component/material errors.

## Add animation and pathing

Read `references/animation-pathing.md` before adding entity motion.

Create original keyframes around the model's actual pivots. Do not copy another add-on's animation data. Reusing documented Bedrock component types and ordinary movement principles is acceptable; copying distinctive timing, poses, names, or data is not.

Keep visual motion in the resource pack:

- Define small idle, locomotion, look, and action clips in `animations/`.
- Select clips through a minimal animation controller.
- Drive locomotion from `query.modified_move_speed`.
- Blend transitions to avoid snapping.
- Animate only necessary bones and keep loop lengths short.

Keep navigation and gameplay in the behavior pack:

- Use supported `minecraft:movement`, `minecraft:movement.basic`, and navigation components.
- Add only the AI goals needed by the design.
- Use bounded search distances, slow base speeds, low-frequency random strolling, and explicit goal priorities.
- Omit natural spawn rules until crowd and hardware tests establish a safe density.
- Avoid scripts for basic locomotion and pathfinding.

Run the cross-file validator:

```bash
python3 scripts/validate_animated_entity.py \
  --geometry path/to/model.geo.json \
  --animations path/to/entity.animation.json \
  --controller path/to/entity.animation_controllers.json \
  --client-entity path/to/entity.entity.json \
  --behavior-entity path/to/entity.behavior.json
```

## Validate in gates

Complete each gate and report evidence:

1. **Static:** Parse all JSON; run both bundled validators; check identifiers, locators, and referenced files.
2. **Blockbench native round-trip:** Reopen and save the project, export through native codecs, compare element counts, and inspect exported locators. Use `NOT_APPLICABLE` with a reason when the approved asset uses no custom geometry. Run representative projects through an actual Blockbench open/save/reopen/native-export cycle, not only a JSON parser.
3. **Blockbench visual evidence:** Capture the fixed proof inventory in the
   Golden pipeline, including true silhouette, atlas-underlay UV, player-scale,
   locomotion-contact, and feature-action views. Capture the exact final model
   in a zero-warning native session and show real timeline clips and keyframes.
   Label every renderer honestly and hash every artifact. Use `NOT_APPLICABLE`
   rather than fabricating editor evidence for native full-cube blocks or flat
   icons.
4. **Creator Tools:** Validate the exact frozen `.mcaddon` with current `addon` and `currentplatform` checks. Record tool version, commands, exit codes, package SHA, and full logs.
5. **Stable BDS:** Boot the exact package, create a small bounded ticking area,
   summon and select the asset, execute bounded stress and cleanup functions,
   restart, and repeat. For an asset-only pack explicitly disable a
   script-runtime requirement rather than inventing a marker script. Treat
   these as adapter/boot/load evidence, not client rendering, combat, or
   controller proof.
6. **Bedrock desktop:** Import both packs, load a clean test world, and verify controller transitions, path selection, collision, water edges, damage reactions, logs, and animation speed under real movement.
7. **Persistence and multiplayer:** Save/reload, restart, join with another client, and verify server-authoritative behavior.
8. **Performance:** Stress the realistic maximum population/effects and inspect frame rate, memory, and tick behavior.
9. **Physical PS4:** Test Realm delivery, controller-only progression, split screen, multiplayer, save/reload, reconnect, and worst-case scenes on hardware.
10. **Marketplace submission:** Complete rights/provenance documentation and submit through an approved Marketplace partner account.

After any package-affecting change, rebuild deterministically and rerun Creator Tools and BDS. Promotion requires the frozen package SHA to equal the package SHA recorded by every qualification receipt. Normalize logs before hashing or regenerate their recorded hashes when formatting changes.

Run two material critique cycles before promotion. Require every art-direction
category to score at least 70/100, weighted overall at least 80/100, and
originality to pass separately. Return clean-room audit repairs to production
as opaque product findings; never disclose control-reference values.

Never state that an asset is PS4 compatible, PS4 verified, or Marketplace approved solely because static, Blockbench, Creator Tools, or BDS gates pass. Keep desktop, Realm, controller, split-screen, and physical-PS4 statuses explicit and pending until tested. State narrow claims and list every remaining gate.

Record independent statuses for static shape validation, Blockbench UI
roundtrip, native export, Bedrock rendering, and physical PS4 rendering.

## Deliverables

Provide:

- Editable `.bbmodel`.
- Exported `.geo.json` or native block geometry.
- Original PNG texture(s).
- Required resource-pack and behavior-pack files.
- A short asset brief and provenance record.
- Validation output and a readiness matrix listing passed, failed, and untested gates.
