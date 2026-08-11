# Ashen remaining plant native gate

Scope is exactly `cinder_grass`, `ash_fern`, `char_shrub`, `soot_mushroom`,
`magma_moss`, `glow_root`, `basalt_flower`, and `ember_vine` from frozen Packet
002. The already-passing `fire_bloom` and `smoke_reed` representatives are
excluded.

The gate stages copies, preserves packet model/UV and texture bytes, creates
the brief-required true `effect` locator from the canonical packet export, and
runs two Blockbench 5.1.6 save/close/reopen/native-export cycles over an
isolated loopback-only CDP session. These briefs declare no animation clips, so
the exact native clip set is empty and no discretionary motion is authored.

This is native source and codec evidence only. It does not edit or qualify the
BP, RP, gameplay, BDS, Bedrock client, multiplayer, console, Marketplace, or
release lanes.
