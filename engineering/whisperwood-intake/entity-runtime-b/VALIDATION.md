# Runtime B Validation

Result: **STATIC_INTEGRATION_PASS_RUNTIME_UNPROVEN**

Validated at source base `0667d65`:

- 5/5 BP entity identifiers close to matching spawn rules and client entities.
- 5/5 native Blockbench receipts report `PASS` within native authoring/export scope.
- 5/5 shipped geometries equal their pass-1 native exports after the authorized identifier-only `aionforge_ww` to `aionbound` transformation.
- 5/5 shipped animation sets equal their pass-1 native exports after the same identifier-only transformation.
- 5/5 shipped PNGs are byte-identical to the native evidence inputs.
- Every client geometry, texture, animation, animation-controller, and render-controller reference closes.
- Every animation-controller state and transition closes locally.
- Animation controllers use only a reviewed stable MoLang query set; the unsupported `query.is_attacking` guess was rejected during review.
- Each entity has movement, navigation, idle locomotion, reaction/target policy, and melee behavior appropriate to its approved role.
- Spawn groups are at most three and weights are at most three; Thorn Stalker weight is one.
- No runtime-B entity has a loot component or an entity loot table.
- Thorn Stalker is machine-classified `BASE_HOSTILE_SHELL_ONLY`, has no boss-state components, and explicitly withholds boss completion.

Commands:

```sh
python3 engineering/whisperwood-intake/entity-runtime-b/test_entity_runtime_b.py
python3 tools/validate_wave1.py --root .
```

Results: 6 runtime-B tests PASS; successor source validator PASS.

These checks do not prove schema acceptance by Stable BDS, client rendering,
observed AI/motion, spawn distribution, persistence, multiplayer, console, or
boss completion. Checkpoint 1 remains the first authorized BDS moment.
