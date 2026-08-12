# Twinbond native-only asset repair

This isolated repair is bound to G8 commit
`50b683dfc3e390b19fc7900b88523c90bcc6a31d` and tree
`6dd2cd6547bfcb061083baa2a87e168f86b5d479`.

It proves native Blockbench 5.1.6 round-trip, true locator export, exact texture
byte preservation, timeline evidence, and two canonically equivalent native
export cycles. The existing generic `idle` and `action` clips cannot expose
four independently readable encounter phases, and the prior RP bound only
`idle`. The repair therefore retains both source clips and adds exactly four
presentation-only clips to each wyrm: `split_approach`, `concord_pressure`,
`relic_trial`, and `finale_ignition`.

The four clips are selected by a client-synchronized enum set alongside the
existing authoritative phase tags. That property is not read by encounter
logic and changes no health, damage, effect, radius, knockback, action timing,
persistence, reward, or attack identity. The relic evidence remains unchanged.

This lane proves native authoring and static BP/RP presentation binding only.
It does not prove Bedrock client playback, gameplay, BDS, multiplayer, console,
Marketplace, candidate, or release readiness.
