# Ashen Creative support tranche

This directory contains three bounded, authority-neutral proposals:

- `W1-001-AH`: selects only already-written Ashen dispositions from `W1-CREATIVE-001`, including the existing `aionbound:drake_scale` row verbatim and no additional identity. Selection is identity-only; it grants no upgrade or sidegrade authority while `W1-CREATIVE-005` remains deferred.
- `W1-004-AH`: applies the already-written global loot/chest/reward-guard envelopes to Ashen and makes the pre-existing Packet 006 `aionbound:ash_drake_horn` the sole critical seal; the pre-existing Packet 006 `aionbound:ember_forge_core` is optional mastery/forge reward only and uses the inherited E elite range when rolled by Kiln Sky.
- `W1-003-KILN-SKY`: proposes a minimal state/timing/ownership envelope for the four approved Kiln Sky phases and six approved Ash Drake attacks, including immutable pull scaling, a separate bounded reward set, exact terminal/reset semantics, no-queue add caps, and ecology-form isolation.

Every file remains `PROPOSED_NOT_RATIFIED`. Nothing here changes the decision ledger or authorizes BP/RP implementation. The JSON files are canonical. The builder reproduces all JSON/Markdown bytes deterministically; the tests also prove exact-subset inheritance, Packet 006 identity provenance, reward/persistence invariants, and explicit non-decisions.

Independent red-team findings accepted after local source verification are represented in the generated semantics above. Two proposed findings were rejected as false positives: `aionbound:drake_scale` is already an exact row in `W1-CREATIVE-001`; `aionbound:ash_drake_horn` and `aionbound:ember_forge_core` are existing Packet 006 identities, not new W1-001 identities.

Run:

```sh
python3 engineering/authority/support-proposals/ashen/test_ashen_support_proposals.py
python3 tools/validate_wave1.py
```
