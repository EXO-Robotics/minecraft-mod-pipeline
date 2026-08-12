# Twinbond native-only asset repair

This isolated lane is bound to G8 commit `edbdf01143e994cae8e77414951d07ae3c95ed63`
and tree `9685cd17539999419d3f8e32272261e585cde0c6`.

It proves native Blockbench 5.1.6 round-trip, true locator export, exact texture
byte preservation, timeline evidence, and two canonically equivalent native
export cycles for `ash_sovereign_wyrm`, `tide_empress_wyrm`, and
`twinbond_relic`. The relic receives exactly its brief-declared `dual_pulse`
clip. The wyrm briefs declare no animation list, so their existing generic
`idle` and `action` source clips are preserved without claiming phase-ready
animation.

No BP/RP, item, recipe, runtime, encounter, progression, authority, or BDS
surface is changed or proven by this lane.
