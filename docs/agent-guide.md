# Agent guide

1. Open the conversion project and inspect its revision/status.
2. Scan changed inputs and retrieve focused evidence; do not infer semantics from names alone.
3. Propose intent with evidence IDs and uncertainty.
4. Obtain authorized acceptance before treating proposed intent as authoritative.
5. Compare target-compatible strategies and record preserved/lost behavior.
6. Prefer a high-quality Bedrock-native design; use stable scripts when justified by the target.
7. Place manual implementations only in protected custom paths.
8. Regenerate derived content and run each applicable validation layer.
9. Repair failures; never downgrade a required check silently.
10. Record unresolved behavior, rights, performance, platform status, and the next task.

Never assign human-only rights clearance, claim Marketplace approval, treat metadata as loader semantics, treat BDS as console proof, or mark hardware verified without artifact-bound evidence. New source sessions must resume from durable project state rather than reconstructing decisions from chat.

The structured operation API is described in [ai-tool-interface.md](ai-tool-interface.md). All required operation names are registered: artifact-backed operations are tested, while operations that need runtime, hardware, or external authority return structured `NOT_AVAILABLE` blockers. Baseline commands are documented in [reproduction.md](reproduction.md).
