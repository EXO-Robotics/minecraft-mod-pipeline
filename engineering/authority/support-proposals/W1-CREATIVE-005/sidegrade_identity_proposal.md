# W1-CREATIVE-005 — Sidegrade Identity Proposal

Status: **PROPOSED_NOT_RATIFIED**  
Authority effect: **NONE UNTIL RATIFIED**

The conservative implementation is declarative, not hidden item state:

- seven small material finishes retain the base item ID and are progression/Codex facts, not inventory variants;
- the four explicitly named cross-region sidegrades receive sibling IDs;
- the four named unique finishes receive sibling IDs;
- Warden’s Pair and Dual Idol remain relationships between existing items;
- inert and ignited Trophy Edge retain their already distinct canonical IDs.

This ticket is deferrable. It does not block base Packet 006 item implementation or the Whisperwood checkpoint. It becomes blocking only before a named cross-region sidegrade or unique finish is registered; until then Engineering uses the approved base item IDs only.

Sibling items reuse approved base meshes. They need their own language, icon, recipe, repair, and Codex closure, but avoid fragile per-stack NBT/dynamic-property migrations and ambiguous inventory presentation. No additional sibling ID is authorized by this proposal.

Approval is required for the seven same-ID finishes, both four-item sibling sets, the two relationship-only pairings, and Trophy Edge staging.
