# Whisperwood direct prop native repair

This bounded lane repairs the Packet 001 `lantern_post` and `moss_cairn`
editable projects through an isolated Blockbench 5.1.6 renderer.

- Both assets receive a true native `effect` locator using the exact parent and
  transform from their canonical packet geometry export.
- Source geometry and texture bytes are preserved; only staged texture paths
  and the Blockbench project identifier are normalized.
- Generic packet preview clips are removed. `lantern_post` receives exactly the
  brief-approved `idle_sway` and `glow` loops. `moss_cairn` receives no clips.
- Each project is saved, closed, reopened, and exported twice through native
  Blockbench geometry and animation codecs.

The receipts prove editable survival and native codec equivalence only. Native
animation authoring does **not** prove that a custom block binds or plays those
clips in Minecraft. Client binding/playback, BDS, console, and Marketplace gates
remain untested.
