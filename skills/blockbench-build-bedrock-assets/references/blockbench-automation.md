# Blockbench automation

Official references:

- Plugin development guide: https://www.blockbench.net/wiki/docs/plugin/
- Blockbench API reference: https://web.blockbench.net/docs/

## Preferred approach

Use Blockbench's public plugin API for repeatable creation or transformation. A plugin can create a project in the intended format, construct cubes/groups/bones, assign texture and UV data, select elements, and invoke supported codecs/export actions.

Use direct `.bbmodel` generation only for controlled prototypes. The format is Blockbench's editable project state and may change; always reopen generated projects and export the runtime `.geo.json` through the correct native codec.

## UI fallback

When automation is unavailable:

1. Inspect the current Blockbench window.
2. Use File > Open Model for `.bbmodel`.
3. Confirm project format, cube/bone/locator counts, texture size, and visible texture.
4. Use File > Save Project. In Animate mode, do not assume a generic save shortcut saves the project rather than the current animation.
5. Use File > Export > Export Bedrock Geometry and the native animation exporter.
6. Reopen the native exports for visual and structural verification.

Do not assume a successful file write means Blockbench accepted the project.

## Native locator rule

A locator is an element, not a group label or an empty bone. Create it with Blockbench's locator facility and parent it in the outliner. After native export, inspect `minecraft:geometry[].bones[].locators` and require every expected locator by name. If the source hierarchy shows a locator but the exported JSON does not, the round-trip failed.

## Native identity and link integrity

Use RFC 4122-shaped UUIDs for groups, elements, animations, animators, and
keyframes. Validate that outliner references resolve to elements, animator keys
resolve to bones, and keyframe links resolve to the intended animation. Embed
or bind the declared texture and require cube faces to reference the correct
texture index.

The native receipt must cover reopen, save, reopen, and export. Capture the
exact final model with zero warnings and a timeline view that exposes every
required clip and real keyframes. Hash those captures. Keep UI screenshots out
of deterministic export equality because editor/OS pixels are not stable, and
record the exclusion reason rather than pretending they are deterministic.

## Evidence capture

Capture at minimum:

- Front, rear, left, right, top, and three-quarter textured views.
- A wireframe view that exposes the rig and pivots.
- An Animate-tab view with the timeline and keyframes visible.
- The texture atlas.

The axis widget is useful for repeatable orthographic views; use **View > View Mode > Wireframe** for rig evidence. Re-query the UI after every state-changing action because element references can move.

Computer-use screenshots may contain JPEG bytes even when the destination name ends in `.png`. Inspect the actual file signature and convert deliberately before accepting or hashing evidence. Hash the final evidence files and record the view inventory. Do not mark the automated quality pass complete if any required view is missing.

On macOS, use the current save-panel fields and Return to confirm paths. A translocated application path may be the only reliable Blockbench app identifier for UI automation.
