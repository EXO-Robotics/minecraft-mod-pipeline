# W1-CREATIVE-004 — Loot and Reward Envelope Proposal

Status: **PROPOSED_NOT_RATIFIED**  
Authority effect: **NONE UNTIL RATIFIED**

The JSON sibling supplies closed tuning intervals for all six Creative rarity roles, boss package roll counts, and four chest sizes. Engineering may tune only within ratified intervals and may not add loot identities.

The minimum immediate tranche is `W1-004-WW-CH1`: apply the full envelope and guard model only to Whisperwood creatures, Whisperwood structures, and Thorn Court. Later-region adoption can be approved when those vertical slices begin.

The critical-path seal is a durable per-player progression credit. The physical trophy is a display object backed by an entitlement and a recovery claim. This avoids pretending Bedrock item delivery has true exactly-once external-effect semantics across a crash: progression is idempotent, while the physical grant is at-most-once best effort with a bounded recovery route.

Only an active tagged arena session can generate a trophy entitlement. Natural Thorn Stalkers and command kills cannot. Repeat clears can award regional materials and open the arena chest, but not another chapter seal or trophy entitlement.

`briar_elk_trophy` and `mosskip_trophy` are proposed as optional mastery/Codex credits. Neither replaces `thorn_stalker_skull` in the chapter-seal or Pilgrim path. This resolves the conflict between “alternate/soft seal” shorthand and the boss document’s explicit statement that mini-apexes do not replace chapter seals.

Approval is required for the rarity intervals, chest bands, entitlement model, repeat-clear policy, and alternate-seal interpretation.
