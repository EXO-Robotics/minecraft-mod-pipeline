# Gate 0 Substrate Remediation

Status: `STATIC_REMEDIATION_PASS`

This successor-only repair addresses the three content-schema debt families captured by the immutable G7 Gate 0 result. G7 itself remains unchanged.

## Repairs

- Added `minecraft:geometry.full_block` to the 32 rejected block definitions that already declared `minecraft:material_instances`. This restores the geometry/material pair required by Stable while preserving the blocks' prior full-cube presentation and texture identity.
- Changed the 19 rejected feature-rule identifiers to `aionbound:<exact filename stem>`. Their `places_feature` targets and distribution rules are unchanged.
- Kept all 12 affected recipe identities and formulas unchanged. Targeted identifier closure confirms their diagnostics were downstream of the missing block registrations.

## Targeted evidence

- `python3 -m unittest tests/wave1_substrate_gate0_regression.py` — PASS, 4 tests.
- `python3 tools/validate_g7.py` — PASS with the inherited 49 blocks, 55 recipes, 24 entities, 56 items, 32 loot tables, 10 spawn rules, and 15 structures.
- `git diff --check` — PASS.

The regression suite checks JSON parsing, geometry/material pairing, exact feature-rule filename binding, feature-target closure, the exact 12-recipe affected set, and custom item/block reference closure.

## Proof boundary

No BDS run occurred in this lane. This report does not establish a Stable BDS pass, client rendering, gameplay, controller/console behavior, candidate publication, or release readiness. The integration owner must rebuild the successor package and run a candidate-scoped Stable BDS check before treating these defects as runtime-cleared.
