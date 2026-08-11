# Ashen remaining landmark visual-native gate

Scope is exactly `fire_totem`, `burned_camp`, `char_wagon`, `broken_bridge`,
`basalt_arch`, `ash_watchtower`, `lava_shrine`, and `ash_cave` from frozen
Packet 002. The already-passing `ember_forge` and `ancient_kiln`
representatives are excluded.

The gate stages copies, preserves packet model/UV and texture bytes, creates
the brief-required true `effect` locator from the canonical packet export, and
runs two Blockbench 5.1.6 save/close/reopen/native-export cycles over an
isolated loopback-only CDP session. It authors every and only brief-declared
clip: `lava_shrine.glow`; the other seven briefs have exact empty clip sets.

This is editable/native landmark visual evidence only. It does not author or
prove `.mcstructure` assembly, world-generation placement, BP/RP runtime
binding, gameplay, BDS, Bedrock client, multiplayer, console, Marketplace, or
release behavior.
