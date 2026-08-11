# Whisperwood Plant Runtime Static Report

Status: `PASS_STATIC_REFERENCE_CLOSURE`

Ten Packet 001 plants are bound as non-colliding, selectable, placeable, breakable custom blocks using the exact native-evidence geometry and texture bytes. Shipping geometry identifiers are normalized to `geometry.aionbound.*`; shape payloads are unchanged.

| Plant | Runtime ID | Placement face | Skeletal playback |
| --- | --- | --- | --- |
| `briar_vine` | `aionbound:briar_vine` | `side` | `NOT_REQUIRED` |
| `ember_thistle` | `aionbound:ember_thistle` | `up` | `NOT_REQUIRED` |
| `glow_moss` | `aionbound:glow_moss` | `up` | `NOT_REQUIRED` |
| `hollow_lily` | `aionbound:hollow_lily` | `up` | `NOT_REQUIRED` |
| `lantern_bloom` | `aionbound:lantern_bloom` | `up` | `WITHHELD_UNSUPPORTED_CUSTOM_BLOCK_SKELETAL_PLAYBACK` |
| `mooncap_mushroom` | `aionbound:mooncap_mushroom` | `up` | `NOT_REQUIRED` |
| `pale_reed` | `aionbound:pale_reed` | `up` | `WITHHELD_UNSUPPORTED_CUSTOM_BLOCK_SKELETAL_PLAYBACK` |
| `root_flower` | `aionbound:root_flower` | `up` | `NOT_REQUIRED` |
| `star_grass` | `aionbound:star_grass` | `up` | `WITHHELD_UNSUPPORTED_CUSTOM_BLOCK_SKELETAL_PLAYBACK` |
| `whisper_fern` | `aionbound:whisper_fern` | `up` | `WITHHELD_UNSUPPORTED_CUSTOM_BLOCK_SKELETAL_PLAYBACK` |

## Animation decision

The four approved Blockbench-authored clips remain in immutable native evidence. They are not copied into the RP because Stable custom-block geometry has no clean entity-style skeletal animation-controller binding. No entity surrogate or Script API behavior was introduced.

## Proof boundary

Proven here: JSON parsing, namespace/identifier/reference closure, native-evidence geometry equivalence, exact source texture-byte equality, full PNG decode, role-grounded static placement/selection definitions, and absence of invented loot or animation bindings.

Not proven here: Creator Tools, Stable BDS, Bedrock client rendering, live placement/harvest behavior, animation playback, world generation, physical console behavior, or Marketplace acceptance.
