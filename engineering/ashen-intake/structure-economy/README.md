# Ashen structure economy lane

This lane binds seven ordinary Ashen barrels to distinct ratified chest tables,
keeps the Ember Forge arena cache empty before valid clear, and provides a
command-free inventory-first reward bridge for future Kiln Sky composition.

The bridge does not decide whether a boss clear is valid. Its protected cache
population method requires an explicit `validClear: true` input owned by the
Kiln Sky service. Neither `aionbound:ash_drake_horn` nor
`aionbound:ember_forge_core` appears in a static structure table.

Activation signatures and stamps are deterministically derived from the exact
block-built assembly coordinates. Visual models are not inputs. This lane makes
no BDS, build, client, boss-terminal, or candidate claim.

Run `python3 engineering/ashen-intake/structure-economy/validate_ashen_structure_economy.py`
to refresh the evidence-derived report, then rerun it with `--check` to prove
deterministic report equality.
