# Metric Definitions

- `MEASURED`: directly emitted by the BDS diagnostic.
- `DERIVED`: calculated from measured counts or bounded configuration.
- `ESTIMATED`: planning-only projection.
- `UNAVAILABLE`: BDS did not expose the metric; no value was invented.

Entity/projectile peaks and cleanup counts are measured. Caps and reserve are derived. PS4 weights are estimated and explicitly uncalibrated. Tick backlog, client frame pacing, client memory, and controller behavior are unavailable.
