# Java mod reconstruction baseline

This baseline converts selected Java-mod mechanics into original Minecraft
Bedrock Add-On systems. It does not build a standalone game, replace vanilla
survival, or authorize source expression for production.

## Boundary

The analysis record may contain opaque IDs for authorized Java evidence.
Concrete source paths, names, assets, code, decompiled material, and distinctive
expression remain analysis-only. The production baseline contains only abstract
roles, original product identities, clean-room contract references, expected
Bedrock outputs, and qualification statuses.

The default mode is `clean_room_originalization`. Authorized adaptation remains
available only when the material-level rights ledger proves the complete
commercial and Marketplace permission set.

## Reconstruction sequence

1. Register each source material and its permissions in the rights ledger.
2. Capture authorized observation evidence under `analysis/evidence/`; assign
   opaque lowercase evidence IDs.
3. Distill observed mechanics into Gameplay Intent IR. Keep observed, inferred,
   selected, redesigned, omitted, and unknown claims distinct.
4. Export a clean-room design contract.
5. Prepare the reconstruction wave with `prepare-reconstruction-wave`.
6. Author Behavior IR and asset contracts. Use original identities and
   Marketplace-safe Bedrock forms.
7. Produce Blockbench and BP/RP/script artifacts from production contracts only.
8. Package deterministically, then qualify Creator Tools, stable BDS,
   multiplayer, persistence, cleanup, desktop controls/rendering, the PS4
   planning proxy, and physical PS4 separately.

Advancing a feature beyond `PENDING_AUTHORIZED_EVIDENCE` requires at least one
opaque authorized-evidence ID. Passing `physical_ps4` requires the feature state
`PS4_VERIFIED`.

## Wave 1 baseline

`Java Mod Reconstruction Wave 1 - Forest Systems` binds:

- Bramblehorn as the existing server-qualified template.
- Mossback Forager as the second regional creature.
- Resonance Sling as the ranged-item and projectile pattern.
- Signal Ruin as the compact structure pattern.
- Thornwarden Elite as the elite encounter pattern.
- Forest Attunement as the additive persistent unlock.
- Sporefall Event as the bounded chaos-event pattern.

The six new reconstruction features remain
`PENDING_AUTHORIZED_EVIDENCE`. Their contracts are planning inputs, not
implementation or qualification evidence. Bramblehorn retains its narrower
existing qualification status. Desktop and physical PS4 gates remain pending.

Render the checked-in baseline deterministically:

```bash
python3 tools/reconstruction/render_java_mod_reconstruction_wave_1.py
```

For a conversion project, pass a JSON object matching the reconstruction input
to:

```bash
mccompiler prepare-reconstruction-wave \
  --project path/to/project \
  --parameters wave.json \
  --expected-revision 1 \
  --json
```

The operation writes:

- `analysis/reconstruction-waves/<wave-id>.json`
- `production/reconstruction-waves/<wave-id>/baseline.json`

Never put the analysis record in a behavior pack, resource pack, `.mcaddon`,
`.mcworld`, or Marketplace submission payload.
