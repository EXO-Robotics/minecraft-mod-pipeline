# Whisperwood entity animation repair B

This isolated Blockbench-native lane authors the exact brief-declared clips for
`bark_wraith`, `briar_elk`, `hollow_widow_spider`, `rot_wolf`, and
`thorn_stalker`.

Authority is deliberately split:

- the entity runtime implementation map supplies approved role, runtime class,
  and movement intent;
- each Packet 001 brief supplies the exact ordered clip names and creative role;
- each canonical static geometry export supplies the locator parents and
  transforms;
- this lane authors visual keyframes only on existing bones.

The tool delegates native save/reopen/export mechanics to the proven repair-A
implementation, while replacing its asset partition and motion specs. It
removes the two generic preview clips, creates only brief-approved clips,
repairs true native locators, and performs two native Blockbench 5.1.6
save-close-reopen/export passes.

Run each asset against an isolated loopback Blockbench instance with
`--capture-timeline`. Evidence is written under
`engineering/native-assets/whisperwood/evidence/<asset>/`.

For Thorn Stalker, clip duration and poses are visual presentation values only.
They do not define hit timing, damage, phases, reset policy, multiplayer
ownership, persistence, terminal rewards, or any other boss gameplay rule.

Receipts prove only native editable integrity, native codec export,
two-pass structural equivalence, locator preservation, and authored keyframe
coverage. They do not prove Bedrock client playback, BDS behavior, controller
behavior, physical-console performance, or Marketplace acceptance.
