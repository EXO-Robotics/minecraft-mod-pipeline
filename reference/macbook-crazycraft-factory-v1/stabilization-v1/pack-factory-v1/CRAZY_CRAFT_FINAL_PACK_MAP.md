# Crazy Craft fixed Bedrock pack factory

The frozen ten-section map remains the source-accounting input. The production unit is now one coherent named Bedrock Add-On pack.

- Packs: **16**
- Existing/reference authorities: **6**
- New packs: **10**
- Frozen source artifacts: **52/52 exact-once**
- Run control: **PAUSED**

## Pack portfolio

| # | Pack | Namespace | Owner | State | Source responsibility |
|---:|---|---|---|---|---|
| 1 | Quietwork | `ccoriginal_cc` | `PACK-WORKER-01-QUIETWORK` | `FINAL_OR_REFERENCE` | The SecretRoomsMod |
| 2 | Catalyst Wilds | `exowild` | `PACK-WORKER-02-CATALYST` | `AWAITING_TEST` | Mutant Creatures |
| 3 | Shatterwild Foundry | `ccoriginal_sw` | `PACK-WORKER-03-SHATTERWILD` | `FINAL_OR_REFERENCE` | reference authority only |
| 4 | Trailbound Packs | `ccr_p07` | `PACK-WORKER-04-TRAILBOUND` | `AWAITING_TEST` | Adventure Backpack |
| 5 | Pocketbound Companions | `ccr_p08` | `PACK-WORKER-05-POCKETBOUND` | `AWAITING_TEST` | Inventory Pets |
| 6 | Wayfarer Settlements | `ccr_p01` | `PACK-WORKER-06-WAYFARER` | `AWAITING_TEST` | CustomNpcs |
| 7 | Reliquary Vaults | `ccr_p13` | `PACK-WORKER-07-RELIQUARY` | `PLANNED_PRODUCTION` | Jewelrycraft 2, Baubles, Iron Chest |
| 8 | Hearth & Hall | `ccr_p11` | `PACK-WORKER-08-HEARTH-HALL` | `PLANNED_PRODUCTION` | BiblioCraft, Carpenter's Blocks, Chisel 2, Decocraft, MrCrayfish's Furniture Mod, Statues |
| 9 | Hearthveil | `ccr_p06` | `PACK-WORKER-09-HEARTHVEIL` | `PLANNED_PRODUCTION` | Witchery, Equivalent Exchange 3 |
| 10 | Aspectweave | `ccr_p02` | `PACK-WORKER-10-ASPECTWEAVE` | `PLANNED_PRODUCTION` | Morph, Armourer's Workshop, Hats, HatStand-4.0.0, iChunUtil, AnimationAPI |
| 11 | Vanguard Arsenal | `ccr_p04` | `PACK-WORKER-11-VANGUARD` | `PLANNED_PRODUCTION` | Superheroes Mod, Mine & Blade Battlegear 2 - Bullseye, GravityGun |
| 12 | Aperture Foundry | `ccr_p16` | `PACK-WORKER-12-APERTURE` | `PLANNED_PRODUCTION` | Transformers Mod, PortalGun-4.0.0-beta-4, Tardis Mod |
| 13 | Echo Vessels | `ccr_p10` | `PACK-WORKER-13-ECHO` | `PLANNED_PRODUCTION` | Soul Shards- The Old Ways, Weeping Angels, Origin |
| 14 | Bounded Outcome Events | `ccr_p03` | `PACK-WORKER-14-OUTCOMES` | `PLANNED_PRODUCTION` | Pandora's Box, LuckyBlocks |
| 15 | Momentum Menagerie | `ccr_p17` | `PACK-WORKER-15-MOMENTUM` | `PLANNED_PRODUCTION` | Killer Pacman, TrailMix, FoodPlus |
| 16 | Latchline Infrastructure | `ccr_p14` | `PACK-WORKER-16-LATCHLINE` | `PLANNED_PRODUCTION` | Railcraft, SecurityCraft, Malisis' Doors, Malisis' Core |

## Factory flow

```text
durable pack owner
→ implementation and original assets
→ immutable candidate submission
→ tester intake
→ mechanical/static/private/BDS/media consolidation
→ one PASS or consolidated repair result
→ same owner replacement generation
→ standalone acceptance
→ incremental shared-runtime integration
→ combined qualification
→ PACK_ACCEPTED_AND_INTEGRATED
```

No product worker is launched by this organization commit.
