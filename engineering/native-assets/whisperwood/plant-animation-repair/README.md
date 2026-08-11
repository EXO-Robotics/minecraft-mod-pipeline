# Whisperwood plant animation repair

This narrow native tool repairs only the four Packet 001 plants withheld by the
plant-class gate:

| Asset | Exact approved clip | Motion envelope |
| --- | --- | --- |
| `lantern_bloom` | `glow_idle` | Slow glow-core scale breathing, maximum 0.065 scale delta |
| `pale_reed` | `sway` | Slow stream-edge clump bend, maximum 2.6 degrees |
| `star_grass` | `wind_sway` | Light asymmetric clump sway, maximum 3.2 degrees |
| `whisper_fern` | `gentle_sway` | Opposed frond drift, maximum 2.0 degrees |

The caller supplies copied `.bbmodel`, PNG, brief, and canonical geometry
inputs. The tool removes the packet's generic `idle`/`action` preview clips,
authors exactly one brief-approved loop with native Blockbench animation APIs,
repairs the canonical `effect` locator, and then requires:

- native save, close, reopen, and export twice;
- exact two-pass geometry and animation codec equivalence;
- unchanged group/cube geometry throughout authoring;
- unchanged texture bytes;
- exact clip, animated-bone, channel, duration, seam, and motion limits;
- zero Blockbench warnings and errors.

Optional screenshots capture the native Animate timeline at three representative
times. They are excluded from deterministic export equality.

This evidence proves only native Blockbench editable and codec behavior. It does
not prove Bedrock rendering or playback, BDS behavior, world generation,
harvesting, console performance, or shipping readiness.
