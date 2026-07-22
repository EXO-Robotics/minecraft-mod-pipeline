# Reconstruction pattern library

Patterns convert reviewed Behavior IR shapes into candidate Bedrock strategies. They never match only on source text or class names.

Required families include items, weapons, tools, armor, projectiles, explosives, effects, cooldowns, abilities, machines, entities, bosses, structures, spawning, transformations, vehicles, inventory, forms, progression, and world mechanics.

Initial patterns cover projectile/explosive/lightning weapons, area mining, teleportation, summoning, passive and active armor, cooldowns, random rewards, processing and energy-like machines, crops, companions, mounts, multiphase bosses, transformations, key-binding and GUI replacements, dimension approximations, and portal/structure transitions.

Each pattern declares:

- Required and forbidden IR shape.
- Candidate target profiles and required catalog symbols.
- Data-driven, scripted, redesign, and rejection options.
- Controller interaction and feedback.
- State ownership, persistence, and migration.
- Multiplayer and performance implications.
- Expected quality dimensions and known losses.
- Positive, near-miss, adverse, and runtime tests.
- Example output and provenance.

A pattern match proposes a strategy; it does not prove parity. Near-miss fixtures are mandatory to guard against overmatching.

