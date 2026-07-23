# Bramblehorn animated add-on fixture

Canonical asset: `ccoriginal:creature.bramblehorn`.

Marketplace-safe runtime binding: `ccoriginal_cc:bramblehorn`.

The fixture contains one original 64×64 texture, an 8-bone/18-cube native
Blockbench source, three gameplay locators, six animation clips, a five-state
lifecycle controller, bounded hostile pathfinding, loot, forest/night spawn
rules, localization, deterministic packaging, and machine-readable provenance.

## Automated qualification

- Native Blockbench reopen, save, geometry export, and animation export: passed.
- Static geometry and animated-entity validators: passed.
- Creator Tools 0.17.6 `addon` and `currentplatform`: passed, zero errors/warnings.
- Stable BDS 1.26.33.2: summon, entity selector, 20-entity stress, cleanup, and
  clean restart rerun passed.
- PS4 planning proxy: three estimated units included inside the existing
  creatures/elite allocation; client rendering and memory remain unmeasured.

Run:

```sh
python3 tools/build_bramblehorn_asset.py
python3 tools/run_bramblehorn_creator_tools.py /path/to/mct
python3 tools/run_bramblehorn_bds.py
```

The package and BDS world are under `addon/` and `qualification/`.

## Remaining physical gates

Bedrock desktop rendering/controller behavior, real multiplayer,
Realm transfer, split-screen, persistence with players, and physical PS4
performance are still pending. This artifact is not described as
PS4-compatible, PS4-certified, or Marketplace-approved.
