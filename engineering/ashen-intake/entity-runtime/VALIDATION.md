# Ashen entity runtime static validation

Exact base: `d3f162db41b06ce502dd8fc6995288d2fe546fa0` / `4843a3ad877cec4ecdd238d01867218ef9687741`.

Results:

- `python3 -m unittest engineering/ashen-intake/entity-runtime/test_ashen_entity_runtime.py -v` — 10/10 PASS.
- `python3 tools/validate_wave1.py --root . --report /private/tmp/ashen-entity-wave1-validation.json` — PASS across JSON/PNG structure, identifier, texture/model, recipe/loot, script-policy, and evidence closure.
- Representative native evidence suite — 9/9 PASS when run from its owning directory.
- Remaining-creature native evidence suite — 6/6 PASS when run from its owning directory.
- Current Stable Creator documentation was checked for entity goals and spawn-rule `biome_filter`, `brightness_filter`, `density_limit`, `distance_filter`, `herd`, and `weight` shapes.
- `git diff --check` — PASS.

The dedicated suite proves exact pass-2 geometry/animation and exact source-texture byte equality, complete PNG decode with chunk CRC checks, geometry/animation bone closure, client/controller/render reference closure, non-statue behavior composition, exactly nine bounded natural spawn rules, no Ash Drake spawn rule, no loot binding, no Kiln Sky session/reward terms in the Ash Drake shell, deterministic output hashes, and deterministic regeneration.

No build, package assembly, Creator Tools, BDS, Bedrock client, gameplay-feel, multiplayer, persistence, console, PS4, Marketplace, or release test was run by this lane.
