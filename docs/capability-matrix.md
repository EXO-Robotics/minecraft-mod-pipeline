# Capability Matrix

The executable matrix lives in `src/mccompiler/capabilities.json`. This table is
the human-readable summary of the first target profile.

| Capability | Native Bedrock surface | Baseline strategy | Expected fidelity |
|---|---|---|---:|
| Pack identity/dependencies | `manifest.json` | Direct | 100% |
| Items | item definitions/components | Direct | 90% |
| Blocks | block definitions/components | Direct | 80–85% |
| Recipes/loot | behavior-pack JSON | Direct | 90–95% |
| Entities | behavior + resource entity JSON | Reconstructed | 65–75% |
| Models/textures/sounds | resource-pack assets | Reconstructed/direct | 60–85% |
| Structures | `.mcstructure` and feature placement | Reconstructed | 65–80% |
| World generation | biomes/features/feature rules | Approximated | 40–60% |
| Item use/entity hit/tick | Script API events/scheduling | Scripted | 65–85% |
| Persistent state | dynamic properties/scoreboards/script state | Scripted | 65–75% |
| Machines/block entities | custom block + script state/UI | Scripted/manual | 50–70% |
| Custom GUI | forms/containers/in-world controls | Approximated | 30–60% |
| Custom packets | redesigned local event flow | Approximated | 25–55% |
| Mixins/engine patches | no direct equivalent | Manual/unsupported | 15–40% |
| Custom dimensions | dimension API or approximation | Approximated | 30–50% |

The scores are planning priors, not benchmark results. The compiler must replace
them with test-backed scores as GameTests and runtime probes are added.

