# W1-CREATIVE-001 — Non-Warehouse Identity Proposal

Status: **PROPOSED_NOT_RATIFIED**  
Authority effect: **NONE UNTIL RATIFIED**

## Proposed answer

Use the warehouse first. Preserve evocative creature-part names in loot presentation and Codex prose, but map them to an existing regional material unless a distinct item is necessary to close an approved recipe or trophy craft.

This produces only nine new inventory identities: `mosskip_crown_fragment`, `thorn_barb`, `stalker_claw`, `hollow_venom_sac`, `drake_scale`, `prism_wing`, `watcher_lens`, `wight_shroud`, and `wing_bone_stay`, all in the `aionbound` namespace. Each has one explicit craft home and requires one shipping icon after ratification.

The smallest immediate tranche is `W1-001-WW`: approve the first four IDs plus the Whisperwood-only alias, narrative, and removal rows. The other five new IDs and later-region rows can remain unratified until their corresponding vertical slice. This keeps the Whisperwood checkpoint from waiting on Skyreach or finale inventory policy.

Everything else is classified in the JSON sibling as one of:

- alias to an existing warehouse resource;
- narrative/Codex state with no inventory object;
- context-only quantity/container wording;
- an already approved derived component.

Critical implementation consequences:

- `Concord Spark` is encounter state, not an item.
- regional keys are durable structure/Codex flags, not consumable key fragments.
- generic mastery-sigil language resolves to the existing `warden_sigil` or a Codex stamp.
- `Memory of Four Lands` retains its already proposed canonical ID, but its shipping presentation remains part of ticket 002.

## Exact approval surface

1. Approve or reject the four-ID Whisperwood tranche now.
2. Approve or defer the five later-region IDs.
3. Approve or reject the applicable alias table rows.
4. Approve curiosities/keys as state rather than inventory.
5. Approve the context-only removals.
6. If IDs pass, authorize only the icons in the ratified tranche; no art work begins from this proposal alone.
