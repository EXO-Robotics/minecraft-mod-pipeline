# Whisperwood Sapling Regrowth

Status: **STATIC_ASSEMBLY_AND_INTERFACE_READY**

The ratified W1-006 tree is one `7x9x7` upright asymmetric assembly with a six-block trunk and exactly the approved four-block palette. The sapling now has a stable declarative supported-soil filter.

Current stable Bedrock does not offer a declarative-only custom sapling growth action. `minecraft:tick` dispatches `onTick` to a registered custom block component, while the older event-bearing ticking components are deprecated. To avoid a missing-component content error, this lane does not attach the component before the owning runtime lane registers it. `WHISPERWOOD_SAPLING_REGROWTH_REPORT.json` binds the exact integration interface.

The committed `.mcstructure` is deterministic little-endian NBT. Blockbench is `NOT_APPLICABLE` because this assembly introduces no custom geometry, texture, UV, rig, or animation. Runtime growth, bone meal, loaded-time timing, restart behavior, and Bedrock/client rendering remain unproven until the interface is wired and Checkpoint 1 runs.
