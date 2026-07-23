# Autonomous Blockbench Asset Authoring

`author_blockbench_asset` is a first-class generation operation. It accepts an
asset brief, versioned style profile, geometry/texture/rig/animation/bounds
contracts, rights state, deterministic seed, native Blockbench source, Bedrock
consumer exports, a machine visual-quality report, and repair history.

The operation fails closed when required inputs are absent, rights are not
releasable, geometry or coordinate semantics drift, required clips/states are
missing, native files cannot be reopened, visual evidence is incomplete, or
the repair loop exceeds five revisions. Accepted assets are copied into the
revisioned project registry with hashes and the explicit disposition
`MARKETPLACE_CANDIDATE_PS4_PENDING`.

## Versioned visual profile

`visual-style-profile-1.0.0` defines the original blocky shape language,
palette/material families, texture density, anatomy and pivot conventions,
animation timing, originality constraints, and console planning budgets.
The Bramblehorn fixture uses the regional-creature limits of 24 cubes, 10
bones, 3 locators, 6 clips, 5 controller states, one 64×64 texture, and a
20-pathfinding-entity stress target.

## Qualification loop

1. Validate the authored `.bbmodel`, texture, geometry, animations, controller,
   client entity, behavior entity, and bindings.
2. Open and save in Blockbench; export geometry and animations through native
   codecs.
3. Compare semantic left/right and front/rear coordinates rather than raw
   signs alone.
4. Capture front, rear, left, right, three-quarter, top, wireframe/rig, texture,
   and animation-timeline evidence.
5. Repair deterministically and record changed elements, cost delta, quality
   delta, previous hash, and new hash.
6. Package with fixed ZIP metadata; run Creator Tools and stable BDS.
7. Feed the measured static/runtime costs into the PS4 planning proxy.

No human step is required for this automated qualification path. Human/legal
rights decisions, Marketplace submission, client rendering, controller
behavior, Realm transfer, and physical console validation remain separate
gates and cannot be promoted by this operation.

## Bramblehorn evidence

The canonical fixture is `ccoriginal:creature.bramblehorn`; its
Marketplace-safe runtime binding is `ccoriginal_cc:bramblehorn`. The native
source and reports live under `prototypes/blockbench/bramblehorn/`.
`readiness-matrix.json` is the concise gate record; hash-bound Creator Tools and
BDS receipts live under `qualification/`.
