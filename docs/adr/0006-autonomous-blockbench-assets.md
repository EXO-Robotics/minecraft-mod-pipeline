# ADR 0006: Treat Blockbench assets as revisioned compiler artifacts

Status: accepted.

Blockbench source is not an informal sidecar. The compiler owns a versioned
asset contract, deterministic native source and Bedrock exports, semantic
coordinate checks, visual evidence, rights/provenance records, repair history,
consumer bindings, cost reports, and qualification receipts.

The compiler may autonomously author and repair an asset only within declared
budgets and a five-revision limit. It must reopen and save the source in
Blockbench, validate native exports, and fail closed if machine quality or
rights gates do not pass. Accepted assets enter the project registry by
content hash.

PS4 is a planning profile until a frozen artifact completes a physical
Realm-to-PS4 run. Automated output may say `PS4_PENDING`; it may not claim
compatibility or certification.
