# Crystal Marsh Economy and Equipment

Status: `SOURCE_COMPLETE_TARGETED_STATIC_PASS`

This lane implements the exact `W1-001-CM` identity dispositions and the
`W1-004-CM` loot/chest bands for Crystal Marsh, plus the eleven direct Packet
006 equipment/display identities. `W1-CREATIVE-005` remains deferred and no
sidegrade representation is created.

The natural `marsh_wight` table is ecology-only and cannot contain
`aionbound:marsh_wight_mask` or write Pearl Depths state. The protected Pearl
Depths material and apex-cache tables likewise contain no mask. Durable seal
credit, entitlement, recovery, and physical fulfillment remain solely owned by
the separately authorized Pearl Depths service.

Native pass-2 geometry, animation, and UV bytes are bound exactly. Shipping
inventory presentation is a separate deterministic 32x32 transparent pixel-art
surface and is not reused as model UV. Static checks do not prove Bedrock
rendering, BDS, multiplayer, controller, console, or candidate readiness.

After the creature and plant definition commits are merged, run:

```sh
python3 engineering/crystal-marsh-intake/economy-equipment/bind_post_merge_loot.py
python3 engineering/crystal-marsh-intake/economy-equipment/bind_post_merge_loot.py --check
```

This only adds the exact twenty `minecraft:loot` pointers. It creates no shared
runtime handler, subscription, scheduler, persistence domain, or reward path.
