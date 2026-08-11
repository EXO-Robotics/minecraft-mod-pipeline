# W1-CREATIVE-006 — Whisperwood Structure Assemblies

Status: `OPEN_SUPPORT_REQUIRED`

The Packet 001 structure models are visual prop inputs. They are not authored
Bedrock encounter assemblies and cannot be counted as `.mcstructure` content.
Engineering found no approved assembly bytes for these eight required targets:

- `hunter_camp`
- `broken_wagon`
- `root_bridge`
- `owl_shrine`
- `forest_waystone`
- `hollow_cave_entrance`
- `ancient_totem`
- `fallen_giant_tree`

Creative/Asset support must provide either:

1. exact approved `.mcstructure` bytes for each target; or
2. an assembly envelope for each target that explicitly authorizes Engineering
   to construct it, binding maximum footprint and height, approved block/prop
   palette, required landmark silhouette, required functional/loot anchor
   positions, terrain attachment rule, and any encounter trigger location.

Existing purpose, visit reason, rarity language, and story identity remain
binding. Loot percentages, blocked non-warehouse identities, boss behavior,
and world-generation frequency are outside this ticket.

Until resolved, Engineering may implement and validate the reusable G7
registration, placement, NBT, persistence, and claim-guard framework, but may
not substitute generic G7 layouts or treat individual `.bbmodel` props as full
structure proof. This blocks the Whisperwood vertical exit and Checkpoint 1
structure-registration claim.

Evidence authority:
`engineering/whisperwood-intake/structure-runtime/WHISPERWOOD_STRUCTURE_RUNTIME_MAP.json`.
