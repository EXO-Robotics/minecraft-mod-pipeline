# Console performance budgets

The production target is designed for lower-end supported console hardware, including PS4 and base Xbox One-class devices. Budgets must be measured and versioned rather than inferred from pack import success.

Measure script time per tick, scheduled queue latency, entity density and AI/pathfinding, particles, animation controllers, geometry, texture memory/handles, file count, pack size, save growth, dynamic properties, scoreboards, structures, chunk activity, split-screen overhead, and multiplayer scaling.

Generated runtime design should be event-driven and use active-object registries, staggered updates, bounded queues, spatial filtering, cached queries, cleanup, per-tick budgets, and explicitly approved degradation. Global unbounded scans are prohibited.

Each report records artifact hash, platform/runtime, scenario, population, warm-up, sample duration, metric values, limits, breaches, approval, and raw evidence. Static estimates are planning aids, not measured passes. No device-specific budget is marked passed until that device/scenario is run.

