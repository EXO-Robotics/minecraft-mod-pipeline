# Whisperwood Codex implementation map

Status: **evidence-bound data map only**. This does not edit BP/RP content, implement UI, or claim runtime proof.

## Integration decision

Preserve G7's migration pattern and existing gameplay stamps, but add a minimal v4 Codex discovery field using registry-versioned compact two-bit states (locked/partial/complete). G7 caps the raw stamp array at 128 and player JSON at 8192 bytes, while four regions already imply 160 pages before structures, equipment, and bosses. The exact IDs below are canonical discovery event keys translated into compact state, not an indefinitely growing stamp array. The existing chat-driven Codex is a schema predecessor, not the target UX; Wave 1 should render a book/form surface and reserve chat for bounded diagnostics.

Creative's frozen category vocabulary has no `block` category. The map therefore retains `entry_kind=block` while using `codex_category=resource`, avoiding a lore/schema invention.

## Entry matrix

| Kind | ID | Importance | Unlock stamp(s) | Readiness | Blockers |
|---|---|---|---|---|---|
| resource | `whisper_bark` | craft_core | `codex:ww:resource:whisper_bark:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>world_distribution:WORLDGEN_RUNTIME |
| resource | `moss_resin` | craft_core | `codex:ww:resource:moss_resin:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>equipment_closure:PACKET-006 |
| resource | `glow_spore` | craft_core | `codex:ww:resource:glow_spore:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>equipment_closure:PACKET-006 |
| resource | `hollow_amber` | craft_core | `codex:ww:resource:hollow_amber:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>component_presentation:W1-CREATIVE-001 |
| resource | `lantern_fur` | craft_core | `codex:ww:resource:lantern_fur:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>equipment_closure:PACKET-006 |
| resource | `moon_sap` | critical_path | `codex:ww:resource:moon_sap:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>equipment_closure:PACKET-006 |
| resource | `root_heart` | critical_path | `codex:ww:resource:root_heart:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>component_presentation:W1-CREATIVE-001 |
| resource | `briar_antler` | craft_core | `codex:ww:resource:briar_antler:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>equipment_closure:PACKET-006 |
| resource | `widow_silk` | craft_core | `codex:ww:resource:widow_silk:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>component_presentation:W1-CREATIVE-001 |
| resource | `ancient_acorn` | exploration | `codex:ww:resource:ancient_acorn:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>twinbond_presentation:W1-CREATIVE-002 |
| block | `whisperwood_log` | craft_core | `codex:ww:block:whisperwood_log:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | world_distribution:WORLDGEN_RUNTIME |
| block | `stripped_whisperwood_log` | craft_core | `codex:ww:block:stripped_whisperwood_log:crafted` | SAFE_NOW | none |
| block | `whisperwood_wood` | exploration | `codex:ww:block:whisperwood_wood:crafted` | SAFE_NOW | none |
| block | `whisperwood_planks` | craft_core | `codex:ww:block:whisperwood_planks:crafted` | SAFE_NOW | none |
| block | `whisperwood_leaves` | exploration | `codex:ww:block:whisperwood_leaves:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | world_distribution:WORLDGEN_RUNTIME |
| block | `whisperwood_sapling` | craft_core | `codex:ww:block:whisperwood_sapling:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | world_distribution:WORLDGEN_RUNTIME |
| block | `whisperwood_roots` | exploration | `codex:ww:block:whisperwood_roots:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | world_distribution:WORLDGEN_RUNTIME |
| block | `moss_bark` | craft_core | `codex:ww:block:moss_bark:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | world_distribution:WORLDGEN_RUNTIME |
| block | `hollow_wood` | exploration | `codex:ww:block:hollow_wood:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | world_distribution:WORLDGEN_RUNTIME |
| block | `forest_brick` | exploration | `codex:ww:block:forest_brick:crafted` | BLOCKED_BY_LISTED_DEPENDENCIES | structure_runtime:STRUCTURE_BYTES_NOT_PRESENT |
| plant | `star_grass` | craft_core | `codex:ww:plant:star_grass:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | world_distribution:WORLDGEN_RUNTIME |
| plant | `whisper_fern` | craft_core | `codex:ww:plant:whisper_fern:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | world_distribution:WORLDGEN_RUNTIME |
| plant | `pale_reed` | critical_path | `codex:ww:plant:pale_reed:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | equipment_closure:PACKET-006 |
| plant | `glow_moss` | craft_core | `codex:ww:plant:glow_moss:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | equipment_closure:PACKET-006 |
| plant | `mooncap_mushroom` | exploration | `codex:ww:plant:mooncap_mushroom:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_tuning:W1-CREATIVE-004 |
| plant | `lantern_bloom` | exploration | `codex:ww:plant:lantern_bloom:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | equipment_closure:PACKET-006 |
| plant | `hollow_lily` | critical_path | `codex:ww:plant:hollow_lily:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_tuning:W1-CREATIVE-004 |
| plant | `root_flower` | craft_core | `codex:ww:plant:root_flower:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | equipment_closure:PACKET-006 |
| plant | `briar_vine` | craft_core | `codex:ww:plant:briar_vine:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | component_presentation:W1-CREATIVE-001<br>equipment_closure:PACKET-006 |
| plant | `ember_thistle` | critical_path | `codex:ww:plant:ember_thistle:harvested` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_tuning:W1-CREATIVE-004<br>ashen_runtime:SLICE-B |
| creature | `mosskip_fawn` | exploration | `codex:ww:creature:mosskip_fawn:observed` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004 |
| creature | `mosskip_doe` | exploration | `codex:ww:creature:mosskip_doe:observed` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004 |
| creature | `mosskip_buck` | craft_core | `codex:ww:creature:mosskip_buck:observed` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>alternate_seal:W1-CREATIVE-004 |
| creature | `lantern_hare` | exploration | `codex:ww:creature:lantern_hare:observed` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004 |
| creature | `rootback_boar` | craft_core | `codex:ww:creature:rootback_boar:observed` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>ingredient_identity:W1-CREATIVE-001 |
| creature | `briar_elk` | craft_core | `codex:ww:creature:briar_elk:observed` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>alternate_seal:W1-CREATIVE-004 |
| creature | `rot_wolf` | exploration | `codex:ww:creature:rot_wolf:defeated` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>ingredient_identity:W1-CREATIVE-001 |
| creature | `thorn_stalker` | critical_path | `codex:ww:creature:thorn_stalker:defeated` | BLOCKED_BY_LISTED_DEPENDENCIES | boss_envelope:W1-CREATIVE-003<br>loot_probability:W1-CREATIVE-004<br>ingredient_identity:W1-CREATIVE-001 |
| creature | `hollow_widow_spider` | craft_core | `codex:ww:creature:hollow_widow_spider:defeated` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>ingredient_identity:W1-CREATIVE-001 |
| creature | `bark_wraith` | exploration | `codex:ww:creature:bark_wraith:defeated` | BLOCKED_BY_LISTED_DEPENDENCIES | loot_probability:W1-CREATIVE-004<br>structure_runtime:STRUCTURE_BYTES_NOT_PRESENT |

## Player-facing answer contract

Every JSON entry binds three concise fields: what the player found, what the material or creature connects to, and the next approved investigation. These are relationship summaries from Creative authority, not new lore. Creature prose remains owned by `CODEX_ENTRIES_CREATURES.md`.

## Proof boundary

This map proves deterministic coverage and schema compatibility only. It does not prove event delivery, loot probabilities, world distribution, equipment behavior, boss semantics, UI quality, BDS load, or client behavior.
