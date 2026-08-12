# Skyreach remaining landmark visual-native gate

Scope is exactly `ancient_sky_arch`, `broken_sky_path`, `cliff_beacon`,
`cliff_outpost`, `floating_ruin_floor`, `hanging_lift_frame`, `nest_platform`,
and `rope_bridge` from frozen Packet 004. The already-passing `wind_shrine`
and `observation_tower` representatives are excluded.

The gate stages copies, preserves packet model/UV and texture bytes, creates
the brief-required true `effect` locator from the canonical packet export, and
runs two Blockbench 5.1.6 save/close/reopen/native-export cycles over an
isolated loopback-only CDP session. It authors every and only brief-declared
clip: `cliff_beacon.flame_idle`; the other seven briefs have exact empty clip
sets.

This is editable/native landmark visual evidence only. It does not author or
prove `.mcstructure` assembly, world-generation placement, BP/RP runtime
binding, gameplay, BDS, Bedrock client, multiplayer, console, Marketplace, or
release behavior.
