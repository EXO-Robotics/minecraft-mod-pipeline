# Ashen Creative support tranche

This directory contains three bounded, authority-neutral proposals:

- `W1-001-AH`: selects only already-written Ashen dispositions from `W1-CREATIVE-001`, including the existing `aionbound:drake_scale` row and no additional identity.
- `W1-004-AH`: applies the already-written global loot/chest/reward-guard envelopes to Ashen and makes `aionbound:ash_drake_horn` the sole critical seal; `aionbound:ember_forge_core` is optional mastery/forge reward only.
- `W1-003-KILN-SKY`: proposes a minimal state/timing/ownership envelope for the four approved Kiln Sky phases and six approved Ash Drake attacks.

Every file remains `PROPOSED_NOT_RATIFIED`. Nothing here changes the decision ledger or authorizes BP/RP implementation. The JSON files are canonical. The builder reproduces all JSON/Markdown bytes deterministically; the tests also prove exact-subset inheritance and explicit non-decisions.

Run:

```sh
python3 engineering/authority/support-proposals/ashen/test_ashen_support_proposals.py
python3 tools/validate_wave1.py
```
