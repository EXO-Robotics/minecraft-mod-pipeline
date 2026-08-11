# Whisperwood early placeholder audio

Status: **EARLY PLACEHOLDER STATIC BINDING ONLY**

This bounded pass gives the ten Whisperwood entities temporary ambient, hurt, and death mappings using existing vanilla sound events. It adds no audio bytes and no custom sound definition. `resource_pack/sounds.json` maps the standard entity events, while each matching behavior entity uses stable `minecraft:ambient_sound_interval` to emit `ambient` at a bounded interval.

Signature-action cues are deliberately withheld. The current exported action clips do not establish a verified semantic action timeline, and a client entity `sound_effects` alias alone is not a playback trigger. Adding aliases without a proven consumer would create declarative wiring with no demonstrated route.

## Authority checked

- Microsoft stable `minecraft:ambient_sound_interval` reference: <https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitycomponents/minecraftcomponent_ambient_sound_interval?view=minecraft-bedrock-stable>
- Microsoft stable actor resource definition (`description.sound_effects` exists): <https://learn.microsoft.com/en-us/minecraft/creator/reference/content/visualreference/actor_resource_definition.v1.8.0?view=minecraft-bedrock-stable>
- Official Mojang vanilla sample `resource_pack/sounds.json`: <https://raw.githubusercontent.com/Mojang/bedrock-samples/main/resource_pack/sounds.json>
- Exact local Stable target evidence: `program/aionbound-core-content-beta-qualification-runs/G000007-R1/control/request.json` (Stable 1.26.33.2, binary SHA-256 `978ea655c418f112a33b80043d676712ad080724382fafda9509825910fa4043`). That BDS evidence does not prove client resource-pack audio.

## Validate

Run:

```sh
python3 engineering/whisperwood-intake/audio-runtime/test_whisperwood_placeholder_audio.py
```

The validator checks exact scope, pack/map equality, ambient emitters, vanilla allowlisting, absence of custom audio bytes/definitions, signature-action withholding, schema constraints available without third-party libraries, and the unchanged final-exit blocker.

## Proof boundary

This is static JSON/reference closure only. It does not claim client playback, mix quality, signature timing, BDS/package admission, custom sound identity, controller, console, multiplayer, or release suitability. `W1-ASSET-AUDIO-001` remains open and blocks Wave 1 final exit.
