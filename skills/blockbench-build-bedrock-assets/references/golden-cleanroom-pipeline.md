# Golden clean-room visual pipeline

Use this standard for custom geometry, rigged entities, animated props,
wearables, equipment, bosses, and any other asset whose visual quality or
originality is a material product requirement.

## Visual firewall

Transform visual evidence through three layers:

`source observation -> abstract visual requirement -> original product direction`

Production may receive gameplay role, locomotion class, approximate scale
range, semantic articulation, gameplay states, collision and locator needs,
readability targets, performance limits, and an original art direction.

Production must not receive source meshes, geometry JSON, UVs, pixels, exact
proportions, distinctive markings, bone names, filenames, keyframes, curves,
palette recipes, or highly distinctive descriptions. A prior asset may be a
construction-quality benchmark but never a reusable shape, rig, palette, or
motion identity.

## Typed visual contract

Choose a class profile rather than reusing one creature profile universally.
Supported profiles should include ambient ground creature, flying creature,
elite, boss, equipment, wearable, block device, and structure prop.

Freeze these typed sections before production:

- Scale and bounds: body ranges, ground plane, collision, selection, visible
  and animated bounds, reach origins, locators, and allowed animated expansion.
- Silhouette: mass ratios, head/body relation, limb ranges, required negative
  space, distance readability, prohibited resemblance cues, and cube repetition.
- Rig: semantic bone roles, hierarchy, pivots, articulated regions, locators,
  and bone/cube limits.
- Animation: per-clip duration range, loop and root-motion policy, participating
  roles, contacts, events, transitions, seam tolerance, bounds, penetration,
  foot slide, first-frame pop, and negative cases.
- Texture/material: atlas size, material regions, palette limits, contrast,
  texel density, overlap, repetition, thin-feature pixels, and state variants.
- Performance: geometry, texture, clip, controller, particle, spawn-density,
  and visible-distance budgets.

Use ranges unless an exact value is product-essential. Keep control references
and private originality comparisons out of the production packet.

## Native Blockbench integrity

The editable `.bbmodel` is a first-class source artifact:

- Use RFC 4122-shaped UUIDs for elements, groups, animations, animators, and
  keyframes.
- Resolve every outliner, element, animator, and keyframe link.
- Embed or bind the declared texture and require every textured cube face to
  reference the intended texture index.
- Reopen, save, reopen, and export through native Blockbench codecs.
- Require zero warnings and exact final model identity in the captured session.
- Capture the animation timeline with every required clip and visible keyframes.
- Hash screenshots and bind their hashes to the round-trip receipt.

Keep native UI captures outside deterministic generated-output equality because
their pixels include editor and OS state. Record that exclusion explicitly;
the modeled source and native runtime exports remain deterministic inputs.

## Fixed proof standard

Freeze camera, projection, lighting, background, resolution, pose, filename,
and source type for every proof view. Require at least:

- front, left, rear, three-quarter front, three-quarter rear, and top;
- player-height near and medium;
- neutral pose, locomotion contacts, and feature-action key poses;
- texture atlas, atlas-underlay UV sheet, and true silhouette-only sheet.

Use honest `source_type` values. A deterministic geometry renderer is not a
Blockbench render. A silhouette proof must contain only the silhouette and
standard reference markers, not shaded material output.

The deterministic proof renderer must consume runtime geometry pivots,
rotations, animation poses, and atlas-informed face material sampling. Do not
approximate poses from cube origins or fill each bone with one arbitrary color.
Include player scale markers where scale is reviewed.

## Automated heuristics

Compute metrics from artifacts, not declarations:

- silhouette occupancy and required negative space;
- intended symmetry and limb separation;
- face/material contrast and palette count;
- flat-plane and cube-uniformity warnings;
- UV bounds, texel-density variance, repetition, and thin-feature pixels;
- animated-bounds overflow, ground contact, foot slide, and clipping;
- first-frame pop, loop seam, missing transition, and state differentiation.

Use the contract's exact field names in validators and reports. A renamed or
missing metric must fail validation rather than silently defaulting to zero.
Heuristics may reject obvious weakness but cannot certify Marketplace-level art.

## Two critique cycles

Cycle 1 reviews construction, hierarchy, pivots, locators, UVs, animation,
proof integrity, and BP/RP binding.

Cycle 2 reviews silhouette, material language, distance readability,
presentation originality, and state communication.

Use this weighted art-direction rubric:

| Category | Weight |
|---|---:|
| Silhouette and proportion | 25% |
| Animation and motion quality | 20% |
| Material and texture language | 20% |
| Gameplay readability | 15% |
| Technical construction | 10% |
| Originality | 10% |

Require every category to score at least 70 and the weighted score to be at
least 80. Technical validity cannot compensate for weak art. Originality also
passes independently.

## Originality audit and repair

After freeze, compare exact identifiers, byte-identical files, geometry
signatures, animation timing patterns, palette/marking structure, silhouette,
and presentation sequencing against authorized control material. Exact clip
duration collisions can be meaningful even when names and geometry differ.

Return only an opaque finding ID, the product-facing defect, allowed outcome,
and invalidated gates to production. Do not reveal control values or reference
details. Production chooses a fresh value within the public contract range.

Any package-affecting repair creates a new production commit and package hash.
Rebuild twice, re-run Creator Tools, re-run Stable and Preview BDS, and
re-audit affected originality and lineage gates.

## Cooperative packaging and BDS

Use one immediate creator-project texture root. Put a feature's entity and item
textures below the same game/asset directory, for example:

`textures/<creator_project>/<asset>/entity/`

`textures/<creator_project>/<asset>/items/`

Update every client binding when paths move. Loose `textures/items`, a
namespace-only items directory, or multiple immediate creator roots may fail
current cooperative Creator Tools profiles even when the files resolve locally.

For deterministic archives use stable entry ordering, permissions, and a fixed
ZIP timestamp such as 1980-01-01. Qualify the exact frozen package hash.

Asset-only packs must declare `require_script_runtime: false` in harnesses that
support it. Still require clean boot, pack/entity resolution, bounded summon or
fixture probes, stress, cleanup, and restart. Never add a fake script merely to
satisfy a harness.

BDS does not prove rendering, animation playback, controller behavior, desktop
client behavior, Realm transfer, split screen, or physical PS4 performance.
