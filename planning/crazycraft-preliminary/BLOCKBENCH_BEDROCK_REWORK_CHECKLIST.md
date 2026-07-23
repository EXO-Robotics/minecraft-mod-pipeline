# Blockbench and Bedrock-native rework checklist

Status: preliminary original-replacement art and implementation plan.

This checklist preserves the high-level experience—odd equipment, regional
creatures, discovery, elites, bosses, powers, and controlled chaos—without
copying protected names, models, textures, sounds, structures, characters,
branding, lore, or other distinctive expression.

## 1. Establish the original visual system

- [x] Choose an original project name and asset namespace.
- [x] Define a visual theme that is not based on any one source mod.
- [x] Define a limited color palette and material families.
- [x] Define texture resolutions: 16x16 for ordinary blocks; larger only when
      justified for entities, bosses, armor, or animated props.
- [x] Define cube density, silhouette, bevel, and animation guidelines.
- [x] Define shared scale, origin, pivot, bone-naming, locator, and UV rules.
- [ ] Create reusable Blockbench templates for blocks, items, creatures,
      humanoids, bosses, and attachables.
- [x] Record author, source brief, creation date, and rights evidence for every
      original asset.

## 2. First vertical slice

Build this before starting the full catalog.

- [ ] Three original full-cube blocks with original textures.
- [ ] One original custom-geometry functional block.
- [ ] One original weapon with first-person and third-person presentation.
- [x] One original regional creature with idle, walk, attack, hurt, and death
      animations.
- [ ] One small original encounter structure made from the new block palette.
- [ ] One loot table, recipe path, spawn rule, and progression reward.
- [ ] Multiplayer and restart-persistence verification.
- [ ] Package and test the slice as a Bedrock add-on.

## 3. Blockbench asset backlog

### Blocks and functional props

- [ ] Original natural and regional block families.
- [ ] Original structure and decorative block families.
- [ ] Original crafting/progression stations.
- [ ] Original summon or encounter-trigger blocks.
- [ ] Animated block entities or props where static blocks are insufficient.
- [ ] Collision and selection bounds for every custom geometry.
- [ ] Placement-orientation previews for directional blocks.
- [ ] Destruction particles or particle texture references.

Prefer standard full-block geometry for ordinary cubes. Use custom Blockbench
geometry only when silhouette or function requires it.

### Weapons, tools, and unusual equipment

Current planning range: 15–20 original weapons.

- [ ] Inventory/icon presentation for each item.
- [ ] Held first-person and third-person presentation.
- [ ] Original 3D geometry only for silhouette-critical equipment.
- [ ] Hand, muzzle, projectile, effect, and attachment locators as required.
- [ ] Use, charge, swing, recoil, or transformation animations as required.
- [ ] Original projectile models and textures.
- [ ] Original cooldown and active-state visual language.

### Armor, wearables, and powers

Current planning range: 6–8 original armor sets and 3–5 power sets.

- [ ] Inventory icons and item textures.
- [ ] Player attachable geometry for nonstandard silhouettes.
- [ ] Male/default and slim-player fit checks where applicable.
- [ ] Helmet visibility and first-person obstruction checks.
- [ ] Equipped, powered, damaged, and cooldown states.
- [ ] Power locators for particles, projectiles, trails, and area effects.
- [ ] Multiplayer ownership and remote-player presentation checks.

### Regional creatures

Current planning range: 25–35 meaningful original creatures.

- [ ] Original role-level brief for each creature.
- [ ] Distinct silhouette, palette, proportions, and movement language.
- [ ] Bedrock bone hierarchy with stable pivots and meaningful names.
- [ ] Idle, locomotion, attack, hurt, death, and special-state animations.
- [ ] Head-look or targeting behavior where appropriate.
- [ ] Ground contact, eye, mouth, hand, projectile, effect, rider, and loot
      locators where required.
- [ ] Collision box, hitbox, visible bounds, shadow, and culling checks.
- [ ] Baby or variant geometry only when it adds player value.
- [ ] Spawn egg colors and inventory presentation.

Create shared rig families where appropriate, but avoid making the roster feel
like palette swaps.

### Elites

Current planning range: 8–12 original elites.

- [ ] Distinct readable silhouette at normal gameplay distance.
- [ ] Telegraph animations for every high-damage attack.
- [ ] Phase, enrage, shield, stagger, and defeat states as required.
- [ ] Effect locators and arena interaction anchors.
- [ ] Performance-safe particle and material plan.
- [ ] Reward-item presentation tied to the progression path.

### Major bosses

Current planning range: 6–8 original bosses.

- [ ] Model complexity budget per boss.
- [ ] Stable root, phase bones, attack locators, camera target, and arena
      anchors.
- [ ] Idle, locomotion, entrance, attacks, transitions, stagger, defeat, and
      despawn animations.
- [ ] Clear telegraphs readable with controller play and split attention.
- [ ] Phase-specific geometry or texture states where justified.
- [ ] Collision, hitbox, culling, shadow, and visible-bounds verification.
- [ ] Four-player entity, animation, particle, and script budget.

### Controlled-chaos outcomes and postgame mutators

Current planning range: 40–75 bounded outcomes.

- [ ] Reuse an approved modular visual kit rather than authoring 75 unrelated
      high-cost models.
- [ ] Create reusable effect anchors, warning markers, arena props, portals,
      hazards, and reward containers.
- [ ] Define low-, medium-, and high-spectacle presentation budgets.
- [ ] Provide visual warning and cleanup states for every spawned outcome.

