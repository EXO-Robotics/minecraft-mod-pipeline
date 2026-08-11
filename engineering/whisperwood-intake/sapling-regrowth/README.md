# Whisperwood Sapling Regrowth

Status: **SOURCE_RUNTIME_WIRED**

The ratified W1-006 tree is one `7x9x7` upright asymmetric assembly with a six-block trunk and exactly the approved four-block palette. The sapling has a stable supported-soil filter, the approved loaded-time tick interval, and the registered `aionbound:whisperwood_sapling_regrowth` component.

Current stable Bedrock dispatches `minecraft:tick` through a registered custom block component. `scripts/main.js` registers this component during `system.beforeEvents.startup`; `scripts/whisperwood_regrowth.js` performs full-footprint obstruction checks before atomic structure placement and applies the bounded one-in-three bone-meal attempt.

The committed `.mcstructure` is deterministic little-endian NBT. Blockbench is `NOT_APPLICABLE` because this assembly introduces no custom geometry, texture, UV, rig, or animation. Source semantic tests do not prove loaded-time delivery, client interaction, BDS restart behavior, or rendering; those remain within Checkpoint 1 and later client proof boundaries.
