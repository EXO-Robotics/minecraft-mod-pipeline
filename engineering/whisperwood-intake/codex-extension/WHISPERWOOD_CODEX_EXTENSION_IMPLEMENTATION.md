# Whisperwood Codex extension implementation

Status: **STATIC_IMPLEMENTATION_PASS_WITH_EXPLICIT_WITHHOLDS**. Base: `34fab77a5212232120b437ab24b55e2eab4ffb98`.

The append-only registry now contains the original 40 Whisperwood pages plus 34 mapped pages: 10 structures, 21 Packet 006 equipment/trophies, Thorn Court, the Whisperwood chapter, and the Ashen rumor. Registry version is 2; persistent state remains schema v4. The exact mapped caps encode a fully populated four-region discovery object in 596 JSON bytes.

All ten structure pages complete from their existing authored interaction anchors. Recognition uses exact relative palette signatures and accepts all four random structure rotations. Activation does not imply or claim loot. The 200-tick proximity alternative remains registered but is not routed because the current pack has no canonical bounded site locator.

Thorn Court encounter credit is emitted only after a valid arena pull. Terminal transitions are composed after durable player completion, seal credit, and reward entitlement exist and before recoverable physical trophy delivery. Ordinary ecology-form Thorn Stalker deaths remain limited to the creature page. Physical skull possession is not inspected. The three mastery trophies remain optional and do not participate in progression.

The broken wagon records the exact Codex/structure-state Ashen hint, “Heat waits east of the burned wagons.” It creates no map-scrap or unlock item.

Twenty equipment pages require the map's exact `successful_craft_output` signal. The current Stable API runtime has no exact craft-completion subscriber, so those triggers are deliberately withheld rather than replaced with first possession. The Thorn Stalker Skull page is separately wired to durable Thorn Court terminal credit.

Checks: Node source semantics 67/67 pass; deterministic generated-data test 1/1 pass; `tools/validate_wave1.py` pass. The Python suite passes 71/72; its single failure executes the pre-existing stale default working-package artifact and observes no startup registration there. This lane was explicitly no-build/no-package, so that artifact was neither rebuilt nor treated as current evidence.

This proves source and semantic integration only. It does not prove an immutable archive, extracted shipped entrypoint, Stable BDS, client UI, or Checkpoint 1.