### Deferred Blockbench-heavy systems

Do not enter full production until their Bedrock-native behavior prototypes
work.

- [ ] Player transformations or alternate forms.
- [ ] Vehicles and rideable machines.
- [ ] Inventory companions.
- [ ] Source-specific machines and energy-network props.
- [ ] Dimension-specific asset sets.

## 4. Assets that should not primarily be made in Blockbench

- [ ] Standard block textures: paint as pixel art.
- [ ] Inventory icons: paint or render, then finish as pixel art.
- [ ] Particles: create texture sheets and Bedrock particle JSON.
- [ ] Sounds and music: author in an audio tool and configure sound JSON.
- [ ] Structures: assemble from the original block palette in Minecraft or a
      structure-authoring workflow, then export Bedrock structure files.
- [ ] UI: design for Bedrock forms or supported UI surfaces.
- [ ] Recipes, loot, trades, spawning, localization, and manifests: author as
      Bedrock data files.

## 5. Java concepts that require Bedrock-native redesign

### Blocks

- [ ] Replace Java blockstate/model assumptions with Bedrock block traits,
      states, permutations, geometry, and material instances.
- [ ] Replace tile/block entities with supported block components and scripts.
- [ ] Define explicit geometry for every custom block.
- [ ] Rebuild placement, rotation, interaction, destruction, and ticking
      behavior using supported Bedrock components/events.

### Items and equipment

- [ ] Replace Java item classes and overrides with Bedrock item components.
- [ ] Replace keyboard-only actions with use, interact, sneak-use, charge, or
      supported controller-friendly inputs.
- [ ] Implement cooldowns, durability, projectiles, and active powers using
      supported components and server-authoritative scripts.
- [ ] Rebuild attachable and render-controller presentation.

### Entities

- [ ] Replace Java entity classes, goals, and renderers with Bedrock behavior
      components, component groups, events, animations, animation controllers,
      render controllers, and scripts.
- [ ] Replace renderer-only state with query/property-driven visual state.
- [ ] Bound spawn counts, pathfinding pressure, particles, and per-tick work.
- [ ] Make important combat and reward decisions server-authoritative.

### Animation and presentation

- [ ] Convert animation intent—not source keyframes—into original Bedrock
      animation JSON and Molang transitions.
- [ ] Rebuild material, texture, geometry, and animation selection through
      Bedrock render and animation controllers.
- [ ] Replace unsupported shaders and post-processing with materials,
      particles, fog, lighting, sounds, and bounded scripted effects.

### State, networking, and progression

- [ ] Replace Java NBT/capabilities with versioned dynamic properties or other
      supported persistent state.
- [ ] Replace custom Java network packets with server-authoritative Script API
      decisions and replicated Bedrock state.
- [ ] Add migration behavior for persistent player and world data.
- [ ] Verify multiplayer ownership, reconnects, deaths, dimension changes, and
      server restarts.

### Interfaces and unsupported systems

- [ ] Redesign custom GUIs as supported forms or world interactions.
- [ ] Redesign source-specific dimensions around currently supported Bedrock
      capabilities; defer when equivalence is not credible.
- [ ] Redesign energy networks as bounded scripted graphs only after a
      performance prototype passes.
- [ ] Replace Java coremods, mixins, reflection, and renderer hooks with
      explicit supported behavior or mark them unsupported.

## 6. Required files per asset class

### Custom block

- [ ] Behavior-pack block definition.
- [ ] Resource-pack geometry or explicit standard geometry.
- [ ] Material instances and terrain texture registration.
- [ ] Original texture files.
- [ ] Loot, recipe, localization, and sounds as applicable.
- [ ] Collision/selection components for custom shapes.

### Entity or boss

- [ ] Behavior entity definition.
- [ ] Client entity definition.
- [ ] Geometry.
- [ ] Textures.
- [ ] Animations and animation controllers.
- [ ] Render controllers and materials.
- [ ] Spawn rules, loot, localization, and sounds.
- [ ] Script integration and persistent-state declarations as applicable.

### Wearable or animated item

- [ ] Item definition.
- [ ] Inventory texture registration and icon.
- [ ] Attachable definition when required.
- [ ] Geometry, textures, animations, and render controller when required.
- [ ] Recipe, loot, localization, sounds, and script behavior.

## 7. Acceptance gates for every original asset

- [ ] Rights provenance is recorded and attributable.
- [ ] No protected source asset was traced, recolored, kitbashed, or used as
      the modeling base.
- [ ] The role-level brief explains what gameplay purpose is preserved.
- [ ] Geometry, textures, identifiers, and animations pass static validation.
- [ ] Pivots, UVs, normals, bounds, locators, and animation loops are checked.
- [ ] The asset is readable in first person, third person, and normal combat
      distance where applicable.
- [ ] Controller interaction is complete.
- [ ] Multiplayer behavior is verified.
- [ ] Restart persistence is verified when stateful.
- [ ] Physical-console performance is measured for high-cost assets.
- [ ] The final resource and behavior packs contain no placeholder or
      uncleared source files.

## 8. Recommended production order

1. Visual system and templates.
2. Vertical slice.
3. Odd arsenal and early-survival blocks/items.
4. One shared creature rig family and the first regional encounter.
5. Discovery structure kit.
6. Elite framework.
7. First major boss and armor/power reward.
8. Additional roster content using proven templates.
9. Controlled-chaos modular visual kit.
10. Postgame states and final optimization.
