# Whisperwood Log Native Evidence

`whisperwood_log` is the first representative Packet 001 asset to pass the
native Blockbench repair gate.

- Blockbench: 5.1.6, isolated profile, loopback CDP only
- Source authority: copied Packet 001 editable, texture, brief, and canonical
  static geometry export; their hashes are bound in the receipt
- Repair: created the brief-required native `effect` locator under the
  canonical export's `chassis` parent at `[0, 17, 0]`
- Result: two native save/close/reopen/export passes were canonically
  equivalent, locator transforms were preserved, and Blockbench emitted no
  warnings

The first sandboxed attempt was denied loopback access. The next attempt proved
that Blockbench 5.1.6 does not expose Node `require` in the renderer; the tool
was repaired to use `Blockbench.read` and `Blockbench.writeFile`. A later
optional screenshot request found that the named front-view preset is not
available in this version. Those attempts are diagnostic history, not PASS
evidence. The committed receipt is the subsequent codec-only PASS.

This evidence proves native editable round-trip and native codec export only.
It does not prove Bedrock client rendering, Stable BDS loading, console
behavior, or shipping readiness. The repaired project retains the packet
namespace and is not yet a normalized shipping asset.
